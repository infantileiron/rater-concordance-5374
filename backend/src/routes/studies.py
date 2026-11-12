from fastapi import APIRouter,Depends
from sqlalchemy import select
from src.config.database import db_session
from src.controllers.auth import current_user,writer,admin
from src.models import AgreementStudy
from src.schemas.study import StudyInput
from src.services import studies as service
from src.utils.serialization import rows
router=APIRouter(prefix="/studies")
@router.get("")
def listing(db=Depends(db_session),user=Depends(current_user)):return rows(db.scalars(select(AgreementStudy).order_by(AgreementStudy.created_at.desc())))
@router.post("")
def create(payload:StudyInput,db=Depends(db_session),user=Depends(writer)):return service.create(db,payload)
