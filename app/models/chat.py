"""
AI 对话模型
"""
from sqlalchemy import Column, Integer, String, Text, BIGINT

from app.models.basic import Base


class ChatSession(Base):
    """AI 对话会话"""
    __tablename__ = "chat_session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    session_id = Column(String(255), nullable=False, unique=True, index=True, comment="会话ID")
    title = Column(String(255), nullable=True, comment="对话标题")
    model = Column(String(50), nullable=True, comment="使用的模型")
    created_at = Column(BIGINT, nullable=False, default=0, comment="创建时间戳")
    updated_at = Column(BIGINT, nullable=False, default=0, comment="更新时间戳")


class ChatMessage(Base):
    """AI 对话消息"""
    __tablename__ = "chat_message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, nullable=False, index=True, comment="会话ID")
    role = Column(String(20), nullable=False, comment="角色（user/assistant/system）")
    content = Column(Text, nullable=False, comment="消息内容")
    message_type = Column(String(50), default="text", comment="消息类型")
    tokens_used = Column(Integer, nullable=True, comment="使用的令牌数")
    created_at = Column(BIGINT, nullable=False, default=0, comment="创建时间戳")
