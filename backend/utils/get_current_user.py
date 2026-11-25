import os
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.db_config import get_db
from backend.crud.users import get_user
from backend.utils.security import oauth2_scheme


load_dotenv()

SECURITY_KEY=os.getenv("SECURITY_KEY")
ALGORITHM="HS256"

#用户认证
async def get_current_user(token: str = Depends(oauth2_scheme),db:AsyncSession=Depends(get_db)):
    credentials_exception = HTTPException(status_code=401,detail="登录状态已失效，请重新登录",headers={"WWW-Authenticate":"Bearer"})
    try:
        payload=jwt.decode(token,SECURITY_KEY,algorithms=[ALGORITHM])
        user_id=int(payload.get("sub"))
    except(jwt.InvalidTokenError,ValueError,TypeError):
        raise credentials_exception
    user=await get_user(db,user_id)
    if not user:
        raise credentials_exception
    return user