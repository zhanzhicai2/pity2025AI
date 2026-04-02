import importlib

from app.crud import Mapper, ModelWrapper, connect
from app.models.test_suite import TestSuite

module = importlib.import_module(__name__)


@ModelWrapper(TestSuite)
class TestSuiteDao(Mapper):
    @classmethod
    @connect
    async def list_suite(cls, page: int, size: int, session=None, **kwargs):
        return await cls.list_with_pagination(page, size, session=session, **kwargs)

    @classmethod
    @connect
    async def query_suite(cls, suite_id: int, session=None):
        return await cls.query_record(session=session, id=suite_id)

    @classmethod
    @connect
    async def query_suite_by_name(cls, name: str, project_id: int, session=None):
        return await cls.query_record(session=session, name=name, project_id=project_id)

    @classmethod
    @connect
    async def insert_suite(cls, form, user_id: int, session=None):
        suite = TestSuite(
            user=user_id,
            name=form.name,
            description=form.description,
            project_id=form.project_id,
            env_id=form.env_id,
            execution_mode=form.execution_mode,
            retry_on_failure=form.retry_on_failure,
            stop_on_failure=form.stop_on_failure,
            notify_on_failure=form.notify_on_failure,
        )
        return await cls.insert(model=suite, session=session)

    @classmethod
    @connect
    async def update_suite(cls, suite_id: int, form, user_id: int, session=None):
        existing = await cls.query_record(session=session, id=suite_id)
        if existing is None:
            raise Exception("套件不存在")

        from app.crud import Mapper as MapperBase
        changed = MapperBase.update_model(existing, form, user_id, not_null=True)
        await session.flush()
        session.expunge(existing)
        return existing

    @classmethod
    @connect
    async def delete_suite(cls, suite_id: int, user_id: int, session=None):
        return await cls.delete_record_by_id(session=session, user=user_id, value=suite_id, key='id')

    @classmethod
    @connect
    async def list_suites_by_project(cls, project_id: int, session=None):
        return await cls.select_list(session=session, project_id=project_id)
