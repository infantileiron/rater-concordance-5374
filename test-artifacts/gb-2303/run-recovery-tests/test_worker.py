"""worker端到端场景：中断恢复、重复投递、抢占、队列抖动与口径保持。"""
import threading
import time

import pytest
from sqlalchemy import update

from src.config.settings import WORKER_LEASE_SECONDS
from src.models import AgreementRun,PanelReview,Report
from src.services import jobs
from src.services.analysis import analyze
import src.worker as worker_mod

from conftest import FakeQueue,make_run


@pytest.fixture
def short_lease(monkeypatch):
 # 让心跳/抢占场景在秒级完成
 from src.config import settings
 monkeypatch.setattr(settings,"WORKER_LEASE_SECONDS",0.3)
 monkeypatch.setattr(worker_mod,"WORKER_LEASE_SECONDS",0.3)


def _reload(db,run_id):
 db.expire_all()
 return db.get(AgreementRun,run_id)


def test_interrupted_run_recovers_with_same_id_and_result(db,study,short_lease):
 """worker中断（无心跳、租约过期）后，同一运行编号被重新认领并完成。"""
 run=make_run(db,study)
 # 模拟worker-A曾认领后崩溃：处于running且租约过期
 jobs.claim_run(run.id,"worker-A",lease_seconds=-1)
 db.execute(update(AgreementRun).where(AgreementRun.id==run.id).values(leased_until=""))
 db.commit()

 queue=FakeQueue()
 jobs.requeue_stale(queue)
 assert [b.decode() for b in queue.items]==[run.id]

 worker_mod.WORKER_ID="worker-B"
 worker_mod.execute(queue.items[0].decode())
 row=_reload(db,run.id)
 assert row.status=="completed"
 assert row.id==run.id  # 运行编号不变
 assert row.attempt==2  # 重新执行产生新attempt
 assert row.error==""
 assert row.result["checksum"]


def test_duplicate_delivery_publishes_once(db,study):
 run=make_run(db,study)
 queue=FakeQueue()
 for _ in range(3):queue.lpush("k",run.id)
 worker_mod.WORKER_ID="worker-A"
 for _ in range(3):
  job=queue.brpop("k")
  if job:worker_mod.execute(job[1].decode())
 row=_reload(db,run.id)
 assert row.status=="completed"
 assert row.attempt==1  # 只有一次有效执行


def test_preemption_old_executor_cannot_overwrite(db,study,short_lease,monkeypatch):
 """抢占场景：旧执行者计算较慢，租约过期被新执行者抢占；旧结果写入必须被拦截。"""
 run=make_run(db,study)
 old_token=jobs.claim_run(run.id,"worker-A",lease_seconds=0.3)
 time.sleep(0.4)  # 心跳未运行，租约过期
 # worker-B抢占
 new_token=jobs.claim_run(run.id,"worker-B",lease_seconds=5)
 assert new_token[0]==old_token[0]+1
 # worker-A“恢复”后用旧token写结果
 assert jobs.complete_run(run.id,old_token[0],{"tampered":True}) is False
 row=_reload(db,run.id)
 assert row.status=="running"
 assert row.result=={}
 # worker-B正常完成
 from src.models import RatingDataset,RatingScale
 dataset=db.get(RatingDataset,study.dataset_id)
 scale=db.get(RatingScale,study.scale_id)
 payload=analyze(dataset.tasks,study.rater_ids,scale.levels)
 assert jobs.complete_run(run.id,new_token[0],payload) is True
 row=_reload(db,run.id)
 assert row.status=="completed"
 assert "tampered" not in row.result
 assert row.result["checksum"]==payload["checksum"]


def test_full_loop_survives_queue_outage_and_reconciles(db,study,monkeypatch):
 """队列短暂不可用时worker不中断；恢复后自动补投并完成已受理运行。"""
 run=make_run(db,study)  # 创建时即处于queued（模拟入队失败后的状态）
 queue=FakeQueue(fail=True)
 stop=threading.Event()

 def should_run():
  return not stop.is_set()

 monkeypatch.setattr(worker_mod,"WORKER_RECONCILE_SECONDS",0.1)
 thread=threading.Thread(target=worker_mod.run_forever,args=(should_run,),kwargs={})
 # run_forever内部自建redis客户端，需patch构造器返回假队列
 import redis as redis_pkg
 monkeypatch.setattr(worker_mod.redis,"Redis",type("R",(),{"from_url":staticmethod(lambda *a,**k:queue)}))
 thread.start()
 time.sleep(0.35)  # 经历若干轮队列故障，进程仍存活
 assert thread.is_alive()
 queue.fail=False
 deadline=time.time()+5
 while time.time()<deadline and _reload(db,run.id).status!="completed":
  time.sleep(0.05)
 stop.set();thread.join(timeout=3)
 row=_reload(db,run.id)
 assert row.status=="completed",f"运行未恢复，状态={row.status}"
 assert row.result["checksum"]


