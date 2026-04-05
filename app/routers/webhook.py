"""
Webhook API 路由
"""
import json
from fastapi import APIRouter, Depends, Query

from app.core.webhook_sender import WebhookSender
from app.crud.webhook import WebhookConfigDao, NotificationHistoryDao, TaskNotificationSettingDao
from app.routers import Permission
from app.schema.webhook import WebhookConfigForm, WebhookTestForm, TaskNotificationSettingForm
from app.utils.logger import Log

logger = Log("webhook_router")
router = APIRouter(prefix="/webhook", tags=["通知管理"])


def get_current_user(user_info=Depends(Permission())):
    """获取当前用户"""
    return user_info


# ==================== Webhook 配置 ====================

@router.get("/configs", summary="获取 Webhook 配置列表")
async def list_configs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_info: dict = Depends(get_current_user)
):
    """获取当前用户的 Webhook 配置列表"""
    try:
        user_id = user_info.get("id")
        configs, total = await WebhookConfigDao.list_configs(user_id, skip, limit)
        result = [{
            "id": c.id,
            "name": c.name,
            "url": c.url,
            "method": c.method,
            "headers": c.headers,
            "secret": c.secret,
            "event_type": c.event_type,
            "content_type": c.content_type,
            "template": c.template,
            "enabled": c.enabled,
            "is_default": c.is_default,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        } for c in configs]
        return {"code": 0, "data": {"list": result, "total": total}, "msg": "success"}
    except Exception as e:
        logger.error(f"获取 Webhook 配置列表失败: {e}")
        return {"code": 110, "data": None, "msg": f"获取配置列表失败: {str(e)}"}


@router.post("/configs", summary="创建 Webhook 配置")
async def create_config(
    form: WebhookConfigForm,
    user_info: dict = Depends(get_current_user)
):
    """创建新的 Webhook 配置"""
    try:
        user_id = user_info.get("id")
        config = await WebhookConfigDao.create(user_id, form)
        return {
            "code": 0,
            "data": {
                "id": config.id,
                "name": config.name,
                "url": config.url,
                "method": config.method,
                "headers": config.headers,
                "secret": config.secret,
                "event_type": config.event_type,
                "content_type": config.content_type,
                "template": config.template,
                "enabled": config.enabled,
                "is_default": config.is_default,
                "created_at": config.created_at
            },
            "msg": "创建成功"
        }
    except Exception as e:
        logger.error(f"创建 Webhook 配置失败: {e}")
        return {"code": 110, "data": None, "msg": f"创建配置失败: {str(e)}"}


@router.put("/configs/{webhook_id}", summary="更新 Webhook 配置")
async def update_config(
    webhook_id: int,
    form: WebhookConfigForm,
    user_info: dict = Depends(get_current_user)
):
    """更新 Webhook 配置"""
    try:
        user_id = user_info.get("id")
        config = await WebhookConfigDao.update(webhook_id, user_id, form)
        return {
            "code": 0,
            "data": {
                "id": config.id,
                "name": config.name,
                "url": config.url,
                "method": config.method,
                "headers": config.headers,
                "secret": config.secret,
                "event_type": config.event_type,
                "content_type": config.content_type,
                "template": config.template,
                "enabled": config.enabled,
                "is_default": config.is_default,
                "updated_at": config.updated_at
            },
            "msg": "更新成功"
        }
    except Exception as e:
        logger.error(f"更新 Webhook 配置失败: {e}")
        return {"code": 110, "data": None, "msg": f"更新配置失败: {str(e)}"}


@router.delete("/configs/{webhook_id}", summary="删除 Webhook 配置")
async def delete_config(
    webhook_id: int,
    user_info: dict = Depends(get_current_user)
):
    """删除 Webhook 配置"""
    try:
        user_id = user_info.get("id")
        success = await WebhookConfigDao.delete(webhook_id, user_id)
        if not success:
            return {"code": 110, "data": None, "msg": "配置不存在"}
        return {"code": 0, "data": None, "msg": "删除成功"}
    except Exception as e:
        logger.error(f"删除 Webhook 配置失败: {e}")
        return {"code": 110, "data": None, "msg": f"删除配置失败: {str(e)}"}


@router.post("/test", summary="测试 Webhook")
async def test_webhook(
    form: WebhookTestForm,
    user_info: dict = Depends(get_current_user)
):
    """发送测试请求到指定 Webhook URL"""
    try:
        result = await WebhookSender.send_test(
            url=form.url,
            method=form.method,
            headers=form.headers,
            body=form.body,
            secret=form.secret,
            content_type=form.content_type or "json"
        )
        if result.get("success"):
            return {"code": 0, "data": result, "msg": "发送成功"}
        else:
            return {"code": 110, "data": result, "msg": f"发送失败: {result.get('error')}"}
    except Exception as e:
        logger.error(f"测试 Webhook 失败: {e}")
        return {"code": 110, "data": None, "msg": f"测试失败: {str(e)}"}


# ==================== 通知历史 ====================

