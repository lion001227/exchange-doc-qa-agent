from fastapi import HTTPException
from sqlalchemy import select

from backend.db.models import User
from backend.utils.security import get_password_hash, verify_password


async def get_user(db,user_id:int):
    #查询用户是否存在
    user=await  db.execute(select(User).where(User.id == user_id))
    result= user.scalars().one_or_none()
    if not result:
        raise HTTPException(status_code=404,detail="用户不存在")
    return result

async def create_user(db,email:str,password:str,user_name:str):
    #检查邮箱是否已被注册
    email_check = await db.execute(select(User).where(User.email == email))
    result = email_check.scalars().one_or_none()
    if result is not None:
        raise HTTPException(status_code=400, detail="该邮箱已被注册")

    #新增用户
    user = User(email=email, password=await get_password_hash(password), username=user_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def check_user(db,email:str,password:str):
    user = await db.execute(select(User).where(User.email == email))
    result= user.scalar_one_or_none()

    if  result is None or not verify_password(password,result.password):
        raise HTTPException(status_code=404,detail="邮箱或密码错误")
    return result