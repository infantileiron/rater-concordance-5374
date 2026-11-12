"""运行任务的队列协调：条件认领、租约、fencing写入与对账。

并发模型
--------
1. 认领（claim）是数据库条件更新（CAS）：只有 queued，或 running 但租约已过期的运行
   才能被某个 worker 认领；认领成功后 attempt 自增。重复投递或多 worker 同时拉到同一
   任务时，只有一个 worker 能拿到非空 token，其余直接跳过，因此同一次执行只发布一次结果。
2. attempt 是单调递增的 fencing 令牌。complete_run / fail_run 都必须带上认领时拿到的
   attempt；旧执行者（已被抢占、attempt 已落后）恢复后写入会命中 0 行，无法覆盖新结果。
3. 租约由后台心跳线程续租。worker 进程中断后租约停止续期，到期后其他 worker 可抢占重算，
   重启的 worker 通过对账自动续算，无需人工介入。
4. 队列（Redis）短暂不可用时不改变运行终态：创建端保留 queued，worker 端重试并周期性对账，
   队列恢复后自动继续。
"""
from datetime import datetime,timedelta,timezone

from sqlalchemy import select,update

from src.config.database import Session
from src.config import settings
from src.config.settings import JOB_QUEUE_KEY
from src.models import AgreementRun
from src.utils.time import now

_TERMINAL_STATUSES=("completed","failed")


def _expiry(seconds):
 return (datetime.now(timezone.utc)+timedelta(seconds=seconds)).isoformat()


def enqueue(queue,run_id):
 """把运行ID投递到队列；队列不可用时抛出 redis.RedisError，由调用方保留queued状态。"""
 queue.lpush(JOB_QUEUE_KEY,run_id)


def claim_run(run_id,worker_id,lease_seconds=None):
 """条件认领一个运行。

 返回 (attempt, leased_until)；运行不存在、已终态或租约仍被任何worker（含自己）
 持有时返回 None。同机恢复也必须等旧租约过期后再认领，避免执行中重复推进attempt。
 """
 if lease_seconds is None:lease_seconds=settings.WORKER_LEASE_SECONDS
 with Session() as db:
  run=db.get(AgreementRun,run_id)
  if run is None or run.status in _TERMINAL_STATUSES:return None
  if run.status=="running" and run.leased_until and run.leased_until>now():
   return None
  previous=run.attempt or 0
  leased_until=_expiry(lease_seconds)
  # 条件更新作为并发CAS：状态与过期判断在数据库侧完成，避免两worker同时读到旧租约
  result=db.execute(
   update(AgreementRun)
   .where(AgreementRun.id==run_id)
   .where(AgreementRun.status.in_(("queued","running")))
   .where((AgreementRun.leased_until=="")|(AgreementRun.leased_until<=now()))
   .values(status="running",attempt=previous+1,leased_by=worker_id,leased_until=leased_until,updated_at=now())
  )
  db.commit()
  if result.rowcount!=1:return None
  return previous+1,leased_until


def renew_lease(run_id,attempt,worker_id,lease_seconds=None):
 """续租。仅当运行仍由本worker以同一attempt持有时成功，返回是否续上。"""
 if lease_seconds is None:lease_seconds=settings.WORKER_LEASE_SECONDS
 with Session() as db:
  result=db.execute(
   update(AgreementRun)
   .where(AgreementRun.id==run_id)
   .where(AgreementRun.attempt==attempt)
   .where(AgreementRun.leased_by==worker_id)
   .where(AgreementRun.status=="running")
   .values(leased_until=_expiry(lease_seconds),updated_at=now())
  )
  db.commit()
  return result.rowcount==1


def complete_run(run_id,attempt,result):
 """fencing写入：仅当前attempt匹配时发布结果，旧执行者恢复后命中0行、无法覆盖。"""
 with Session() as db:
  rowcount=db.execute(
   update(AgreementRun)
   .where(AgreementRun.id==run_id)
   .where(AgreementRun.attempt==attempt)
   .where(AgreementRun.status=="running")
   .values(status="completed",result=result,error="",leased_by="",leased_until="",updated_at=now())
  ).rowcount
  db.commit()
  return rowcount==1


def fail_run(run_id,attempt,message):
 """计算本身失败时落失败态；同样受attempt fencing保护，被抢占后不覆盖新执行者。"""
 with Session() as db:
  rowcount=db.execute(
   update(AgreementRun)
   .where(AgreementRun.id==run_id)
   .where(AgreementRun.attempt==attempt)
   .where(AgreementRun.status=="running")
   .values(status="failed",error=message,leased_by="",leased_until="",updated_at=now())
  ).rowcount
  db.commit()
  return rowcount==1


def stale_run_ids():
 """对账查询：所有queued，以及running但租约已过期的运行（worker崩溃/中断遗留）。"""
 with Session() as db:
  return list(db.scalars(
   select(AgreementRun.id)
   .where((AgreementRun.status=="queued")|
          ((AgreementRun.status=="running")&
           ((AgreementRun.leased_until=="")|(AgreementRun.leased_until<=now()))))
  ))


def requeue_stale(queue):
 """把待处理与租约过期的运行重新投递；重复投递安全，claim保证单次执行。"""
 ids=[rid for rid in stale_run_ids()]
 for rid in ids:enqueue(queue,rid)
 return ids
