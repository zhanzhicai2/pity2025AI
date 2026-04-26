"""KnowledgeLib DAO"""
from datetime import datetime
from typing import List, Tuple

from sqlalchemy import select, func, update

from app.crud import Mapper, ModelWrapper, connect
from app.models.knowledge_lib import KnowledgeLib
from app.models.knowledge_base import KnowledgeBase


@ModelWrapper(KnowledgeLib)
class KnowledgeLibDao(Mapper):
    """知识库容器 DAO"""

    @classmethod
    @connect
    async def create_knowledge_lib(
        cls, name, project_id, description=None,
        chunk_size=500, overlap=50, user_id=None, session=None
    ):
        """创建知识库"""
        model = KnowledgeLib(user_id)
        model.name = name
        model.project_id = project_id
        model.description = description
        model.chunk_size = chunk_size
        model.overlap = overlap
        model.document_count = 0
        return await cls.insert(model=model, session=session)

    @classmethod
    @connect
    async def update_knowledge_lib(
        cls, lib_id, name=None, description=None,
        chunk_size=None, overlap=None, session=None
    ):
        """更新知识库"""
        kwargs = {"updated_at": datetime.now()}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if chunk_size is not None:
            kwargs["chunk_size"] = chunk_size
        if overlap is not None:
            kwargs["overlap"] = overlap
        stmt = update(KnowledgeLib).where(KnowledgeLib.id == lib_id).values(**kwargs)
        await session.execute(stmt)

    @classmethod
    @connect
    async def list_knowledge_libs(
        cls, project_id=None, session=None
    ) -> Tuple[List, int]:
        """列出知识库"""
        kwargs = {}
        if project_id is not None:
            kwargs["project_id"] = project_id
        return await cls.list_with_pagination(1, 1000, session=session, deleted_at=0, **kwargs)

    @classmethod
    @connect
    async def get_knowledge_lib(cls, lib_id, session=None):
        """获取单个知识库"""
        stmt = select(KnowledgeLib).where(KnowledgeLib.id == lib_id, KnowledgeLib.deleted_at == 0)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    @connect
    async def delete_knowledge_lib(cls, lib_id, user_id=None, session=None):
        """软删除知识库"""
        await cls.delete_record_by_id(session=session, user=user_id, value=lib_id)

    @classmethod
    @connect
    async def update_document_count(cls, lib_id, session=None):
        """更新文档数量统计"""
        stmt = select(func.count()).where(KnowledgeBase.lib_id == lib_id, KnowledgeBase.deleted_at == 0)
        result = await session.execute(stmt)
        count = result.scalar()
        update_stmt = update(KnowledgeLib).where(KnowledgeLib.id == lib_id).values(
            document_count=count, updated_at=datetime.now()
        )
        await session.execute(update_stmt)
