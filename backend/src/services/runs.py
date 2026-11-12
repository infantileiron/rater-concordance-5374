import logging,uuid
import redis
from fastapi import HTTPException
from src.models import AgreementRun,AgreementStudy
from src.config.settings import REDIS_URL
from src.services import jobs
from src.utils.time import now
from src.utils.serialization import serialize

log=logging.getLogger("runs")


def create(db,study_id):
 if not db.get(AgreementStudy,study_id):raise HTTPException(404,"评测研究不存在")
 item=AgreementRun(id=str(uuid.uuid4()),study_id=study_id,status="queued",result={},error="",attempt=0,leased_by="",leased_until="",updated_at="",created_at=now())
 db.add(item);db.commit()
 # 队列短暂不可用时不把运行置失败：保留queued，worker周期性对账会自动补投并续算
 try:
  jobs.enqueue(redis.Redis.from_url(REDIS_URL),item.id)
 except redis.RedisError:
  log.warning("run %s 创建时队列不可用，保留排队状态等待worker对账",item.id)
 return serialize(item)


def require_completed(db,id):
 item=db.get(AgreementRun,id)
 if not item:raise HTTPException(404,"运行不存在")
 if item.status!="completed":raise HTTPException(409,"计算尚未完成")
 return item
