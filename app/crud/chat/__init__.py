"""
Chat DAO
"""
import uuid
import time
from typing import List, Optional

from sqlalchemy import select, or_, desc

from app.crud import Mapper, ModelWrapper
from app.models import async_session
from app.models.chat import ChatSession, ChatMessage
from app.schema.chat import ChatSessionForm, ChatMessageForm


@ModelWrapper(ChatSession)
class ChatSessionDao(Mapper):

    @classmethod
    async def create_session(cls, user_id: int, title: Optional[str] = None, model: Optional[str] = None):
        """创建会话"""
        try:
            session_id = str(uuid.uuid4())
            async with async_session() as session:
                async with session.begin():
                    data = ChatSession(
                        user_id=user_id,
                        session_id=session_id,
                        title=title or "新对话",
                        model=model,
                        created_at=int(time.time() * 1000),
                        updated_at=int(time.time() * 1000)
                    )
                    session.add(data)
                    await session.flush()
                    await session.refresh(data)
                    session.expunge(data)
                    return data
        except Exception as e:
            cls.__log__.error(f"创建会话失败, error: {str(e)}")
            raise Exception(f"创建会话失败, {str(e)}")

    @classmethod
    async def get_session(cls, session_id: int, user_id: int):
        """获取会话"""
        try:
            async with async_session() as session:
                sql = select(ChatSession).where(
                    ChatSession.id == session_id,
                    ChatSession.user_id == user_id
                )
                result = await session.execute(sql)
                return result.scalars().first()
        except Exception as e:
            cls.__log__.error(f"获取会话失败, error: {str(e)}")
            raise Exception(f"获取会话失败, {str(e)}")

    @classmethod
    async def get_session_by_sid(cls, session_id: str, user_id: int):
        """通过 session_id 获取会话"""
        try:
            async with async_session() as session:
                sql = select(ChatSession).where(
                    ChatSession.session_id == session_id,
                    ChatSession.user_id == user_id
                )
                result = await session.execute(sql)
                return result.scalars().first()
        except Exception as e:
            cls.__log__.error(f"获取会话失败, error: {str(e)}")
            raise Exception(f"获取会话失败, {str(e)}")

    @classmethod
    async def list_sessions(cls, user_id: int, skip: int = 0, limit: int = 20):
        """获取会话列表"""
        try:
            async with async_session() as session:
                conditions = [ChatSession.user_id == user_id]
                sql = select(ChatSession).where(*conditions).order_by(
                    desc(ChatSession.updated_at)
                ).offset(skip).limit(limit)
                result = await session.execute(sql)
                sessions = result.scalars().all()

                # 统计总数
                count_sql = select(ChatSession).where(*conditions)
                count_result = await session.execute(count_sql)
                total = len(count_result.scalars().all())

                return sessions, total
        except Exception as e:
            cls.__log__.error(f"获取会话列表失败, error: {str(e)}")
            raise Exception(f"获取会话列表失败, {str(e)}")

    @classmethod
    async def update_session(cls, session_id: int, user_id: int, title: Optional[str] = None):
        """更新会话"""
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(ChatSession).where(
                        ChatSession.id == session_id,
                        ChatSession.user_id == user_id
                    )
                    result = await session.execute(sql)
                    data = result.scalars().first()
                    if not data:
                        raise Exception("会话不存在")
                    if title:
                        data.title = title
                    data.updated_at = int(time.time() * 1000)
                    await session.flush()
                    session.expunge(data)
                    return data
        except Exception as e:
            cls.__log__.error(f"更新会话失败, error: {str(e)}")
            raise Exception(f"更新会话失败, {str(e)}")

    @classmethod
    async def delete_session(cls, session_id: int, user_id: int):
        """删除会话"""
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(ChatSession).where(
                        ChatSession.id == session_id,
                        ChatSession.user_id == user_id
                    )
                    result = await session.execute(sql)
                    data = result.scalars().first()
                    if not data:
                        return False
                    await session.delete(data)
                    return True
        except Exception as e:
            cls.__log__.error(f"删除会话失败, error: {str(e)}")
            raise Exception(f"删除会话失败, {str(e)}")


@ModelWrapper(ChatMessage)
class ChatMessageDao(Mapper):

    @classmethod
    async def create_message(cls, session_id: int, role: str, content: str,
                           message_type: str = "text", tokens_used: Optional[int] = None):
        """创建消息"""
        try:
            async with async_session() as session:
                async with session.begin():
                    data = ChatMessage(
                        session_id=session_id,
                        role=role,
                        content=content,
                        message_type=message_type,
                        tokens_used=tokens_used,
                        created_at=int(time.time() * 1000)
                    )
                    session.add(data)
                    await session.flush()
                    await session.refresh(data)
                    session.expunge(data)
                    return data
        except Exception as e:
            cls.__log__.error(f"创建消息失败, error: {str(e)}")
            raise Exception(f"创建消息失败, {str(e)}")

    @classmethod
    async def get_messages(cls, session_id: int, skip: int = 0, limit: int = 100):
        """获取消息列表"""
        try:
            async with async_session() as session:
                sql = select(ChatMessage).where(
                    ChatMessage.session_id == session_id
                ).order_by(ChatMessage.created_at).offset(skip).limit(limit)
                result = await session.execute(sql)
                messages = result.scalars().all()

                # 统计总数
                count_sql = select(ChatMessage).where(ChatMessage.session_id == session_id)
                count_result = await session.execute(count_sql)
                total = len(count_result.scalars().all())

                return messages, total
        except Exception as e:
            cls.__log__.error(f"获取消息列表失败, error: {str(e)}")
            raise Exception(f"获取消息列表失败, {str(e)}")

    @classmethod
    async def get_message_count(cls, session_id: int):
        """获取消息数量"""
        try:
            async with async_session() as session:
                sql = select(ChatMessage).where(ChatMessage.session_id == session_id)
                result = await session.execute(sql)
                return len(result.scalars().all())
        except Exception as e:
            cls.__log__.error(f"获取消息数量失败, error: {str(e)}")
            raise Exception(f"获取消息数量失败, {str(e)}")

    @classmethod
    async def delete_messages(cls, session_id: int):
        """删除会话的所有消息"""
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(ChatMessage).where(ChatMessage.session_id == session_id)
                    result = await session.execute(sql)
                    messages = result.scalars().all()
                    for msg in messages:
                        await session.delete(msg)
                    return True
        except Exception as e:
            cls.__log__.error(f"删除消息失败, error: {str(e)}")
            raise Exception(f"删除消息失败, {str(e)}")
