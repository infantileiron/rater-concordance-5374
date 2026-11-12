import uuid
from sqlalchemy import select
from fastapi import HTTPException
from src.models import AgreementStudy,RatingScale
from src.services.datasets import require
from src.services.cohort import prepare
from src.utils.time import now
from src.utils.serialization import serialize
def create(db,payload):
 dataset=require(db,payload.dataset_id);scale=db.get(RatingScale,payload.scale_id)
 if not scale:raise HTTPException(404,"标尺不存在")
 if not set(payload.rater_ids)<=set(dataset.raters):raise HTTPException(422,"所选评委不在盲评数据中")
 try:prepare(dataset.tasks,payload.rater_ids,scale.levels)
 except ValueError as e:raise HTTPException(422,str(e))
 if db.scalar(select(AgreementStudy).where(AgreementStudy.name==payload.name)):raise HTTPException(409,"评测研究名称已存在")
 item=AgreementStudy(id=str(uuid.uuid4()),created_at=now(),**payload.model_dump());db.add(item);db.commit();return serialize(item)
