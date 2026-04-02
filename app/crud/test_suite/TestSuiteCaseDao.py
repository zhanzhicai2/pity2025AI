import importlib

from sqlalchemy import select

from app.crud import Mapper, ModelWrapper, connect
from app.models.test_suite import TestSuiteCase

module = importlib.import_module(__name__)


@ModelWrapper(TestSuiteCase)
class TestSuiteCaseDao(Mapper):
    @classmethod
    @connect
    async def list_cases(cls, page: int, size: int, suite_id: int, session=None):
        conditions = [cls.__model__.suite_id == suite_id]
        if hasattr(cls.__model__, 'deleted_at'):
            conditions.append(cls.__model__.deleted_at == 0)
        sql = select(cls.__model__).where(*conditions).order_by(cls.__model__.order)
        return await cls.pagination(page, size, session, sql)

    @classmethod
    @connect
    async def list_all_cases(cls, suite_id: int, session=None):
        """获取套件下所有用例（用于执行）"""
        conditions = [
            cls.__model__.suite_id == suite_id,
            cls.__model__.enabled == True,
        ]
        if hasattr(cls.__model__, 'deleted_at'):
            conditions.append(cls.__model__.deleted_at == 0)
        sql = select(cls.__model__).where(*conditions).order_by(cls.__model__.order)
        result = await session.execute(sql)
        return result.scalars().all()

    @classmethod
    @connect
    async def query_case(cls, case_id: int, suite_id: int, session=None):
        return await cls.query_record(session=session, id=case_id, suite_id=suite_id)

    @classmethod
    @connect
    async def insert_case(cls, form, suite_id: int, user_id: int, session=None):
        suite_case = TestSuiteCase(
            user=user_id,
            suite_id=suite_id,
            case_id=form.case_id,
            order=form.order,
            enabled=form.enabled,
            timeout=form.timeout,
            retry=form.retry,
        )
        return await cls.insert(model=suite_case, session=session)

    @classmethod
    @connect
    async def update_case(cls, case_id: int, form, user_id: int, session=None):
        existing = await cls.query_record(session=session, id=case_id)
        if existing is None:
            raise Exception("套件用例不存在")

        from app.crud import Mapper as MapperBase
        changed = MapperBase.update_model(existing, form, user_id, not_null=True)
        await session.flush()
        session.expunge(existing)
        return existing

    @classmethod
    @connect
    async def delete_case(cls, case_id: int, user_id: int, session=None):
        return await cls.delete_record_by_id(session=session, user=user_id, value=case_id, key='id')

    @classmethod
    @connect
    async def reorder_cases(cls, suite_id: int, cases: list, user_id: int, session=None):
        """批量更新用例顺序"""
        for item in cases:
            case_id = item.get("id")
            order = item.get("order")
            if case_id and order is not None:
                existing = await cls.query_record(session=session, id=case_id)
                if existing:
                    existing.order = order
                    existing.update_user = user_id
        await session.flush()