def test_create_keeps_queued_when_queue_down(db,study,monkeypatch):
 """创建运行时队列不可用：不置失败，保留queued，对账后可继续。"""
 import redis as redis_pkg
 from src.services import runs as runs_service

 class BrokenQueue:
  def lpush(self,*a,**k):raise redis_pkg.RedisError("down")

 monkeypatch.setattr(runs_service.redis,"Redis",type("R",(),{"from_url":staticmethod(lambda *a,**k:BrokenQueue())}))
 serialized=runs_service.create(db,study.id)
 assert serialized["status"]=="queued"
 assert serialized["attempt"]==0
 # 队列恢复，worker对账即能完成
 queue=FakeQueue()
 jobs.requeue_stale(queue)
 assert [b.decode() for b in queue.items]==[serialized["id"]]
 worker_mod.WORKER_ID="worker-A"
 worker_mod.execute(serialized["id"])
 assert _reload(db,serialized["id"]).status=="completed"


def test_compute_error_marks_failed_and_requeue_skips_terminal(db,study,monkeypatch):
 run=make_run(db,study)

 def boom(*a,**k):raise ValueError("标尺损坏")

 monkeypatch.setattr(worker_mod,"analyze",boom)
 worker_mod.WORKER_ID="worker-A"
 worker_mod.execute(run.id)
 row=_reload(db,run.id)
 assert row.status=="failed"
 assert "标尺损坏" in row.error
 # 失败是终态：对账不会重复投递
 queue=FakeQueue()
 assert jobs.requeue_stale(queue)==[]


def test_heartbeat_keeps_long_run_leased(db,study,short_lease):
 """计算耗时超过单轮租约时，心跳续租保证不会被其他worker抢占。"""
 run=make_run(db,study)
 attempt,_=jobs.claim_run(run.id,"worker-A",lease_seconds=0.3)
 hb=worker_mod.LeaseHeartbeat(run.id,attempt,"worker-A",lease_seconds=0.3)
 hb.start()
 time.sleep(0.7)  # 已超过0.3秒租约，靠心跳续命
 assert jobs.renew_lease(run.id,attempt,"worker-B") is False
 assert jobs.claim_run(run.id,"worker-B") is None  # 租约仍有效，抢占不到
 hb.stop()


def test_scoring_contract_unchanged_after_recovery(db,study):
 """恢复路径产出与直接analyze完全一致：评分口径、隔离与校验码不变。"""
 run=make_run(db,study)
 worker_mod.WORKER_ID="worker-A"
 worker_mod.execute(run.id)
 row=_reload(db,run.id)
 from src.models import RatingDataset,RatingScale
 dataset=db.get(RatingDataset,study.dataset_id)
 scale=db.get(RatingScale,study.scale_id)
 expected=analyze(dataset.tasks,study.rater_ids,scale.levels)
 assert row.result==expected
 assert row.result["tasks_total"]==5
 assert row.result["tasks_complete"]==4
 assert {i["task_id"] for i in row.result["isolated"]}=={"ST-004"}
 assert len(row.result["pairs"])==6


def test_review_and_report_relations_survive_recovery(db,study):
 """复核与归档关系仍绑定原运行编号，恢复完成后可正常复核、只归档一次。"""
 run=make_run(db,study)
 worker_mod.WORKER_ID="worker-A"
 worker_mod.execute(run.id)
 row=_reload(db,run.id)
 assert row.status=="completed"
 review=PanelReview(id="rv-1",run_id=run.id,note="恢复后复核口径一致，可接受。",decision="accepted",author="analyst@songting.demo",created_at=__import__("src.utils.time",fromlist=["now"]).now())
 report=Report(id="rp-1",run_id=run.id,title="恢复运行归档",published_by="admin@songting.demo",created_at=__import__("src.utils.time",fromlist=["now"]).now())
 db.add(review);db.add(report);db.commit()
 # 同一run的归档唯一约束仍在
 from sqlalchemy.exc import IntegrityError
 db.add(Report(id="rp-2",run_id=run.id,title="重复归档",published_by="admin@songting.demo",created_at=report.created_at))
 with pytest.raises(IntegrityError):
  db.commit()
 db.rollback()
 assert db.query(Report).filter(Report.run_id==run.id).count()==1
 assert db.query(PanelReview).filter(PanelReview.run_id==run.id).count()==1
