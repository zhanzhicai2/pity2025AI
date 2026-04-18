"""知识库容器 CRUD 路由"""
from fastapi import APIRouter, Depends

from app.crud.knowledge_lib.KnowledgeLibDao import KnowledgeLibDao
from app.routers import Permission
from app.schema.knowledge_lib_schema import (
    KnowledgeLibCreate,
    KnowledgeLibUpdate,
    KnowledgeLibResponse,
)
from app.handler.fatcory import PityResponse

kb_router = APIRouter(prefix="/rag/knowledge-bases", tags=["KnowledgeBase CRUD"])


@kb_router.post("")
async def create_knowledge_base(
    body: KnowledgeLibCreate,
    user_info: dict = Depends(Permission()),
):
    """创建知识库"""
    user_id = user_info.get("id")
    try:
        record = await KnowledgeLibDao.create_knowledge_lib(
            name=body.name,
            project_id=body.project_id,
            description=body.description,
            chunk_size=body.chunk_size,
            overlap=body.overlap,
            user_id=user_id,
        )
        return PityResponse.success(KnowledgeLibResponse.model_validate(record))
    except Exception as e:
        return PityResponse.failed(f"创建知识库失败: {e}")


@kb_router.get("")
async def list_knowledge_bases(
    project_id: int,
    user_info: dict = Depends(Permission()),
):
    """列出知识库"""
    try:
        data, total = await KnowledgeLibDao.list_knowledge_libs(project_id=project_id)
        return PityResponse.success(
            [KnowledgeLibResponse.model_validate(d) for d in data]
        )
    except Exception as e:
        return PityResponse.failed(f"查询失败: {e}")


@kb_router.get("/{lib_id}")
async def get_knowledge_base(
    lib_id: int,
    user_info: dict = Depends(Permission()),
):
    """获取知识库详情"""
    try:
        record = await KnowledgeLibDao.get_knowledge_lib(lib_id)
        if record is None:
            return PityResponse.failed("知识库不存在")
        return PityResponse.success(KnowledgeLibResponse.model_validate(record))
    except Exception as e:
        return PityResponse.failed(f"查询失败: {e}")


@kb_router.put("/{lib_id}")
async def update_knowledge_base(
    lib_id: int,
    body: KnowledgeLibUpdate,
    user_info: dict = Depends(Permission()),
):
    """更新知识库"""
    try:
        await KnowledgeLibDao.update_knowledge_lib(
            lib_id=lib_id,
            name=body.name,
            description=body.description,
            chunk_size=body.chunk_size,
            overlap=body.overlap,
        )
        return PityResponse.success(msg="更新成功")
    except Exception as e:
        return PityResponse.failed(f"更新失败: {e}")


@kb_router.delete("/{lib_id}")
async def delete_knowledge_base(
    lib_id: int,
    user_info: dict = Depends(Permission()),
):
    """删除知识库"""
    user_id = user_info.get("id")
    try:
        await KnowledgeLibDao.delete_knowledge_lib(lib_id=lib_id, user_id=user_id)
        return PityResponse.success(msg="删除成功")
    except Exception as e:
        return PityResponse.failed(f"删除失败: {e}")
