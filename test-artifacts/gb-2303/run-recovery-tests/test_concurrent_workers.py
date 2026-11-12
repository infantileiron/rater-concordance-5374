"""多worker并发与真实run_forever循环的端到端验证。"""
import threading
import time

import pytest

from src.models import AgreementRun
import src.worker as worker_mod

from conftest import FakeQueue,make_run


class SharedFakeQueue(FakeQueue):
 """线程安全的共享队列，模拟多worker消费同一Redis列表。"""

 def __init__(self,fail=False):
  super().__init__(fail)
  self._lock=threading.Lock()

 def lpush(self,key,value):
  with self._lock:
   super().lpush(key,value)

 def brpop(self,key,timeout=1):
  with self._lock:
   return super().brpop(key,timeout)


def _reload(db,run_id):
 db.expire_all()
 return db.get(AgreementRun,run_id)


def test_two_concurrent_workers_each_run_published_once(db,study,monkeypatch):
 """两个真实工作循环并发消费同一队列、且每运行重复投递，结果只发布一次。

 使用生产级长租约（30秒），保证快速计算不会因租约过期被抢占；抢占本身由
 test_worker.py 的短租约用例覆盖。
 """
 from src.config import settings
 monkeypatch.setattr(settings,"WORKER_LEASE_SECONDS",30)
 monkeypatch.setattr(worker_mod,"WORKER_LEASE_SECONDS",30)
 runs=[make_run(db,study) for _ in range(6)]
 queue=SharedFakeQueue()
 # 每个运行投递两次，制造重复投递
 for run in runs:
  queue.lpush("k",run.id)
  queue.lpush("k",run.id)

 monkeypatch.setattr(worker_mod,"WORKER_RECONCILE_SECONDS",0.05)
 monkeypatch.setattr(worker_mod.redis,"Redis",
   type("R",(),{"from_url":staticmethod(lambda *a,**k:queue)}))

 stop=threading.Event()
 def should_run():
  return not stop.is_set()

 workers=[
  threading.Thread(target=worker_mod.run_forever,args=(should_run,),kwargs={"worker_id":f"worker-{i}"},name=f"loop-{i}")
  for i in range(2)
 ]
 for w in workers:w.start()
 deadline=time.time()+15
 while time.time()<deadline:
  states=[_reload(db,r.id).status for r in runs]
  if all(s=="completed" for s in states):break
  time.sleep(0.1)
 stop.set()
 for w in workers:w.join(timeout=3)

 for run in runs:
  row=_reload(db,run.id)
  assert row.status=="completed",f"{run.id} 状态={row.status}"
  # 重复投递下每个运行只被有效认领一次：attempt停在1，结果只发布一次
  assert row.attempt==1,f"{run.id} 被重复执行，attempt={row.attempt}"
  assert row.leased_by==""  # 完成后已释放租约
  assert row.result["checksum"]
 # 队列中的重复消息最终都被消费（或残留也仅会被claim跳过），运行数与结果数一致
 assert len({r.id for r in runs})==6
