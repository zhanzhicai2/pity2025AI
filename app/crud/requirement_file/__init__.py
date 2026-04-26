"""
需求文件 DAO 层
"""
from typing import Optional

from sqlalchemy import select, update

from app.crud import Mapper, ModelWrapper, connect
from app.models.requirement_file import RequirementFile


@ModelWrapper(RequirementFile)
class RequirementFileDao(Mapper):
    """需求文件数据访问对象"""

    @classmethod
    @connect
    async def list_files(cls, session=None, requirement_id: int = None):
        """获取指定需求文档下的文件列表"""
        query = (
            select(RequirementFile)
            .where(
                RequirementFile.requirement_id == requirement_id,
                RequirementFile.deleted_at == 0,
            )
            .order_by(RequirementFile.id.desc())
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @classmethod
    @connect
    async def get_by_id(cls, session=None, file_id: int = None):
        """根据ID获取文件"""
        query = select(RequirementFile).where(
            RequirementFile.id == file_id,
            RequirementFile.deleted_at == 0,
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    @connect
    async def insert(cls, session=None, model: RequirementFile = None):
        """插入文件记录"""
        session.add(model)
        await session.flush()
        await session.commit()
        await session.refresh(model)
        return model

    @classmethod
    @connect
    async def delete_file(cls, session=None, file_id: int = None, user_id: int = None):
        """逻辑删除文件"""
        query = select(RequirementFile).where(
            RequirementFile.id == file_id,
            RequirementFile.deleted_at == 0,
        )
        result = await session.execute(query)
        file = result.scalar_one_or_none()
        if not file:
            return None

        stmt = (
            update(RequirementFile)
            .where(RequirementFile.id == file_id)
            .values(
                deleted_at=int(__import__('time').time() * 1000),
                update_user=user_id,
            )
        )
        await session.execute(stmt)
        await session.commit()
        return file