@router.get("/histories", summary="获取通知历史")
async def list_histories(
    config_id: int = Query(None, description="Webhook配置ID"),
    status: str = Query(None, description="发送状态"),
    days: int = Query(7, ge=1, le=30, description="最近天数"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_info: dict = Depends(get_current_user)
):
    """获取通知发送历史"""
    try:
        histories, total = await NotificationHistoryDao.list_histories(
            config_id=config_id, status=status, days=days, skip=skip, limit=limit
        )
        result = [{
            "id": h.id,
            "config_id": h.config_id,
            "title": h.title,
            "content": h.content,
            "status": h.status,
            "error_message": h.error_message,
            "response_data": h.response_data,
            "sent_at": h.sent_at,
            "created_at": h.created_at
        } for h in histories]
        return {"code": 0, "data": {"list": result, "total": total}, "msg": "success"}
    except Exception as e:
        logger.error(f"获取通知历史失败: {e}")
        return {"code": 110, "data": None, "msg": f"获取通知历史失败: {str(e)}"}


@router.delete("/histories/{history_id}", summary="删除通知历史")
async def delete_history(
    history_id: int,
    user_info: dict = Depends(get_current_user)
):
    """删除通知历史记录"""
    try:
        success = await NotificationHistoryDao.delete_history(history_id)
        if not success:
            return {"code": 110, "data": None, "msg": "历史记录不存在"}
        return {"code": 0, "data": None, "msg": "删除成功"}
    except Exception as e:
        logger.error(f"删除通知历史失败: {e}")
        return {"code": 110, "data": None, "msg": f"删除失败: {str(e)}"}


# ==================== 任务通知设置 ====================

@router.get("/task-settings", summary="获取任务通知设置列表")
async def list_task_settings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_info: dict = Depends(get_current_user)
):
    """获取任务通知设置列表"""
    try:
        settings, total = await TaskNotificationSettingDao.list_settings(skip, limit)
        result = [{
            "id": s.id,
            "task_id": s.task_id,
            "task_type": s.task_type,
            "config_id": s.config_id,
            "is_enabled": s.is_enabled,
            "notify_on_success": s.notify_on_success,
            "notify_on_failure": s.notify_on_failure,
            "created_at": s.created_at,
            "updated_at": s.updated_at
        } for s in settings]
        return {"code": 0, "data": {"list": result, "total": total}, "msg": "success"}
    except Exception as e:
        logger.error(f"获取任务通知设置失败: {e}")
        return {"code": 110, "data": None, "msg": f"获取任务通知设置失败: {str(e)}"}


@router.post("/task-settings", summary="创建任务通知设置")
async def create_task_setting(
    form: TaskNotificationSettingForm,
    user_info: dict = Depends(get_current_user)
):
    """创建任务通知设置"""
    try:
        user_id = user_info.get("id")
        setting = await TaskNotificationSettingDao.create(user_id, form)
        return {
            "code": 0,
            "data": {
                "id": setting.id,
                "task_id": setting.task_id,
                "task_type": setting.task_type,
                "config_id": setting.config_id,
                "is_enabled": setting.is_enabled,
                "notify_on_success": setting.notify_on_success,
                "notify_on_failure": setting.notify_on_failure,
                "created_at": setting.created_at
            },
            "msg": "创建成功"
        }
    except Exception as e:
        logger.error(f"创建任务通知设置失败: {e}")
        return {"code": 110, "data": None, "msg": f"创建设置失败: {str(e)}"}


@router.put("/task-settings/{setting_id}", summary="更新任务通知设置")
async def update_task_setting(
    setting_id: int,
    form: TaskNotificationSettingForm,
    user_info: dict = Depends(get_current_user)
):
    """更新任务通知设置"""
    try:
        setting = await TaskNotificationSettingDao.update(setting_id, form)
        return {
            "code": 0,
            "data": {
                "id": setting.id,
                "task_id": setting.task_id,
                "task_type": setting.task_type,
                "config_id": setting.config_id,
                "is_enabled": setting.is_enabled,
                "notify_on_success": setting.notify_on_success,
                "notify_on_failure": setting.notify_on_failure,
                "updated_at": setting.updated_at
            },
            "msg": "更新成功"
        }
    except Exception as e:
        logger.error(f"更新任务通知设置失败: {e}")
        return {"code": 110, "data": None, "msg": f"更新设置失败: {str(e)}"}


@router.delete("/task-settings/{setting_id}", summary="删除任务通知设置")
async def delete_task_setting(
    setting_id: int,
    user_info: dict = Depends(get_current_user)
):
    """删除任务通知设置"""
    try:
        success = await TaskNotificationSettingDao.delete(setting_id)
        if not success:
            return {"code": 110, "data": None, "msg": "设置不存在"}
        return {"code": 0, "data": None, "msg": "删除成功"}
    except Exception as e:
        logger.error(f"删除任务通知设置失败: {e}")
        return {"code": 110, "data": None, "msg": f"删除设置失败: {str(e)}"}


# ==================== 发送通知 ====================

@router.post("/send", summary="发送通知")
async def send_notification(
    config_id: int = Query(..., description="Webhook配置ID"),
    title: str = Query(..., description="通知标题"),
    content: str = Query(None, description="通知内容"),
    user_info: dict = Depends(get_current_user)
):
    """发送通知到配置的 Webhook"""
    try:
        # 获取配置
        config = await WebhookConfigDao.get_by_id(config_id)
        if not config:
            return {"code": 110, "data": None, "msg": "Webhook 配置不存在"}

        if not config.enabled:
            return {"code": 110, "data": None, "msg": "Webhook 配置已禁用"}

        # 发送请求
        result = await WebhookSender.send(
            url=config.url,
            method=config.method,
            headers=json.loads(config.headers) if config.headers else {},
            body={"title": title, "content": content} if content else {"title": title},
            secret=config.secret,
            content_type=config.content_type
        )

        if result.get("success"):
            return {"code": 0, "data": result, "msg": "发送成功"}
        else:
            return {"code": 110, "data": result, "msg": f"发送失败: {result.get('error')}"}
    except Exception as e:
        logger.error(f"发送通知失败: {e}")
        return {"code": 110, "data": None, "msg": f"发送通知失败: {str(e)}"}
