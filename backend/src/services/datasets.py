import uuid
from sqlalchemy import select
from fastapi import HTTPException
from src.models import RatingDataset
from src.utils.time import now
from src.utils.serialization import serialize
def create(db,payload):
 if db.scalar(select(RatingDataset).where(RatingDataset.name==payload.name)):raise HTTPException(409,"盲评集名称已存在")
 item=RatingDataset(id=str(uuid.uuid4()),name=payload.name,source=payload.source,raters=payload.raters,tasks=[t.model_dump() for t in payload.tasks],created_at=now());db.add(item);db.commit();return serialize(item)
def require(db,id):
 item=db.get(RatingDataset,id)
 if not item:raise HTTPException(404,"盲评数据不存在")
 return item
