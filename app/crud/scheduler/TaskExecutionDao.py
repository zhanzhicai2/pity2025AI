from datetime import datetime
import importlib

from sqlalchemy import select

from app.crud import Mapper, ModelWrapper, connect
from app.models.scheduler import PityTaskExecution

module = importlib.import_module(__name__)


@ModelWrapper(PityTaskExecution)
class PityTaskExecutionDao(Mapper):
    @classmethod
    @connect
    async def list_execution(cls, page: int, size: int, session=None, **kwargs):
        return await cls.list_with_pagination(page, size, session=session, **kwargs)

    @classmethod
    @connect
    async def query_execution(cls, execution_id: int, session=None):
        return await cls.query_record(session=session, id=execution_id)

    @classmethod
    @connect
    async def list_executions_by_task(cls, task_id: int, page: int, size: int, session=None):
        """获取任务的所有执行记录"""
        conditions = [cls.__model__.task_id == task_id]
        if hasattr(cls.__model__, 'deleted_at'):
            conditions.append(cls.__model__.deleted_at == 0)
        sql = select(cls.__model__).where(*conditions).order_by(cls.__model__.id.desc())
        return await cls.pagination(page, size, session, sql)

    @classmethod
    @connect
    async def insert_execution(cls, task_id: int, trace_id: str, executor: int, user_id: int, session=None):
        execution = PityTaskExecution(
            user=user_id,
            task_id=task_id,
            trace_id=trace_id,
            status="pending",
            executor=executor,
            start_time=datetime.now(),
        )
        return await cls.insert(model=execution, session=session)

    @classmethod
    @connect
    async def update_execution_success(cls, execution_id: int, result: dict, user_id: int, session=None):
        """更新执行成功状态"""
        from sqlalchemy import update
        sql = update(cls.__model__).where(cls.__model__.id == execution_id).values(
            status="success",
            result=result,
            end_time=datetime.now(),
            updated_at=datetime.now(),
            update_user=user_id,
        )
        await session.execute(sql)

    @classmethod
    @connect
    async def update_execution_failed(cls, execution_id: int, error_message: str, user_id: int, session=None):
        """更新执行失败状态"""
        from sqlalchemy import update
        sql = update(cls.__model__).where(cls.__model__.id == execution_id).values(
            status="failed",
            error_message=error_message,
            end_time=datetime.now(),
            updated_at=datetime.now(),
            update_user=user_id,
        )
        await session.execute(sql)

    @classmethod
    @connect
    async def update_execution_running(cls, execution_id: int, session=None):
        """更新为运行中状态"""
        from sqlalchemy import update
        sql = update(cls.__model__).where(cls.__model__.id == execution_id).values(
            status="running",
        )
        await session.execute(sql)

    @classmethod
    @connect
    async def query_latest_execution(cls, task_id: int, session=None):
        """获取任务最新一条执行记录"""
        conditions = [cls.__model__.task_id == task_id]
        if hasattr(cls.__model__, 'deleted_at'):
            conditions.append(cls.__model__.deleted_at == 0)
        sql = select(cls.__model__).where(*conditions).order_by(cls.__model__.id.desc()).limit(1)
        result = await session.execute(sql)
        return result.scalars().first()
