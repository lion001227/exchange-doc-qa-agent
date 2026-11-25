from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import DateTime, Integer, String, Index, ForeignKey, Enum, Text, JSON, Float, func, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    created_at:Mapped[datetime]=mapped_column(DateTime,default=func.now(),comment="创建时间")

class User(Base):
    __tablename__="users"

    id:Mapped[int]=mapped_column(BigInteger,primary_key=True,nullable=False,autoincrement=True,comment="用户ID")
    username:Mapped[str]=mapped_column(String(50),nullable=False,comment="用户名")
    email:Mapped[str]=mapped_column(String(100),unique=True,nullable=False,comment="邮箱")
    password:Mapped[str]=mapped_column(String(255),nullable=False,comment="密码")
    updated_at:Mapped[datetime]=mapped_column(DateTime,default=func.now(),onupdate=func.now(),comment="更新时间")

    def __repr__(self):
        return f"<User (id={self.id},name={self.username},email={self.email})>"

class Conversation(Base):
    __tablename__="conversations"

    __table_args__=(Index('idx_created','created_at'),
                    Index('uk_thread','thread_id',unique=True),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment="会话ID")
    user_id:Mapped[int]=mapped_column(BigInteger,ForeignKey("users.id",ondelete="CASCADE",onupdate="CASCADE"),nullable=False,comment="用户ID")
    thread_id: Mapped[str] = mapped_column(String(100), nullable=False, comment="LangGraph会话ID")
    title: Mapped[Optional[str]] = mapped_column(String(200), comment="会话标题")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(),comment="最后更新时间")

    def __repr__(self):
        return f"<Conversation (id={self.id},user_id={self.user_id},thread_id={self.thread_id}),title={self.title}>"

class Message(Base):
    __tablename__="messages"

    __table_args__=(Index('idx_created_at','created_at'),
                    Index('idx_conv_created','conversation_id','created_at'),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment="消息ID")
    conversation_id:Mapped[int]=mapped_column(BigInteger,ForeignKey("conversations.id",ondelete="CASCADE",onupdate="CASCADE"),nullable=False,comment="会话所属ID")
    user_id:Mapped[int]=mapped_column(BigInteger,ForeignKey("users.id",ondelete="CASCADE",onupdate="CASCADE"),nullable=False,comment="用户ID")
    role:Mapped[str]=mapped_column(Enum('user','assistant','system','tool',name='role_enum',native_enum=False,length=20),nullable=False,comment="角色")
    content:Mapped[Optional[str]]=mapped_column(Text,comment="消息内容")
    meta_data:Mapped[Optional[Dict[str,Any]]]=mapped_column("metadata",JSON,comment="来源，工具调用等附加信息")
    input_token_usage:Mapped[Optional[int]]=mapped_column(Integer,comment="输入token消耗量")
    output_token_usage:Mapped[Optional[int]]=mapped_column(Integer,comment="输出token消耗量")
    total_token_usage:Mapped[Optional[int]]=mapped_column(Integer,comment="总token消耗量")
    latency:Mapped[Optional[float]]=mapped_column(Float,comment="响应耗时")
    tool_call:Mapped[Optional[str]]=mapped_column(String(50),comment="工具调用")
    relevant_document:Mapped[Optional[str]]=mapped_column(Text,comment="相关文档")

    def __repr__(self):
        return f"<Messages (id={self.id},conversation_id={self.conversation_id},role={self.role},content={self.content},meta_date={self.meta_data},total_token_usage={self.total_token_usage},latency={self.latency})>"