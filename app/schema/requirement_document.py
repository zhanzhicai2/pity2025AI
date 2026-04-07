"""
需求文档 Schema
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RequirementDocumentBaseSchema(BaseModel):
    """基础 Schema"""
    name: str = Field(..., description="文档名称")
    doc_type: str = Field(..., description="文档类型")
    project_id: Optional[int] = Field(None, description="关联项目ID")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_name: Optional[str] = Field(None, description="文件名")
    content: Optional[str] = Field(None, description="文档内容")


class RequirementDocumentCreateSchema(RequirementDocumentBaseSchema):
    """创建文档 Schema"""
    pass


class RequirementDocumentUpdateSchema(BaseModel):
    """更新文档 Schema"""
    name: Optional[str] = Field(None, description="文档名称")
    doc_type: Optional[str] = Field(None, description="文档类型")
    project_id: Optional[int] = Field(None, description="关联项目ID")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_name: Optional[str] = Field(None, description="文件名")
    content: Optional[str] = Field(None, description="文档内容")


class RequirementDocumentOutSchema(RequirementDocumentBaseSchema):
    """输出 Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    create_user: int
    created_at: str
    updated_at: str
    update_user: Optional[int] = None


class RequirementDocumentQuerySchema(BaseModel):
    """查询 Schema"""
    project_id: Optional[int] = Field(None, description="项目ID筛选")
    doc_type: Optional[str] = Field(None, description="文档类型筛选")
    keyword: Optional[str] = Field(None, description="关键词搜索")
