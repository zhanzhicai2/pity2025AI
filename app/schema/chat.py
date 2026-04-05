"""
AI 对话 Schema
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class ChatSessionForm(BaseModel):
    """对话会话表单"""
    id: Optional[int] = None
    session_id: Optional[str] = None
    title: Optional[str] = None
    model: Optional[str] = None


class ChatMessageForm(BaseModel):
    """对话消息表单"""
    id: Optional[int] = None
    session_id: int
    role: str = Field(..., description="角色（user/assistant/system）")
    content: str
    message_type: str = "text"
    tokens_used: Optional[int] = None


class SendMessageForm(BaseModel):
    """发送消息表单"""
    content: str = Field(..., description="消息内容")
    model: Optional[str] = Field(None, description="使用的模型")
    use_rag: bool = Field(False, description="是否启用知识库检索增强")


class ChatSessionResponse(BaseModel):
    """对话会话响应"""
    id: int
    session_id: str
    title: Optional[str] = None
    model: Optional[str] = None
    message_count: Optional[int] = 0
    created_at: int


class ChatMessageResponse(BaseModel):
    """对话消息响应"""
    id: int
    session_id: int
    role: str
    content: str
    message_type: str = "text"
    tokens_used: Optional[int] = None
    created_at: int


class ChatHistoryResponse(BaseModel):
    """对话历史响应"""
    sessions: List[ChatSessionResponse]
    total: int
