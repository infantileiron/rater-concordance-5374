import hashlib,hmac,secrets
from datetime import datetime,timedelta,timezone
import jwt
from src.config.settings import JWT_SECRET
def hash_password(password):
 salt=secrets.token_hex(16)
 return salt+":"+hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),120000).hex()
def verify_password(password,stored):
 salt,digest=stored.split(":")
 return hmac.compare_digest(digest,hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),120000).hex())
def token(user):
 return jwt.encode({"sub":user.id,"role":user.role,"email":user.email,"exp":datetime.now(timezone.utc)+timedelta(hours=8)},JWT_SECRET,algorithm="HS256")
def decode(value): return jwt.decode(value,JWT_SECRET,algorithms=["HS256"])
