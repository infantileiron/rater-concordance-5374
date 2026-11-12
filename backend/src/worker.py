"""独立后台worker：从Redis队列拉取运行并执行一致性计算。

可靠性保证
----------
- 启动即对账：所有 queued 与租约过期的 running 运行重新入队，中断后无需人工重启续算。
- 运行期周期性对账：Redis短暂不可用或消息丢失时，待处理运行仍会被重新投递。
- 认领为数据库CAS并带fencing令牌，多worker并发或重复投递不重复发布结果；
  旧执行者恢复后的写入受attempt保护，不能覆盖新执行者的结果。
- 计算过程持有租约并由心跳线程续租；进程崩溃后租约到期，其他worker可抢占。
"""
import logging
import os
import socket
import threading
import time
import uuid
from pathlib import Path

import redis
from sqlalchemy.exc import SQLAlchemyError

from src.config.database import Session
from src.config.settings import (
 JOB_QUEUE_KEY,
 REDIS_URL,
 WORKER_LEASE_SECONDS,
 WORKER_RECONCILE_SECONDS,
)
from src.models import AgreementRun,AgreementStudy,RatingDataset,RatingScale
from src.services import jobs
from src.services.analysis import analyze

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s worker %(message)s")
log=logging.getLogger("worker")
heartbeat=Path("/artifacts/worker-heartbeat")
WORKER_ID=f"{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:8]}"


class LeaseHeartbeat:
 """后台续租：在租约到期前以同一attempt续租，被抢占后自动停止。"""

 def __init__(self,run_id,attempt,worker_id=WORKER_ID,lease_seconds=None):
  self.run_id=run_id
  self.attempt=attempt
  self.worker_id=worker_id
  self.lease_seconds=WORKER_LEASE_SECONDS if lease_seconds is None else lease_seconds
  self._stop=threading.Event()
  self._thread=threading.Thread(target=self._loop,name=f"lease-{run_id[:8]}",daemon=True)

 def start(self):
  self._thread.start()

 def _loop(self):
  interval=max(0.05,self.lease_seconds/3)
  while not self._stop.wait(interval):
   try:
    if not jobs.renew_lease(self.run_id,self.attempt,self.worker_id,self.lease_seconds):
     log.warning("run %s attempt %s 续租失败，执行权可能已被抢占",self.run_id,self.attempt)
     self._stop.set()
   except SQLAlchemyError:
    log.exception("run %s 续租异常，等待下一轮重试",self.run_id)

 def stop(self):
  self._stop.set()
  self._thread.join(timeout=5)


def execute(run_id,worker_id=WORKER_ID):
 token=jobs.claim_run(run_id,worker_id)
 if token is None:
  log.info("run %s 已被处理或仍被其他worker持有，跳过重复投递",run_id)
  return
 attempt,_leased_until=token
 log.info("run %s 由 %s 认领（attempt=%s）",run_id,worker_id,attempt)
 lease=LeaseHeartbeat(run_id,attempt,worker_id)
 lease.start()
 try:
  with Session() as db:
   run=db.get(AgreementRun,run_id)
   study=db.get(AgreementStudy,run.study_id)
   dataset=db.get(RatingDataset,study.dataset_id)
   scale=db.get(RatingScale,study.scale_id)
   payload=analyze(dataset.tasks,study.rater_ids,scale.levels)
  # fencing写入：被抢占时rowcount=0，新执行者的结果不会被覆盖
  if jobs.complete_run(run_id,attempt,payload):
   log.info("run %s 计算完成（attempt=%s）",run_id,attempt)
  else:
   log.warning("run %s 完成写入被fencing拦截，执行权已转交新执行者",run_id)
 except Exception as exc:
  log.exception("run %s 计算失败",run_id)
  try:
   if not jobs.fail_run(run_id,attempt,str(exc)):
    log.warning("run %s 失败写入被fencing拦截",run_id)
  except SQLAlchemyError:
   log.exception("run %s 失败态落库异常，等待租约过期后重新对账",run_id)
 finally:
  lease.stop()


def run_forever(should_run=lambda:True,worker_id=WORKER_ID):
 client=redis.Redis.from_url(REDIS_URL,socket_keepalive=True)
 log.info("worker %s 启动，开始启动对账",worker_id)
 try:
  jobs.requeue_stale(client)
 except (redis.RedisError,SQLAlchemyError):
  log.warning("启动对账时队列或数据库不可用，进入重试循环等待恢复")
 last_reconcile=0.0
 while should_run():
  try:
   heartbeat.touch()
  except OSError:
   pass
  try:
   job=client.brpop(JOB_QUEUE_KEY,timeout=1)
  except redis.RedisError:
   # 队列短暂不可用：不中断进程，退避后重试，由对账保证不丢运行
   log.warning("队列不可用，1秒后重试")
   time.sleep(1)
   job=None
  if job:
   try:
    execute(job[1].decode(),worker_id)
   except Exception:
    log.exception("run %s 执行异常，已隔离并继续处理后续任务",job[1])
  now_ts=time.monotonic()
  if now_ts-last_reconcile>=WORKER_RECONCILE_SECONDS:
   try:
    jobs.requeue_stale(client)
   except (redis.RedisError,SQLAlchemyError):
    log.warning("对账时队列或数据库不可用，下个周期重试")
   last_reconcile=now_ts


if __name__=="__main__":
 run_forever()
