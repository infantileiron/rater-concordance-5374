from fastapi import APIRouter,Depends
from sqlalchemy import select
from src.config.database import db_session
from src.controllers.auth import current_user
from src.models import AuditEvent
from src.utils.serialization import rows
router=APIRouter()
@router.get("/audit")
def listing(db=Depends(db_session),user=Depends(current_user)): return rows(db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(200)))
