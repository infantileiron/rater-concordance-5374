import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from src.config.database import Session
from src.models import AuditEvent
from src.utils.time import now
from src.utils.security import decode
class AuditMiddleware(BaseHTTPMiddleware):
 async def dispatch(self,request,call_next):
  response=await call_next(request)
  if request.method in ("POST","PATCH","DELETE"):
   actor="anonymous"
   try: actor=decode(request.headers.get("authorization","").split(" ",1)[1])["email"]
   except Exception: pass
   with Session() as db:
    db.add(AuditEvent(id=str(uuid.uuid4()),actor=actor,action=request.method+" "+request.url.path,status=response.status_code,created_at=now()));db.commit()
  return response
