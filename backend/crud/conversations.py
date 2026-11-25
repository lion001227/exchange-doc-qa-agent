from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, update, func, delete

from agent.agent import delete_agent_thread
from backend.db.models import Conversation

from backend.cache.conversations import set_cache_conversation,get_cache_conversation,delete_cache_conversations

async def get_conversation_list(db,user_id):
    result=await db.execute(select(Conversation).where(Conversation.user_id==user_id).order_by(Conversation.created_at.desc()))
    return result.scalars().all()

async def get_conversation(db,user_id,conversation_id):
    #查询指定对话，先查缓存
    result=await get_cache_conversation(user_id,conversation_id)
    if result:
        print("缓存返回数据")
        return result
    #缓存没数据查数据库
    result=await db.execute(select(Conversation).where(Conversation.id==conversation_id,Conversation.user_id==user_id))
    conversations= result.scalars().one_or_none()

    #写入缓存
    if conversations:
        conversations=jsonable_encoder(conversations)
        print(f"写入缓存：{conversations}")
        await set_cache_conversation(user_id,conversation_id,conversations)

    return conversations

async def create_conversations(db,user_id,thread_id,question:Optional[str]=None):
    #新建对话
    conversation=Conversation(thread_id=thread_id,user_id=user_id,title=question)
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    #删除缓存，缓存在查询的时候写入
    print("删除缓存conversation")
    await delete_cache_conversations(user_id,conversation.id)
    return conversation

async def update_conversations_time(db,conversation_id):
    #更新对话表时间
    result=await db.execute(update(Conversation).where(Conversation.id==conversation_id,).values(updated_at=func.now()))
    await db.commit()
    return result.rowcount>0

async def clear_conversations(db,user_id,conversation_id):
    #查找删除的数据
    conversation=await get_conversation(db,user_id,conversation_id)
    if not conversation:
        raise HTTPException(404,detail="会话不存在")

    #获取thread_id
    thread_id = conversation.get("thread_id") if isinstance(conversation,dict) else conversation.thread_id

    #删除LangGraph状态
    delete_agent_thread(thread_id)

    #删除MySQL数据库
    if isinstance(conversation,dict):
        await db.execute(delete(Conversation).where(Conversation.user_id==user_id,Conversation.id==conversation_id))

    else:
        await db.delete(conversation)
    await db.commit()

    return {"message":"删除成功"}
