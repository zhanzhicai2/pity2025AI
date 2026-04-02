import importlib

from app.crud import Mapper, ModelWrapper, connect
from app.models.scheduler import PityCrontabSchedule

module = importlib.import_module(__name__)


@ModelWrapper(PityCrontabSchedule)
class PityCrontabScheduleDao(Mapper):
    @classmethod
    @connect
    async def list_crontab(cls, session=None, **kwargs):
        return await cls.select_list(session=session, **kwargs)

    @classmethod
    @connect
    async def query_crontab(cls, crontab_id: int, session=None):
        return await cls.query_record(session=session, id=crontab_id)

    @classmethod
    @connect
    async def insert_crontab(cls, form, user_id: int, session=None):
        crontab = PityCrontabSchedule(
            user=user_id,
            minute=form.minute,
            hour=form.hour,
            day_of_week=form.day_of_week,
            day_of_month=form.day_of_month,
            month_of_year=form.month_of_year,
            expression=form.expression,
        )
        return await cls.insert(model=crontab, session=session)

    @classmethod
    @connect
    async def update_crontab(cls, crontab_id: int, form, user_id: int, session=None):
        crontab = PityCrontabSchedule(
            user=user_id,
            minute=form.minute,
            hour=form.hour,
            day_of_week=form.day_of_week,
            day_of_month=form.day_of_month,
            month_of_year=form.month_of_year,
            expression=form.expression,
        )
        crontab.id = crontab_id
        return await cls.update_record_by_id(user_id, crontab, not_null=True, session=session)

    @classmethod
    @connect
    async def delete_crontab(cls, crontab_id: int, user_id: int, session=None):
        return await cls.delete_record_by_id(session=session, user=user_id, value=crontab_id, key='id')
