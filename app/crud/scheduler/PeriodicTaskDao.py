import importlib

from app.crud import Mapper, ModelWrapper, connect
from app.models.scheduler import PityPeriodicTask

module = importlib.import_module(__name__)


@ModelWrapper(PityPeriodicTask)
class PityPeriodicTaskDao(Mapper):
    @classmethod
    @connect
    async def list_task(cls, page: int, size: int, session=None, **kwargs):
        return await cls.list_with_pagination(page, size, session=session, **kwargs)

    @classmethod
    @connect
    async def query_task(cls, task_id: int, session=None):
        return await cls.query_record(session=session, id=task_id)

    @classmethod
    @connect
    async def query_task_by_name(cls, name: str, session=None):
        return await cls.query_record(session=session, name=name)

    @classmethod
    @connect
    async def insert_task(cls, form, user_id: int, session=None):
        task = PityPeriodicTask(
            user=user_id,
            name=form.name,
            description=form.description,
            task_type=form.task_type,
            task_config=form.task_config,
            schedule_type=form.schedule_type,
            crontab_id=form.crontab_id,
            interval_id=form.interval_id,
            enabled=form.enabled,
            project_id=form.project_id,
            notify_on_failure=form.notify_on_failure,
            max_instances=form.max_instances,
        )
        return await cls.insert(model=task, session=session)

    @classmethod
    @connect
    async def update_task(cls, task_id: int, form, user_id: int, session=None):
        # 先查询现有数据
        existing = await cls.query_record(session=session, id=task_id)
        if existing is None:
            raise Exception("任务不存在")

        # 更新字段
        from app.crud import Mapper as MapperBase
        changed = MapperBase.update_model(existing, form, user_id, not_null=True)
        await session.flush()
        session.expunge(existing)
        return existing

    @classmethod
    @connect
    async def delete_task(cls, task_id: int, user_id: int, session=None):
        return await cls.delete_record_by_id(session=session, user=user_id, value=task_id, key='id')

    @classmethod
    @connect
    async def toggle_task(cls, task_id: int, enabled: bool, user_id: int, session=None):
        await cls.update_by_map(
            user_id,
            cls.__model__.id == task_id,
            session=session,
            enabled=enabled,
        )

    @classmethod
    @connect
    async def list_enabled_tasks(cls, session=None):
        """获取所有启用的任务"""
        return await cls.select_list(session=session, enabled=True)

    @classmethod
    @connect
    async def list_tasks_by_project(cls, project_id: int, session=None):
        """获取指定项目的所有任务"""
        return await cls.select_list(session=session, project_id=project_id)
