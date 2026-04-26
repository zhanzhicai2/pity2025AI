"""
需求文档 DAO 层
"""
from typing import Optional, List

from sqlalchemy import select, update

from app.crud import Mapper, ModelWrapper, connect
from app.models.requirement_document import RequirementDocument


@ModelWrapper(RequirementDocument)
class RequirementDocumentDao(Mapper):
    """需求文档数据访问对象"""

    @classmethod
    @connect
    async def list_documents(cls, session=None, project_id: Optional[int] = None, doc_type: Optional[str] = None):
        """获取文档列表"""
        query = select(RequirementDocument).where(RequirementDocument.deleted_at == 0)

        if project_id:
            query = query.where(RequirementDocument.project_id == project_id)

        if doc_type:
            query = query.where(RequirementDocument.doc_type == doc_type)

        query = query.order_by(RequirementDocument.id.desc())

        result = await session.execute(query)
        return list(result.scalars().all())

    @classmethod
    @connect
    async def get_by_id(cls, session=None, document_id: int = None):
        """根据ID获取文档"""
        query = select(RequirementDocument).where(
            RequirementDocument.id == document_id,
            RequirementDocument.deleted_at == 0
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    @connect
    async def insert(cls, session=None, model: RequirementDocument = None):
        """插入文档"""
        session.add(model)
        await session.flush()
        await session.commit()
        await session.refresh(model)
        return model

    @classmethod
    @connect
    async def update_document(cls, session=None, document_id: int = None, user_id: int = None, **kwargs):
        """更新文档"""
        kwargs['updated_at'] = __import__('datetime').datetime.now()
        kwargs['update_user'] = user_id

        stmt = (
            update(RequirementDocument)
            .where(RequirementDocument.id == document_id, RequirementDocument.deleted_at == 0)
            .values(**kwargs)
        )
        await session.execute(stmt)
        await session.commit()

        query = select(RequirementDocument).where(RequirementDocument.id == document_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    @connect
    async def delete_document(cls, session=None, document_id: int = None, user_id: int = None):
        """删除文档（逻辑删除）"""
        query = select(RequirementDocument).where(
            RequirementDocument.id == document_id,
            RequirementDocument.deleted_at == 0
        )
        result = await session.execute(query)
        document = result.scalar_one_or_none()
        if not document:
            return False

        stmt = (
            update(RequirementDocument)
            .where(RequirementDocument.id == document_id)
            .values(
                deleted_at=int(__import__('time').time() * 1000),
                update_user=user_id
            )
        )
        await session.execute(stmt)
        await session.commit()
        return True

    @classmethod
    @connect
    async def search_by_content(cls, session=None, keyword: str = None, project_id: Optional[int] = None):
        """搜索文档内容"""
        query = select(RequirementDocument).where(
            RequirementDocument.deleted_at == 0,
            RequirementDocument.content.like(f'%{keyword}%')
        )

        if project_id:
            query = query.where(RequirementDocument.project_id == project_id)

        query = query.order_by(RequirementDocument.id.desc())

        result = await session.execute(query)
        return list(result.scalars().all())
