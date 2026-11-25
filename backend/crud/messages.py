import json
from typing import Optional, Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, update, delete

from backend.db.models import  Message

from backend.cache.messages import set_cache_messages,get_cache_messages,delete_cache_messages


async def get_message(db,user_id,conversation_id):
    #查缓存的消息
    result=await get_cache_messages(user_id,conversation_id)
    if result:
        print("返回缓存消息")
        return result

    #缓存没消息查数据库
    result=await db.execute(select(Message).where(Message.conversation_id==conversation_id,Message.user_id==user_id))
    messages= result.scalars().all()

    #存入缓存
    if messages:
        #将orm对象转换成json
        messages=jsonable_encoder(messages)
        print(f"写入缓存库：{messages}")
        await set_cache_messages(user_id,conversation_id,messages)

    return messages

async def create_message(db,user_id,conversation_id,role,content,
                         metadata:Optional[Any]=None,
                         input_token_usage:Optional[int]=None,
                         output_token_usage:Optional[int]=None,
                         total_token_usage:Optional[int]=None,
                         latency:Optional[float]=None,
                         tool_call:Optional[str]=None,
                         relevant_document:Optional[str]=None):
    message=Message(user_id=user_id,
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    meta_data=metadata,
                    input_token_usage=input_token_usage,
                    output_token_usage=output_token_usage,
                    total_token_usage=total_token_usage,
                    latency=latency,
                    tool_call=tool_call,
                    relevant_document=relevant_document
                    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    #删缓存，查询才重新写缓存
    print("删除缓存message")
    await delete_cache_messages(user_id,conversation_id)
    return message

async def update_message(db,message_id,content,metadata,input_token_usage,output_token_usage,total_token_usage,latency,tool_call,relevant_document):
    message=await db.execute(update(Message).where(Message.id==message_id).values(
                    content=content,
                    meta_data=metadata,
                    input_token_usage=input_token_usage,
                    output_token_usage=output_token_usage,
                    total_token_usage=total_token_usage,
                    latency=latency,
                    tool_call=tool_call,
                    relevant_document=relevant_document
    ))

    await db.commit()
    return message

async def delete_message(db,user_id,conversation_id,message_id):
    message=await db.execute(delete(Message).where(Message.user_id==user_id,Message.conversation_id==conversation_id,Message.id==message_id))
    await db.commit()
    return message.rowcount>0