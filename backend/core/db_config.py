from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os

#数据库连接配置
DB_HOST=os.getenv("DB_HOST","localhost")
DB_PORT=os.getenv("DB_PORT","3306")
DB_USER=os.getenv("DB_USER","root")
DB_PASSWORD=os.getenv("DB_PASSWORD","123456")
DB_NAME=os.getenv("DB_NAME","exchange_qa_agent_db")

#charset=utf8mb4，支持完整的 UTF-8 字符集，包括 Emoji
ASYNC_DB_URL=f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

#创建异步引擎
async_engine = create_async_engine(
    ASYNC_DB_URL,
    echo=True,#打印sql日志
    pool_size=10,#连接池中保持的持久连接数
    max_overflow=20,#连接池允许创建的额外连接数
)

#创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,   #指定引擎
    class_=AsyncSession, #指定会话类
    expire_on_commit=False,#会话对象不过期，不重新查询数据库
)

#依赖项，获取数据库对话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
