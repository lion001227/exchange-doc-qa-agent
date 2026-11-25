import logging
from fastapi import HTTPException
from openai import  RateLimitError, APITimeoutError

logger = logging.getLogger(__name__)

from langchain_core.messages import HumanMessage

async def ask_agent(question:str,thread_id:str):
    from agent.agent import agent

    try:
        result=agent.invoke({"messages":[HumanMessage(content=question)]},
                            config={"configurable":{
                                "thread_id":thread_id,
                            }}
                            )
        return result["messages"][-1].content

    except RateLimitError as e:
        logger.error(f"限流：{e}")
        raise HTTPException(status_code=429,detail="请求过于频繁")

    except APITimeoutError as e:
        logger.error(f"上游超时：{e}")
        raise HTTPException(status_code=504,detail="上游超时")

    except Exception as e:
        logger.error(f"agent异常：{e}",exc_info=True)
        raise HTTPException(status_code=500,detail="内部错误")