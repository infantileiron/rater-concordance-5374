from fastapi import APIRouter,Depends
from sqlalchemy import select
from src.config.database import db_session
from src.controllers.auth import current_user,writer,admin
from src.models import Report
from src.schemas.report import ReportInput
from src.services import reports as service
from src.utils.serialization import rows
router=APIRouter(prefix="/reports")
@router.get("")
def listing(db=Depends(db_session),user=Depends(current_user)):return rows(db.scalars(select(Report).order_by(Report.created_at.desc())))
@router.post("")
def create(payload:ReportInput,db=Depends(db_session),user=Depends(admin)):return service.create(db,payload,user)

@router.get("/{id}/csv")
def download(id:str,db=Depends(db_session),user=Depends(current_user)):
 from fastapi.responses import Response
 return Response(service.export(db,id),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":"attachment; filename=rater-agreement.csv"})
