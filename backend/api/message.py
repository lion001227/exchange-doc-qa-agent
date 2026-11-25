from typing import List

from fastapi import HTTPException, APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.db_config import get_db
from backend.crud.messages import get_message, delete_message
from backend.db.models import User
from backend.schemas import message
from backend.utils.get_current_user import get_current_user

router = APIRouter(prefix="/api/messages",tags=["messages"])

@router.get('/check',response_model=List[message.Message])
async def get_messages(conversation_id:int,user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    result=await get_message(db,user.id,conversation_id)
    if  len(result)<1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="消息不存在")
    return result

@router.delete('/clear')
async def delete_messages(conversation_id:int,message_id:int,user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    result=await delete_message(db,user.id,conversation_id,message_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="消息不存在")
    return f"用户{user.id}会话{conversation_id}删除成功"