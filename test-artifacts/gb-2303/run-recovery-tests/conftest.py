"""恢复/幂等/抢占测试的共享夹具。

仅使用SQLite内存库与假队列，不依赖外部Postgres/Redis；被测协调逻辑全部走
真实SQLAlchemy条件更新（CAS），与生产Postgres语义一致。
"""
import os
import sys
import uuid
from pathlib import Path

# 测试用短租约与快速对账，需在导入src.config.settings之前设置
os.environ["WORKER_LEASE_SECONDS"]="2"
os.environ["WORKER_RECONCILE_SECONDS"]="0.3"
# 本地无Postgres驱动，导入期engine先用sqlite占位，夹具会重绑到内存库
os.environ.setdefault("DATABASE_URL","sqlite://")

BACKEND=Path(__file__).resolve().parents[3]/"backend"
sys.path.insert(0,str(BACKEND))

import pytest
from sqlalchemy import create_engine,event

from src.config import database as db_config
from src.config.database import Base
from src.models import AgreementStudy,RatingDataset,RatingScale
from src.utils.time import now


@pytest.fixture
def session_factory(tmp_path):
 # 文件型SQLite + 独立连接池，避免内存库StaticPool单连接在多线程下的驱动限制；
 # 被测的是SQLAlchemy条件更新语义，与生产Postgres的行锁CAS一致
 db_file=tmp_path/"test.db"
 engine=create_engine(
  f"sqlite:///{db_file}",
  connect_args={"check_same_thread":False,"timeout":30},
 )
 @event.listens_for(engine,"connect")
 def _set_sqlite_pragma(dbapi_conn,_record):
  cursor=dbapi_conn.cursor()
  cursor.execute("PRAGMA journal_mode=WAL")
  cursor.execute("PRAGMA busy_timeout=30000")
  cursor.close()
 Base.metadata.create_all(engine)
 # jobs/worker在调用时引用src.config.database.Session，重绑到测试engine即可生效
 db_config.Session.configure(bind=engine)
 yield db_config.Session
 db_config.Session.configure(bind=db_config.engine)
 engine.dispose()


@pytest.fixture
def db(session_factory):
 with session_factory() as session:
  yield session


@pytest.fixture
def study(db):
 raters=["评委甲","评委乙","评委丙","评委丁"]
 levels=[{"code":f"L{i}","label":f"等级{i}"} for i in range(1,6)]
 tasks=[]
 for idx in range(1,6):
  tasks.append({
   "task_id":f"ST-{idx:03}",
   "group":"测试任务组",
   "ratings":{r:f"L{min(5,1+(idx%5)+j)}" for j,r in enumerate(raters)},
  })
 # 一项缺评分：验证整任务隔离口径在恢复路径中保持不变
 tasks[3]["ratings"]["评委丁"]=None
 dataset=RatingDataset(id="ds-1",name="测试数据集",source="unit-test",raters=raters,tasks=tasks,created_at=now())
 scale=RatingScale(id="sc-1",name="五级标尺",levels=levels,created_at=now())
 study=AgreementStudy(id="st-1",name="测试研究",dataset_id="ds-1",scale_id="sc-1",rater_ids=raters,created_at=now())
 db.add_all([dataset,scale,study]);db.commit()
 return study


def make_run(db,study,status="queued",**kw):
 from src.models import AgreementRun
 run=AgreementRun(
  id=str(uuid.uuid4()),study_id=study.id,status=status,result={},error="",
  attempt=kw.get("attempt",0),leased_by=kw.get("leased_by",""),
  leased_until=kw.get("leased_until",""),updated_at=kw.get("updated_at",""),
  created_at=now(),
 )
 db.add(run);db.commit()
 return run


class FakeQueue:
 """模拟Redis列表队列：lpush入尾、brpop/rpop从头，支持故障注入。"""

 def __init__(self,fail=False):
  self.items=[]
  self.fail=fail
  self.down_until=0.0

 def lpush(self,_key,value):
  if self.fail:raise __import__("redis").RedisError("queue unavailable")
  self.items.append(value.encode() if isinstance(value,str) else value)

 def rpop(self):
  if self.fail:raise __import__("redis").RedisError("queue unavailable")
  return self.items.pop(0) if self.items else None

 def brpop(self,_key,timeout=1):
  if self.fail:raise __import__("redis").RedisError("queue unavailable")
  return (None,self.items.pop(0)) if self.items else None
