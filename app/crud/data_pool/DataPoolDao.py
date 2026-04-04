from typing import List, Optional

from sqlalchemy import select

from app.crud import Mapper, ModelWrapper
from app.models import async_session
from app.models.data_pool import DataPoolRecord
from app.schema.data_pool import DataPoolRecordForm


@ModelWrapper(DataPoolRecord)
class DataPoolDao(Mapper):

    @classmethod
    async def insert_record(cls, form: DataPoolRecordForm, user_id: int):
        try:
            async with async_session() as session:
                async with session.begin():
                    data = DataPoolRecord(**form.model_dump(), user_id=user_id)
                    session.add(data)
                    await session.flush()
                    await session.refresh(data)
                    session.expunge(data)
                    return data
        except Exception as e:
            cls.__log__.error(f"新增数据池记录失败, error: {str(e)}")
            raise Exception(f"新增数据池记录失败, {str(e)}")

    @classmethod
    async def update_record(cls, form: DataPoolRecordForm, user: int):
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(DataPoolRecord).where(
                        DataPoolRecord.id == form.id,
                        DataPoolRecord.deleted_at == 0
                    )
                    result = await session.execute(sql)
                    query = result.scalars().first()
                    if query is None:
                        raise Exception("数据池记录不存在")
                    cls.update_model(query, form, user)
                    await session.flush()
                    session.expunge(query)
                    return query
        except Exception as e:
            cls.__log__.error(f"编辑数据池记录失败, error: {str(e)}")
            raise Exception(f"编辑数据池记录失败, {str(e)}")

    @classmethod
    async def delete_record(cls, id: int, user: int):
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(DataPoolRecord).where(
                        DataPoolRecord.id == id,
                        DataPoolRecord.deleted_at == 0
                    )
                    result = await session.execute(sql)
                    query = result.scalars().first()
                    if query is None:
                        raise Exception("数据池记录不存在")
                    cls.delete_model(query, user)
        except Exception as e:
            cls.__log__.error(f"删除数据池记录失败, error: {str(e)}")
            raise Exception(f"删除数据池记录失败, {str(e)}")

    @classmethod
    async def list_records(
        cls,
        user_id: int,
        page: int = 1,
        size: int = 20,
        tool_name: Optional[str] = None,
        tool_category: Optional[str] = None,
        is_favorite: Optional[bool] = None
    ):
        try:
            async with async_session() as session:
                # 构建查询条件
                conditions = [DataPoolRecord.deleted_at == 0]
                if user_id:
                    conditions.append(DataPoolRecord.user_id == user_id)
                if tool_name:
                    conditions.append(DataPoolRecord.tool_name == tool_name)
                if tool_category:
                    conditions.append(DataPoolRecord.tool_category == tool_category)
                if is_favorite is not None:
                    conditions.append(DataPoolRecord.is_favorite == is_favorite)

                # 分页查询
                offset = (page - 1) * size
                sql = select(DataPoolRecord).where(*conditions).offset(offset).limit(size)
                result = await session.execute(sql)
                records = result.scalars().all()

                # 统计总数
                count_sql = select(DataPoolRecord).where(*conditions)
                count_result = await session.execute(count_sql)
                total = len(count_result.scalars().all())

                return records, total
        except Exception as e:
            cls.__log__.error(f"查询数据池记录失败, error: {str(e)}")
            raise Exception(f"查询数据池记录失败, {str(e)}")

    @classmethod
    async def favorite_record(cls, id: int, user: int, is_favorite: bool):
        try:
            async with async_session() as session:
                async with session.begin():
                    sql = select(DataPoolRecord).where(
                        DataPoolRecord.id == id,
                        DataPoolRecord.deleted_at == 0
                    )
                    result = await session.execute(sql)
                    query = result.scalars().first()
                    if query is None:
                        raise Exception("数据池记录不存在")
                    query.is_favorite = is_favorite
                    query.update_user = user
                    await session.flush()
                    session.expunge(query)
                    return query
        except Exception as e:
            cls.__log__.error(f"收藏数据池记录失败, error: {str(e)}")
            raise Exception(f"收藏数据池记录失败, {str(e)}")
