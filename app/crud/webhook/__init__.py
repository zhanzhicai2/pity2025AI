"""
Webhook DAO
"""
import json
import time
from typing import List, Optional

from sqlalchemy import select, or_, desc

from app.crud import Mapper, ModelWrapper
from app.models import async_session
from app.models.webhook import WebhookConfig, NotificationHistory, TaskNotificationSetting
from app.schema.webhook import WebhookConfigForm, TaskNotificationSettingForm


@ModelWrapper(WebhookConfig)
class WebhookConfigDao(Mapper):

    @classmethod
    async def create(cls, user_id: int, form: WebhookConfigForm):
        """创建 Webhook 配置"""
        try:
            async with async_session() as session:
                async with session.begin():
                    data = WebhookConfig(
                        user_id=user_id,
                        name=form.name,
                        url=form.url,
                        method=form.method,
                        headers=form.headers or "{}",
                        secret=form.secret,
                        event_type=form.event_type,
                        content_type=form.content_type or "json",
                        template=form.template,
                        enabled=form.enabled,
                        is_default=form.is_default,
                        created_at=int(time.time() * 1000),
                        updated_at=int(time.time() * 1000)
                    )
                    session.add(data)
                    await session.flush()
                    await session.refresh(data)
                    session.expunge(data)
                    return data
        except Exception as e:
            cls.__log__.error(f"创建 Webhook 配置失败, error: {str(e)}")
            raise Exception(f"创建 Webhook 配置失败, {str(e)}")

    @classmethod
    async def get_by_id(cls, webhook_id: int, user_id: Optional[int] = None):
        """获取 Webhook 配置"""
        try:
            async with async_session() as session:
                conditions = [WebhookConfig.id == webhook_id]
                if user_id is not None:
                    conditions.append(WebhookConfig.user_id == user_id)
                sql = select(WebhookConfig).where(*conditions)
                result = await session.execute(sql)
                return result.scalars().first()
        except Exception as e:
            cls.__log__.error(f"获取 Webhook 配置失败, error: {str(e)}")
            raise Exception(f"获取 Webhook 配置失败, {str(e)}")

    @classmethod
    async def list_configs(cls, user_id: int, skip: int = 0, limit: int = 20):
        """获取 Webhook 配置列表"""
        try:
            async with async_session() as session:
                conditions = [WebhookConfig.user_id == user_id]
                sql = select(WebhookConfig).where(*conditions).order_by(
                    desc(WebhookConfig.updated_at)
                ).offset(skip).limit(limit)
                result = await session.execute(sql)
                configs = result.scalars().all()

                count_sql = select(WebhookConfig).where(*conditions)
                count_result = await session.execute(count_sql)
                total = len(count_result.scalars().all())

                return configs, total
        except Exception as e:
            cls.__log__.error(f"获取 Webhook 配置列表失败, error: {str(e)}")
            raise Exception(f"获取 Webhook 配置列表失败, {str(e)}")

    @classmethod
    async def update(cls, webhook_id: int, user_id: int, form: WebhookConfigForm):
        """更新 Webhook 配置"""
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(WebhookConfig).where(
                        WebhookConfig.id == webhook_id,
                        WebhookConfig.user_id == user_id
                    )
                    result = await session.execute(sql)
                    data = result.scalars().first()
                    if not data:
                        raise Exception("Webhook 配置不存在")

                    data.name = form.name
                    data.url = form.url
                    data.method = form.method
                    data.headers = form.headers or "{}"
                    data.secret = form.secret
                    data.event_type = form.event_type
                    data.content_type = form.content_type or "json"
                    data.template = form.template
                    data.enabled = form.enabled
                    data.is_default = form.is_default
                    data.updated_at = int(time.time() * 1000)

                    await session.flush()
                    session.expunge(data)
                    return data
        except Exception as e:
            cls.__log__.error(f"更新 Webhook 配置失败, error: {str(e)}")
            raise Exception(f"更新 Webhook 配置失败, {str(e)}")

    @classmethod
    async def delete(cls, webhook_id: int, user_id: int):
        """删除 Webhook 配置"""
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(WebhookConfig).where(
                        WebhookConfig.id == webhook_id,
                        WebhookConfig.user_id == user_id
                    )
                    result = await session.execute(sql)
                    data = result.scalars().first()
                    if not data:
                        return False
                    await session.delete(data)
                    return True
        except Exception as e:
            cls.__log__.error(f"删除 Webhook 配置失败, error: {str(e)}")
            raise Exception(f"删除 Webhook 配置失败, {str(e)}")

    @classmethod
    async def get_by_event_type(cls, event_type: str):
        """获取指定事件类型的已启用 Webhook 配置"""
        try:
            async with async_session() as session:
                sql = select(WebhookConfig).where(
                    WebhookConfig.event_type == event_type,
                    WebhookConfig.enabled == True
                )
                result = await session.execute(sql)
                return result.scalars().all()
        except Exception as e:
            cls.__log__.error(f"获取事件类型 Webhook 失败, error: {str(e)}")
            raise Exception(f"获取事件类型 Webhook 失败, {str(e)}")

    @classmethod
    async def get_default(cls, user_id: int):
        """获取用户默认配置"""
        try:
            async with async_session() as session:
                sql = select(WebhookConfig).where(
                    WebhookConfig.user_id == user_id,
                    WebhookConfig.is_default == True,
                    WebhookConfig.enabled == True
                )
                result = await session.execute(sql)
                return result.scalars().first()
        except Exception as e:
            cls.__log__.error(f"获取默认 Webhook 配置失败, error: {str(e)}")
            raise Exception(f"获取默认 Webhook 配置失败, {str(e)}")


