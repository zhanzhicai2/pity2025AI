"""
AI 对话 API 路由
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
import json
import asyncio

from app.core.ai.openai_service import OpenAIService
from app.crud.chat import ChatSessionDao, ChatMessageDao
from app.routers import Permission
from app.schema.chat import SendMessageForm, ChatSessionResponse, ChatMessageResponse
from app.utils.logger import Log

logger = Log("chat_router")
router = APIRouter(prefix="/ai/chat", tags=["AI对话"])


def get_current_user(user_info=Depends(Permission())):
    """获取当前用户"""
    return user_info


@router.post("/sessions", summary="创建会话")
async def create_session(user_info: dict = Depends(get_current_user)):
    """创建新对话"""
    try:
        user_id = user_info.get("id")
        session = await ChatSessionDao.create_session(user_id)
        return {
            "code": 0,
            "data": {
                "id": session.id,
                "session_id": session.session_id,
                "title": session.title,
                "model": session.model,
                "created_at": session.created_at
            },
            "msg": "success"
        }
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        return {"code": 110, "data": None, "msg": f"创建会话失败: {str(e)}"}


@router.get("/sessions", summary="获取会话列表")
async def list_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_info: dict = Depends(get_current_user)
):
    """获取当前用户的会话列表"""
    try:
        user_id = user_info.get("id")
        sessions, total = await ChatSessionDao.list_sessions(user_id, skip, limit)

        # 获取每个会话的消息数量
        result = []
        for s in sessions:
            msg_count = await ChatMessageDao.get_message_count(s.id)
            result.append({
                "id": s.id,
                "session_id": s.session_id,
                "title": s.title,
                "model": s.model,
                "message_count": msg_count,
                "created_at": s.created_at
            })

        return {"code": 0, "data": {"list": result, "total": total}, "msg": "success"}
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        return {"code": 110, "data": None, "msg": f"获取会话列表失败: {str(e)}"}


@router.get("/sessions/{session_id}", summary="获取会话详情")
async def get_session(session_id: int, user_info: dict = Depends(get_current_user)):
    """获取会话详情"""
    try:
        user_id = user_info.get("id")
        session = await ChatSessionDao.get_session(session_id, user_id)
        if not session:
            return {"code": 110, "data": None, "msg": "会话不存在"}

        msg_count = await ChatMessageDao.get_message_count(session.id)
        return {
            "code": 0,
            "data": {
                "id": session.id,
                "session_id": session.session_id,
                "title": session.title,
                "model": session.model,
                "message_count": msg_count,
                "created_at": session.created_at
            },
            "msg": "success"
        }
    except Exception as e:
        logger.error(f"获取会话详情失败: {e}")
        return {"code": 110, "data": None, "msg": f"获取会话详情失败: {str(e)}"}


@router.delete("/sessions/{session_id}", summary="删除会话")
async def delete_session(session_id: int, user_info: dict = Depends(get_current_user)):
    """删除会话"""
    try:
        user_id = user_info.get("id")
        # 先删除消息
        await ChatMessageDao.delete_messages(session_id)
        # 再删除会话
        success = await ChatSessionDao.delete_session(session_id, user_id)
        if not success:
            return {"code": 110, "data": None, "msg": "会话不存在"}
        return {"code": 0, "data": None, "msg": "删除成功"}
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        return {"code": 110, "data": None, "msg": f"删除会话失败: {str(e)}"}


@router.get("/messages/{session_id}", summary="获取消息列表")
async def get_messages(
    session_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_info: dict = Depends(get_current_user)
):
    """获取会话的消息列表"""
    try:
        user_id = user_info.get("id")
        # 验证会话归属
        session = await ChatSessionDao.get_session(session_id, user_id)
        if not session:
            return {"code": 110, "data": None, "msg": "会话不存在"}

        messages, total = await ChatMessageDao.get_messages(session_id, skip, limit)
        result = [{
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role,
            "content": m.content,
            "message_type": m.message_type,
            "tokens_used": m.tokens_used,
            "created_at": m.created_at
        } for m in messages]

        return {"code": 0, "data": {"list": result, "total": total}, "msg": "success"}
    except Exception as e:
        logger.error(f"获取消息列表失败: {e}")
        return {"code": 110, "data": None, "msg": f"获取消息列表失败: {str(e)}"}


@router.post("/send/{session_id}", summary="发送消息")
async def send_message(
    session_id: int,
    form: SendMessageForm,
    user_info: dict = Depends(get_current_user)
):
    """发送消息并获取AI响应"""
    try:
        user_id = user_info.get("id")

        # 验证会话归属
        session = await ChatSessionDao.get_session(session_id, user_id)
        if not session:
            return {"code": 110, "data": None, "msg": "会话不存在"}

        # 保存用户消息
        user_msg = await ChatMessageDao.create_message(
            session_id=session_id,
            role="user",
            content=form.content
        )

        # 获取历史消息构建上下文（包括刚添加的用户消息）
        messages, _ = await ChatMessageDao.get_messages(session_id, 0, 100)
        history = [{"role": m.role, "content": m.content} for m in messages]

        # 调用 AI 服务
        ai_service = OpenAIService()
        response = await ai_service.chat(history, model=form.model or session.model)

        # 保存 AI 响应
        assistant_msg = await ChatMessageDao.create_message(
            session_id=session_id,
            role="assistant",
            content=response
        )

        # 更新会话时间
        await ChatSessionDao.update_session(session_id, user_id)

        return {
            "code": 0,
            "data": {
                "user_message": {
                    "id": user_msg.id,
                    "role": user_msg.role,
                    "content": user_msg.content,
                    "created_at": user_msg.created_at
                },
                "assistant_message": {
                    "id": assistant_msg.id,
                    "role": assistant_msg.role,
                    "content": assistant_msg.content,
                    "created_at": assistant_msg.created_at
                }
            },
            "msg": "success"
        }
    except ValueError as e:
        return {"code": 110, "data": None, "msg": str(e)}
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return {"code": 110, "data": None, "msg": f"发送消息失败: {str(e)}"}


@router.post("/send/stream/{session_id}", summary="发送消息（流式响应）")
async def send_message_stream(
    session_id: int,
    form: SendMessageForm,
    user_info: dict = Depends(get_current_user)
):
    """发送消息并获取AI流式响应（SSE）"""

    async def event_generator():
        try:
            user_id = user_info.get("id")

            # 验证会话归属
            session = await ChatSessionDao.get_session(session_id, user_id)
            if not session:
                yield f"data: {json.dumps({'type': 'error', 'message': '会话不存在'}, ensure_ascii=False)}\n\n"
                return

            # 保存用户消息
            user_msg = await ChatMessageDao.create_message(
                session_id=session_id,
                role="user",
                content=form.content
            )

            yield f"data: {json.dumps({'type': 'user_message', 'data': {'id': user_msg.id, 'content': user_msg.content}}, ensure_ascii=False)}\n\n"

            # 获取历史消息构建上下文
            messages, _ = await ChatMessageDao.get_messages(session_id, 0, 100)
            history = [{"role": m.role, "content": m.content} for m in messages[:-1]]

            # 调用 AI 流式服务
            ai_service = OpenAIService()
            full_content = ""
            async for chunk in ai_service.chat_stream(history, model=form.model or session.model):
                full_content += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'data': chunk}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)

            # 保存 AI 响应
            assistant_msg = await ChatMessageDao.create_message(
                session_id=session_id,
                role="assistant",
                content=full_content
            )

            # 更新会话时间
            await ChatSessionDao.update_session(session_id, user_id)

            yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_msg.id}, ensure_ascii=False)}\n\n"

        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"流式发送消息失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'发送消息失败: {str(e)}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/models", summary="获取可用模型")
async def get_models(user_info: dict = Depends(get_current_user)):
    """获取可用的 AI 模型列表"""
    try:
        from config import Config
        models = [
            {"id": "minimax", "name": "MiniMax", "enabled": bool(Config.AI_OPENAI_API_KEY)},
            {"id": "deepseek", "name": "DeepSeek", "enabled": bool(Config.AI_OPENAI_API_KEY)},
            {"id": "zhipu", "name": "智谱 GLM", "enabled": bool(Config.AI_OPENAI_API_KEY)},
        ]
        return {"code": 0, "data": models, "msg": "success"}
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        return {"code": 110, "data": None, "msg": f"获取模型列表失败: {str(e)}"}
