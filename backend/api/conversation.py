from typing import List

from fastapi import APIRouter,status
from fastapi import Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.crud.conversations import get_conversation, clear_conversations, get_conversation_list
from backend.core.db_config import get_db
from backend.db.models import User
from backend.schemas.conversation import Conversation
from backend.utils.get_current_user import get_current_user

router = APIRouter(prefix="/api/conversation",tags=["conversation"])

@router.get('/list',response_model=List[Conversation])
async def get_conversations_list(user:User = Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    result=await get_conversation_list(db,user.id)
    return result

@router.get('/check')
async def get_conversations(conversation_id:int,user:User = Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    result=await get_conversation(db,user.id,conversation_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="会话不存在")
    return result


@router.delete('/clear')
async def delete_conversations(conversation_id:int,user:User = Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    await clear_conversations(db,user.id,conversation_id)
    return f"删除用户{user.id}会话{conversation_id}成功"


