"""
需求文档 DAO 层
"""
from typing import Optional, List

from sqlalchemy import select, update

from app.crud import Mapper, ModelWrapper
from app.models import async_session
from app.models.requirement_document import RequirementDocument


@ModelWrapper(RequirementDocument)
class RequirementDocumentDao(Mapper):
    """需求文档数据访问对象"""

    @classmethod
    async def list_documents(
        cls,
        project_id: Optional[int] = None,
        doc_type: Optional[str] = None
    ) -> List[RequirementDocument]:
        """获取文档列表"""
        async with async_session() as session:
            query = select(RequirementDocument).where(RequirementDocument.deleted_at == 0)

            if project_id:
                query = query.where(RequirementDocument.project_id == project_id)

            if doc_type:
                query = query.where(RequirementDocument.doc_type == doc_type)

            query = query.order_by(RequirementDocument.id.desc())

            result = await session.execute(query)
            return list(result.scalars().all())

    @classmethod
    async def get_by_id(cls, document_id: int) -> Optional[RequirementDocument]:
        """根据ID获取文档"""
        async with async_session() as session:
            query = select(RequirementDocument).where(
                RequirementDocument.id == document_id,
                RequirementDocument.deleted_at == 0
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def insert(cls, model: RequirementDocument) -> RequirementDocument:
        """插入文档"""
        async with async_session() as session:
            session.add(model)
            await session.flush()
            await session.commit()
            await session.refresh(model)
            return model

    @classmethod
    async def update_document(cls, document_id: int, user_id: int, **kwargs) -> Optional[RequirementDocument]:
        """更新文档"""
        async with async_session() as session:
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
    async def delete_document(cls, document_id: int, user_id: int) -> bool:
        """删除文档（逻辑删除）"""
        async with async_session() as session:
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
    async def search_by_content(cls, keyword: str, project_id: Optional[int] = None) -> List[RequirementDocument]:
        """搜索文档内容"""
        async with async_session() as session:
            query = select(RequirementDocument).where(
                RequirementDocument.deleted_at == 0,
                RequirementDocument.content.like(f'%{keyword}%')
            )

            if project_id:
                query = query.where(RequirementDocument.project_id == project_id)

            query = query.order_by(RequirementDocument.id.desc())

            result = await session.execute(query)
            return list(result.scalars().all())
