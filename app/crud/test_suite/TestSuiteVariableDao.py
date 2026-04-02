import importlib

from app.crud import Mapper, ModelWrapper, connect
from app.models.test_suite import TestSuiteVariable

module = importlib.import_module(__name__)


@ModelWrapper(TestSuiteVariable)
class TestSuiteVariableDao(Mapper):
    @classmethod
    @connect
    async def list_variables(cls, suite_id: int, session=None):
        return await cls.select_list(session=session, suite_id=suite_id)

    @classmethod
    @connect
    async def query_variable(cls, var_id: int, suite_id: int, session=None):
        return await cls.query_record(session=session, id=var_id, suite_id=suite_id)

    @classmethod
    @connect
    async def insert_variable(cls, form, suite_id: int, user_id: int, session=None):
        variable = TestSuiteVariable(
            user=user_id,
            suite_id=suite_id,
            key=form.key,
            value=form.value,
            var_type=form.var_type,
            description=form.description,
        )
        return await cls.insert(model=variable, session=session)

    @classmethod
    @connect
    async def update_variable(cls, var_id: int, form, user_id: int, session=None):
        existing = await cls.query_record(session=session, id=var_id)
        if existing is None:
            raise Exception("变量不存在")

        from app.crud import Mapper as MapperBase
        changed = MapperBase.update_model(existing, form, user_id, not_null=True)
        await session.flush()
        session.expunge(existing)
        return existing

    @classmethod
    @connect
    async def delete_variable(cls, var_id: int, user_id: int, session=None):
        return await cls.delete_record_by_id(session=session, user=user_id, value=var_id, key='id')
