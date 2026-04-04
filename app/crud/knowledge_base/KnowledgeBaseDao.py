"""
KnowledgeBase DAO
"""
from app.crud import Mapper, ModelWrapper, connect
from app.models.knowledge_base import KnowledgeBase


@ModelWrapper(KnowledgeBase)
class KnowledgeBaseDao(Mapper):
    """知识库文档 DAO"""

    @classmethod
    @connect
    async def insert_knowledge(
        cls, name, file_type, file_path, file_size, content_hash,
        status, chunk_count, doc_metadata=None, user_id=None, session=None
    ):
        """插入知识库文档记录"""
        model = KnowledgeBase()
        model.name = name
        model.file_type = file_type
        model.file_path = file_path
        model.file_size = file_size
        model.content_hash = content_hash
        model.doc_metadata = doc_metadata or {}
        model.status = status
        model.chunk_count = chunk_count
        model.create_user = user_id
        return await cls.insert(model=model, session=session)

    @classmethod
    @connect
    async def update_status(cls, id, status, error_msg=None, chunk_count=None, session=None):
        """更新文档状态"""
        kwargs = {"status": status}
        if error_msg is not None:
            kwargs["error_msg"] = error_msg
        if chunk_count is not None:
            kwargs["chunk_count"] = chunk_count
        await cls.update_by_id(id, session=session, **kwargs)

    @classmethod
    @connect
    async def list_knowledge(cls, page=1, size=20, name=None, status=None, session=None):
        """分页查询知识库文档"""
        kwargs = {}
        if name:
            kwargs["name"] = name
        if status:
            kwargs["status"] = status
        return await cls.list_with_pagination(page, size, session=session, **kwargs)