@ModelWrapper(NotificationHistory)
class NotificationHistoryDao(Mapper):

    @classmethod
    async def create(cls, config_id: int, title: str, content: str = None,
                     status: str = "pending", error_message: str = None,
                     response_data: str = None):
        """创建通知历史"""
        try:
            async with async_session() as session:
                async with session.begin():
                    data = NotificationHistory(
                        config_id=config_id,
                        title=title,
                        content=content,
                        status=status,
                        error_message=error_message,
                        response_data=response_data,
                        sent_at=int(time.time() * 1000) if status == "success" else None,
                        created_at=int(time.time() * 1000)
                    )
                    session.add(data)
                    await session.flush()
                    await session.refresh(data)
                    session.expunge(data)
                    return data
        except Exception as e:
            cls.__log__.error(f"创建通知历史失败, error: {str(e)}")
            raise Exception(f"创建通知历史失败, {str(e)}")

    @classmethod
    async def update_status(cls, history_id: int, status: str,
                           error_message: str = None, response_data: str = None):
        """更新通知状态"""
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(NotificationHistory).where(
                        NotificationHistory.id == history_id
                    )
                    result = await session.execute(sql)
                    data = result.scalars().first()
                    if not data:
                        return None

                    data.status = status
                    if status == "success":
                        data.sent_at = int(time.time() * 1000)
                    if error_message:
                        data.error_message = error_message
                    if response_data:
                        data.response_data = response_data

                    await session.flush()
                    session.expunge(data)
                    return data
        except Exception as e:
            cls.__log__.error(f"更新通知状态失败, error: {str(e)}")
            raise Exception(f"更新通知状态失败, {str(e)}")

    @classmethod
    async def list_histories(cls, config_id: int = None, status: str = None,
                            days: int = 7, skip: int = 0, limit: int = 100):
        """获取通知历史列表"""
        try:
            async with async_session() as session:
                conditions = []
                if config_id is not None:
                    conditions.append(NotificationHistory.config_id == config_id)
                if status:
                    conditions.append(NotificationHistory.status == status)

                # 时间范围
                time_threshold = int(time.time() * 1000) - days * 24 * 60 * 60 * 1000
                conditions.append(NotificationHistory.created_at >= time_threshold)

                sql = select(NotificationHistory).where(*conditions).order_by(
                    desc(NotificationHistory.created_at)
                ).offset(skip).limit(limit)
                result = await session.execute(sql)
                histories = result.scalars().all()

                count_sql = select(NotificationHistory).where(*conditions)
                count_result = await session.execute(count_sql)
                total = len(count_result.scalars().all())

                return histories, total
        except Exception as e:
            cls.__log__.error(f"获取通知历史列表失败, error: {str(e)}")
            raise Exception(f"获取通知历史列表失败, {str(e)}")

    @classmethod
    async def delete_history(cls, history_id: int):
        """删除通知历史"""
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(NotificationHistory).where(
                        NotificationHistory.id == history_id
                    )
                    result = await session.execute(sql)
                    data = result.scalars().first()
                    if not data:
                        return False
                    await session.delete(data)
                    return True
        except Exception as e:
            cls.__log__.error(f"删除通知历史失败, error: {str(e)}")
            raise Exception(f"删除通知历史失败, {str(e)}")


