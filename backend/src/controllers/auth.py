from fastapi import Depends,HTTPException
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from src.utils.security import decode
bearer=HTTPBearer(auto_error=False)
def current_user(credentials:HTTPAuthorizationCredentials=Depends(bearer)):
 if not credentials: raise HTTPException(401,"请先登录")
 try: return decode(credentials.credentials)
 except Exception: raise HTTPException(401,"会话过期，请重新登录")
def writer(user=Depends(current_user)):
 if user["role"] not in ("admin","analyst"): raise HTTPException(403,"只读账号不能修改数据")
 return user
def admin(user=Depends(current_user)):
 if user["role"]!="admin": raise HTTPException(403,"仅管理员可批准归档")
 return user
