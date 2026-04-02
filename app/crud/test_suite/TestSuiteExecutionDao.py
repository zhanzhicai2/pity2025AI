from datetime import datetime
import importlib

from sqlalchemy import select, update

from app.crud import Mapper, ModelWrapper, connect
from app.models.test_suite import TestSuiteExecution

module = importlib.import_module(__name__)


@ModelWrapper(TestSuiteExecution)
class TestSuiteExecutionDao(Mapper):
    @classmethod
    @connect
    async def list_executions(cls, page: int, size: int, suite_id: int, session=None):
        conditions = [cls.__model__.suite_id == suite_id]
        if hasattr(cls.__model__, 'deleted_at'):
            conditions.append(cls.__model__.deleted_at == 0)
        sql = select(cls.__model__).where(*conditions).order_by(cls.__model__.id.desc())
        return await cls.pagination(page, size, session, sql)

    @classmethod
    @connect
    async def query_execution(cls, execution_id: int, session=None):
        return await cls.query_record(session=session, id=execution_id)

    @classmethod
    @connect
    async def insert_execution(cls, suite_id: int, trace_id: str, executor: int, user_id: int, session=None):
        execution = TestSuiteExecution(
            user=user_id,
            suite_id=suite_id,
            trace_id=trace_id,
            status="pending",
            executor=executor,
            start_time=datetime.now(),
        )
        return await cls.insert(model=execution, session=session)

    @classmethod
    @connect
    async def update_execution_started(cls, execution_id: int, session=None):
        """更新执行开始"""
        sql = update(cls.__model__).where(cls.__model__.id == execution_id).values(
            status="running",
            start_time=datetime.now(),
        )
        await session.execute(sql)

    @classmethod
    @connect
    async def update_execution_result(cls, execution_id: int, total: int, passed: int, failed: int, error: int,
                                     user_id: int, session=None):
        """更新执行结果"""
        status = "success" if failed == 0 and error == 0 else "failed"
        sql = update(cls.__model__).where(cls.__model__.id == execution_id).values(
            status=status,
            total_cases=total,
            passed=passed,
            failed=failed,
            error=error,
            end_time=datetime.now(),
            updated_at=datetime.now(),
            update_user=user_id,
        )
        await session.execute(sql)

    @classmethod
    @connect
    async def update_execution_failed(cls, execution_id: int, error_message: str, user_id: int, session=None):
        """更新执行失败状态"""
        sql = update(cls.__model__).where(cls.__model__.id == execution_id).values(
            status="failed",
            end_time=datetime.now(),
            updated_at=datetime.now(),
            update_user=user_id,
        )
        await session.execute(sql)

    @classmethod
    @connect
    async def query_latest_execution(cls, suite_id: int, session=None):
        """获取套件最新一条执行记录"""
        conditions = [cls.__model__.suite_id == suite_id]
        if hasattr(cls.__model__, 'deleted_at'):
            conditions.append(cls.__model__.deleted_at == 0)
        sql = select(cls.__model__).where(*conditions).order_by(cls.__model__.id.desc()).limit(1)
        result = await session.execute(sql)
        return result.scalars().first()
