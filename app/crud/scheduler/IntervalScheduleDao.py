import importlib

from app.crud import Mapper, ModelWrapper, connect
from app.models.scheduler import PityIntervalSchedule

module = importlib.import_module(__name__)


@ModelWrapper(PityIntervalSchedule)
class PityIntervalScheduleDao(Mapper):
    @classmethod
    @connect
    async def list_interval(cls, session=None, **kwargs):
        return await cls.select_list(session=session, **kwargs)

    @classmethod
    @connect
    async def query_interval(cls, interval_id: int, session=None):
        return await cls.query_record(session=session, id=interval_id)

    @classmethod
    @connect
    async def insert_interval(cls, form, user_id: int, session=None):
        interval = PityIntervalSchedule(
            user=user_id,
            interval_type=form.interval_type,
            interval_value=form.interval_value,
        )
        return await cls.insert(model=interval, session=session)

    @classmethod
    @connect
    async def update_interval(cls, interval_id: int, form, user_id: int, session=None):
        interval = PityIntervalSchedule(
            user=user_id,
            interval_type=form.interval_type,
            interval_value=form.interval_value,
        )
        interval.id = interval_id
        return await cls.update_record_by_id(user_id, interval, not_null=True, session=session)

    @classmethod
    @connect
    async def delete_interval(cls, interval_id: int, user_id: int, session=None):
        return await cls.delete_record_by_id(session=session, user=user_id, value=interval_id, key='id')
