from fastapi import APIRouter,Depends
from sqlalchemy import select
from src.config.database import db_session
from src.controllers.auth import current_user,writer,admin
from src.models import RatingDataset
from src.schemas.dataset import DatasetInput
from src.services import datasets as service
from src.utils.serialization import rows
router=APIRouter(prefix="/datasets")
@router.get("")
def listing(db=Depends(db_session),user=Depends(current_user)):return rows(db.scalars(select(RatingDataset).order_by(RatingDataset.created_at.desc())))
@router.post("")
def create(payload:DatasetInput,db=Depends(db_session),user=Depends(writer)):return service.create(db,payload)
