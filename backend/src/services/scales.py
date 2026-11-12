import uuid
from sqlalchemy import select
from fastapi import HTTPException
from src.models import RatingScale
from src.utils.time import now
from src.utils.serialization import serialize
def create(db,payload):
 if db.scalar(select(RatingScale).where(RatingScale.name==payload.name)):raise HTTPException(409,"标尺名称已存在")
 item=RatingScale(id=str(uuid.uuid4()),name=payload.name,levels=[l.model_dump() for l in payload.levels],created_at=now());db.add(item);db.commit();return serialize(item)
