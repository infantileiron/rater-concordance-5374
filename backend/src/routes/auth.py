from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from src.schemas.auth import Login
from src.config.database import db_session
from src.models import User
from src.utils.security import verify_password,token
from src.controllers.auth import current_user
router=APIRouter(prefix="/auth")
@router.post("/login")
def login(payload:Login,db=Depends(db_session)):
 user=db.scalar(select(User).where(User.email==payload.email))
 if not user or not verify_password(payload.password,user.password): raise HTTPException(401,"账号或密码错误")
 return {"token":token(user),"user":{"email":user.email,"role":user.role}}
@router.get("/me")
def me(user=Depends(current_user)): return user
