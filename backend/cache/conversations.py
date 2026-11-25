from typing import Dict, Any, List

from backend.core.redis_config import get_json_cache, set_cache, delete_cache

CONVERSATION_KEY="exchange:conversations"

#获取对话缓存
async def get_cache_conversation(user_id: int,conversation_id: int):
    key=f"{CONVERSATION_KEY}:{user_id}:{conversation_id}"
    return await get_json_cache(key)

#写入对话缓存
async def set_cache_conversation(user_id: int,conversation_id: int,value:List[Dict[str,Any]]):
    key=f"{CONVERSATION_KEY}:{user_id}:{conversation_id}"
    return await set_cache(key,value)

#删除对话缓存
async def delete_cache_conversations(user_id:int,conversation_id:int):
    key=f"{CONVERSATION_KEY}:{user_id}:{conversation_id}"
    return await delete_cache(key)

