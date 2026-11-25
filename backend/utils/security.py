import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

load_dotenv()

SECURITY_KEY=os.getenv("SECURITY_KEY")
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

#密码加密
async def get_password_hash(password:str):
    return password_hash.hash(password)

#验证密码
def verify_password(plain_password:str, hashed_password:str):
    return password_hash.verify(plain_password, hashed_password)

#生成JWT
async def create_access_token(user_id:int):
    expire=datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub":str(user_id),
        "exp": expire,
    }
    return jwt.encode(payload,SECURITY_KEY,algorithm=ALGORITHM)

