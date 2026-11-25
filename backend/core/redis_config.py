import json
import traceback
from typing import Any
import os

import redis.asyncio as redis

REDIS_HOST=os.getenv("REDIS_HOST","localhost")
REDIS_PORT=os.getenv("REDIS_PORT",6379)
REDIS_DB=os.getenv("REDIS_DB",0)

redis_client=redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,     #是否将字节数据解码为字符串
)

#读取字符串
async def get_cache(key:str):
    try:
        return await redis_client.get(key)
    except Exception as e:
        print(f"获取缓存失败：{e}")
        return None

#读取字符串
async def get_json_cache(key:str):
    data=await redis_client.get(key)
    try:
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        print(f"获取json缓存失败：{e}")
        return None

#设置缓存
async def set_cache(key:str,value:Any,expire:int=3600):
    try:
        if isinstance(value,(list,dict)):
            #转json，中文正常保存
            value=json.dumps(value,ensure_ascii=False)
        result=await redis_client.setex(key,expire,value)
        print(f"setex返回：{result}")
        return True
    except Exception as e:
        print(f"设置缓存失败：{e}")

        #打印完整堆栈
        traceback.print_exc()
        return False

#删除缓存
async def delete_cache(key:str):
    try:
        await redis_client.delete(key)
        print(f"删除{key}成功")
        return True
    except Exception as e:
        print(f"删除缓存失败：{e}")
        # 打印完整堆栈
        traceback.print_exc()
        return False

