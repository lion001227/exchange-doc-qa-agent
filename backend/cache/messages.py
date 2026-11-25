from typing import Dict, Any, List

from backend.core.redis_config import get_json_cache,set_cache,delete_cache

MESSAGES_KEY="exchange:messages"

#获取消息缓存
async def get_cache_messages(user_id:int,conversation_id:int):
    key=f"{MESSAGES_KEY}:{user_id}:{conversation_id}"
    return await get_json_cache(key)

#写入消息缓存
async def set_cache_messages(user_id:int,conversation_id:int,value:List[Dict[str,Any]],expire:int=1800):
    key=f"{MESSAGES_KEY}:{user_id}:{conversation_id}"
    return await set_cache(key,value,expire)

#删除消息缓存
async def delete_cache_messages(user_id:int,conversation_id:int):
    key=f"{MESSAGES_KEY}:{user_id}:{conversation_id}"
    return await delete_cache(key)