@ModelWrapper(TaskNotificationSetting)
class TaskNotificationSettingDao(Mapper):

    @classmethod
    async def create(cls, user_id: int, form: TaskNotificationSettingForm):
        """创建任务通知设置"""
        try:
            async with async_session() as session:
                async with session.begin():
                    data = TaskNotificationSetting(
                        task_id=form.task_id,
                        task_type=form.task_type,
                        config_id=form.config_id,
                        is_enabled=form.is_enabled,
                        notify_on_success=form.notify_on_success,
                        notify_on_failure=form.notify_on_failure,
                        created_at=int(time.time() * 1000),
                        updated_at=int(time.time() * 1000)
                    )
                    session.add(data)
                    await session.flush()
                    await session.refresh(data)
                    session.expunge(data)
                    return data
        except Exception as e:
            cls.__log__.error(f"创建任务通知设置失败, error: {str(e)}")
            raise Exception(f"创建任务通知设置失败, {str(e)}")

    @classmethod
    async def get_by_task(cls, task_id: int, task_type: str):
        """获取任务的通知设置"""
        try:
            async with async_session() as session:
                sql = select(TaskNotificationSetting).where(
                    TaskNotificationSetting.task_id == task_id,
                    TaskNotificationSetting.task_type == task_type
                )
                result = await session.execute(sql)
                return result.scalars().first()
        except Exception as e:
            cls.__log__.error(f"获取任务通知设置失败, error: {str(e)}")
            raise Exception(f"获取任务通知设置失败, {str(e)}")

    @classmethod
    async def list_settings(cls, skip: int = 0, limit: int = 100):
        """获取任务通知设置列表"""
        try:
            async with async_session() as session:
                sql = select(TaskNotificationSetting).order_by(
                    desc(TaskNotificationSetting.updated_at)
                ).offset(skip).limit(limit)
                result = await session.execute(sql)
                settings = result.scalars().all()

                count_sql = select(TaskNotificationSetting)
                count_result = await session.execute(count_sql)
                total = len(count_result.scalars().all())

                return settings, total
        except Exception as e:
            cls.__log__.error(f"获取任务通知设置列表失败, error: {str(e)}")
            raise Exception(f"获取任务通知设置列表失败, {str(e)}")

    @classmethod
    async def update(cls, setting_id: int, form: TaskNotificationSettingForm):
        """更新任务通知设置"""
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(TaskNotificationSetting).where(
                        TaskNotificationSetting.id == setting_id
                    )
                    result = await session.execute(sql)
                    data = result.scalars().first()
                    if not data:
                        raise Exception("通知设置不存在")

                    data.config_id = form.config_id
                    data.is_enabled = form.is_enabled
                    data.notify_on_success = form.notify_on_success
                    data.notify_on_failure = form.notify_on_failure
                    data.updated_at = int(time.time() * 1000)

                    await session.flush()
                    session.expunge(data)
                    return data
        except Exception as e:
            cls.__log__.error(f"更新任务通知设置失败, error: {str(e)}")
            raise Exception(f"更新任务通知设置失败, {str(e)}")

    @classmethod
    async def delete(cls, setting_id: int):
        """删除任务通知设置"""
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(TaskNotificationSetting).where(
                        TaskNotificationSetting.id == setting_id
                    )
                    result = await session.execute(sql)
                    data = result.scalars().first()
                    if not data:
                        return False
                    await session.delete(data)
                    return True
        except Exception as e:
            cls.__log__.error(f"删除任务通知设置失败, error: {str(e)}")
            raise Exception(f"删除任务通知设置失败, {str(e)}")
