from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.db_config import get_db
from backend.crud.users import create_user, check_user
from backend.db.models import User
from backend.utils.get_current_user import get_current_user
from backend.utils.security import create_access_token

router = APIRouter(prefix="/api/auth")

@router.post("/register")
async def register(user_name:str,email:str,password:str,db:AsyncSession=Depends(get_db)):
    await create_user(db,email,password,user_name)
    return {"message":"用户注册成功"}

@router.post("/login")
async def login(email:str,password:str,db:AsyncSession=Depends(get_db)):
    user=await check_user(db,email,password)
    token=await create_access_token(user.id)
    return {"access_token":token,
            "token_type":"bearer",
            "user_id":user.id,}

@router.get("/me")
async def user_info(current_user:User = Depends(get_current_user)):
     return {
         "id": current_user.id,
         "username": current_user.username,
         "email": current_user.email
     }