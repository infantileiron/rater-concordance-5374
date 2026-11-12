"""认领、fencing、租约与对账的单元测试（不依赖Redis）。"""
import time
from datetime import datetime,timedelta,timezone

import pytest
from sqlalchemy import select

from src.models import AgreementRun
from src.services import jobs
from src.utils.time import now

from conftest import FakeQueue,make_run


def _iso(seconds):
 return (datetime.now(timezone.utc)+timedelta(seconds=seconds)).isoformat()


def test_claim_queued_sets_running_and_attempt(db,study):
 run=make_run(db,study)
 token=jobs.claim_run(run.id,"worker-A")
 assert token is not None
 attempt,leased_until=token
 assert attempt==1
 db.expire_all()
 claimed=db.get(AgreementRun,run.id)
 assert claimed.status=="running"
 assert claimed.attempt==1
 assert claimed.leased_by=="worker-A"
 assert claimed.leased_until>now()


def test_duplicate_delivery_claimed_once(db,study):
 """重复投递同一任务：第二个worker在租约期内无法认领，结果只发布一次。"""
 run=make_run(db,study)
 first=jobs.claim_run(run.id,"worker-A")
 second=jobs.claim_run(run.id,"worker-B")
 assert first is not None
 assert second is None
 db.expire_all()
 claimed=db.get(AgreementRun,run.id)
 assert claimed.leased_by=="worker-A"
 assert claimed.attempt==1


def test_completed_run_claim_is_noop(db,study):
 run=make_run(db,study,status="completed",attempt=1,result={"done":True})
 assert jobs.claim_run(run.id,"worker-A") is None
 db.expire_all()
 assert db.get(AgreementRun,run.id).status=="completed"


def test_fencing_blocks_stale_executor_completion(db,study):
 """旧执行者恢复后以过期attempt写入，必须被拦截，不能覆盖新执行者结果。"""
 run=make_run(db,study)
 old=jobs.claim_run(run.id,"worker-A")  # attempt=1
 # worker-A中断，租约过期后worker-B抢占
 db.execute(__import__("sqlalchemy").update(AgreementRun).where(AgreementRun.id==run.id)
            .values(leased_until=_iso(-10)))
 db.commit()
 new=jobs.claim_run(run.id,"worker-B")  # attempt=2
 assert new[0]==2
 # 旧执行者尝试用attempt=1发布
 assert jobs.complete_run(run.id,old[0],{"stale":True}) is False
 db.expire_all()
 row=db.get(AgreementRun,run.id)
 assert row.status=="running"
 assert row.result=={}
 # 新执行者正常发布
 assert jobs.complete_run(run.id,new[0],{"fresh":True}) is True
 db.expire_all()
 row=db.get(AgreementRun,run.id)
 assert row.status=="completed"
 assert row.result=={"fresh":True}


def test_fencing_blocks_stale_executor_failure(db,study):
 run=make_run(db,study)
 old=jobs.claim_run(run.id,"worker-A")
 db.execute(__import__("sqlalchemy").update(AgreementRun).where(AgreementRun.id==run.id)
            .values(leased_until=_iso(-10)))
 db.commit()
 new=jobs.claim_run(run.id,"worker-B")
 # 旧执行者想把运行置失败，不能影响新执行者
 assert jobs.fail_run(run.id,old[0],"boom") is False
 db.expire_all()
 assert db.get(AgreementRun,run.id).status=="running"
 assert jobs.complete_run(run.id,new[0],{"ok":1}) is True


def test_lease_renew_and_preempt_after_expiry(db,study):
 run=make_run(db,study)
 attempt,_=jobs.claim_run(run.id,"worker-A",lease_seconds=0.4)
 assert jobs.renew_lease(run.id,attempt,"worker-A",lease_seconds=1) is True
 db.expire_all()
 first_until=db.get(AgreementRun,run.id).leased_until
 assert first_until>now()
 # 非持有者不能续租
 assert jobs.renew_lease(run.id,attempt,"worker-X",lease_seconds=10) is False
 time.sleep(1.05)
 db.expire_all()
 assert db.get(AgreementRun,run.id).leased_until<now()
 # 租约过期后可被其他worker抢占，attempt递增
 token=jobs.claim_run(run.id,"worker-B")
 assert token[0]==attempt+1
 db.expire_all()
 row=db.get(AgreementRun,run.id)
 assert row.leased_by=="worker-B"
 assert row.status=="running"


def test_requeue_stale_covers_queued_and_expired_running(db,study):
 queued=make_run(db,study,status="queued")
 running_fresh=make_run(db,study,status="running",attempt=1,leased_by="w-1",leased_until=_iso(60))
 running_dead=make_run(db,study,status="running",attempt=2,leased_by="w-2",leased_until=_iso(-5))
 completed=make_run(db,study,status="completed",attempt=1)
 queue=FakeQueue()
 ids=jobs.requeue_stale(queue)
 assert set(ids)=={queued.id,running_dead.id}
 assert {b.decode() for b in queue.items}=={queued.id,running_dead.id}
 assert running_fresh.id not in ids
 assert completed.id not in ids


def test_requeue_is_safe_under_duplicate_enqueue(db,study):
 run=make_run(db,study)
 queue=FakeQueue()
 jobs.requeue_stale(queue)
 jobs.requeue_stale(queue)  # 重复对账导致重复投递
 assert [b.decode() for b in queue.items]==[run.id,run.id]
 # 第一条消息完成执行并进入终态
 assert jobs.claim_run(run.id,"w") is not None
 assert jobs.complete_run(run.id,1,{"once":True}) is True
 # 第二条重复投递：终态运行不再被认领，结果不会二次发布
 assert jobs.claim_run(run.id,"w") is None
 db.expire_all()
 assert db.get(AgreementRun,run.id).result=={"once":True}


def test_other_worker_cannot_claim_active_lease(db,study):
 run=make_run(db,study)
 assert jobs.claim_run(run.id,"worker-A") is not None
 # 租约期内其他worker的重复投递全部跳过
 assert jobs.claim_run(run.id,"worker-B") is None
 assert jobs.claim_run(run.id,"worker-C") is None
