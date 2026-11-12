from fastapi import APIRouter,Depends
from sqlalchemy import select
from src.config.database import db_session
from src.controllers.auth import current_user,writer,admin
from src.models import RatingScale
from src.schemas.scale import ScaleInput
from src.services import scales as service
from src.utils.serialization import rows
router=APIRouter(prefix="/scales")
@router.get("")
def listing(db=Depends(db_session),user=Depends(current_user)):return rows(db.scalars(select(RatingScale).order_by(RatingScale.created_at.desc())))
@router.post("")
def create(payload:ScaleInput,db=Depends(db_session),user=Depends(writer)):return service.create(db,payload)
