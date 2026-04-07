"""
需求文档路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.crud.requirement_document import RequirementDocumentDao
from app.exception.error import ParamsError
from app.handler.fatcory import PityResponse
from app.models.requirement_document import RequirementDocument
from app.routers import Permission
from app.schema.requirement_document import (
    RequirementDocumentCreateSchema,
    RequirementDocumentUpdateSchema,
)
from app.utils.logger import Log

router = APIRouter(prefix="/requirement/document", tags=["需求文档管理"])
logger = Log("requirement_document_router")


def get_current_user(user_info=Depends(Permission())):
    """获取当前用户"""
    return user_info


@router.get("")
async def list_documents(
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    doc_type: Optional[str] = Query(None, description="文档类型筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    user_info: dict = Depends(get_current_user),
):
    """获取需求文档列表"""
    if keyword:
        documents = await RequirementDocumentDao.search_by_content(keyword, project_id)
    else:
        documents = await RequirementDocumentDao.list_documents(project_id=project_id, doc_type=doc_type)
    return PityResponse.success_with_size(documents)


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    user_info: dict = Depends(get_current_user),
):
    """获取文档详情"""
    document = await RequirementDocumentDao.get_by_id(document_id=document_id)
    if not document:
        raise ParamsError("文档不存在")
    return PityResponse.success(document)


@router.post("")
async def create_document(
    data: RequirementDocumentCreateSchema,
    user_info: dict = Depends(get_current_user),
):
    """创建需求文档"""
    document = RequirementDocument(
        user=user_info['id'],
        name=data.name,
        doc_type=data.doc_type,
        project_id=data.project_id,
        file_path=data.file_path,
        file_name=data.file_name,
        content=data.content,
    )

    result = await RequirementDocumentDao.insert(model=document)
    return PityResponse.success(result)


@router.put("/{document_id}")
async def update_document(
    document_id: int,
    data: RequirementDocumentUpdateSchema,
    user_info: dict = Depends(get_current_user),
):
    """更新需求文档"""
    document = await RequirementDocumentDao.get_by_id(document_id=document_id)
    if not document:
        raise ParamsError("文档不存在")

    update_data = data.model_dump(exclude_unset=True)
    result = await RequirementDocumentDao.update_document(document_id, user_info['id'], **update_data)
    return PityResponse.success(result)


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    user_info: dict = Depends(get_current_user),
):
    """删除需求文档"""
    success = await RequirementDocumentDao.delete_document(document_id, user_info['id'])
    if not success:
        raise ParamsError("文档不存在")
    return {"code": 0, "msg": "删除成功"}
