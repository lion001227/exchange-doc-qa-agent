import logging
import time
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from backend.api import chat, conversation, message, auth
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.chat_service import ask_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(
    title="Exchange-QA-Agent",
    version="1.0.0",
)

@app.exception_handler(Exception)
async def exception_handler(request: ChatRequest,exc: Exception):
    logger.exception("问答失败，系统发生未捕捉的异常")
    return JSONResponse(status_code=500,content={"detail":"服务器内部错误"})

app.include_router(chat.router)
app.include_router(conversation.router)
app.include_router(message.router)
app.include_router(auth.router)

