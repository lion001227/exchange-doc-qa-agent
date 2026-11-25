import logging
import time
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from agent.agent import agent
from backend.core.db_config import get_db
from backend.crud.conversations import create_conversations, update_conversations_time
from backend.crud.messages import create_message
from backend.db.models import User
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.crud import users, conversations
from backend.utils.get_document import has_document
from backend.utils.jsonable import to_jsonable
from backend.utils.get_current_user import get_current_user
from evaluation.evaluate import get_called_tools
from rag.rag import retrieve_for_evaluation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/chat",tags=["chat"])

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/qa", response_model=ChatResponse)
async def chat(request: ChatRequest,
               conversation_id:int|None=None,
               user:User=Depends(get_current_user),
               db:AsyncSession=Depends(get_db)):
    #查询用户是否存在
    await users.get_user(db,user.id)

    #查询会话是否存在
    conversation=None
    if conversation_id is not None:
        conversation=await conversations.get_conversation(db,user.id,conversation_id)
    #不存在则写入会话表
    if conversation is None:
        conversation=await create_conversations(db,user.id,request.thread_id,request.question)
        conversation_id=conversation.id

    #用户提问写入messages表
    await create_message(db,user.id,conversation_id,role="user",content=request.question)
    start=time.perf_counter()
    # answer=await ask_agent(question=request.question,thread_id=request.thread_id)
    #获取回答
    result=agent.invoke({"messages":[("user",request.question)]},
                           config={"configurable":{"thread_id":request.thread_id}})

    answer=result["messages"][-1].content
    meta_data=to_jsonable(result)
    input_token_usage=result["messages"][-1].usage_metadata["input_tokens"]
    output_token_usage=result["messages"][-1].usage_metadata["output_tokens"]
    total_token_usage=result["messages"][-1].usage_metadata["total_tokens"]
    latency=time.perf_counter()-start
    tool_call=get_called_tools(result)
    #判断有没有相关文档，调用交易所工具的相关文档返回None
    result=has_document(tool_call)
    if result:
        relevant_document="\n\n==文档分隔==\n\n".join(str(doc) for doc in retrieve_for_evaluation(request.question))
    else:
        relevant_document=None

    #agent回答写入messages表
    await create_message(db,user.id,conversation_id,
                         role="assistant",
                         content=answer,
                         metadata=meta_data,
                         input_token_usage=input_token_usage,
                         output_token_usage=output_token_usage,
                         total_token_usage=total_token_usage,
                         latency=latency,
                         tool_call=",".join(str(tool) for tool in tool_call),
                         relevant_document=relevant_document)
    #更新会话时间
    await update_conversations_time(db,conversation_id)

    logger.info("问答完成，thread_id=%s，耗时=%.2fs",request.thread_id,latency)
    return ChatResponse(answer=answer,thread_id=request.thread_id,conversation_id=conversation_id)


