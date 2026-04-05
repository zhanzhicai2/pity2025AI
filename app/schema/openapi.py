"""
OpenAPI 导入 Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class OpenAPIParseForm(BaseModel):
    """解析 OpenAPI 文档"""
    url: Optional[str] = Field(None, description="OpenAPI 文档 URL")
    content: Optional[str] = Field(None, description="OpenAPI 文档内容（JSON 格式）")


class OpenAPIGenerateForm(BaseModel):
    """生成测试用例"""
    project_id: int = Field(..., description="项目ID")
    apis: List[dict] = Field(..., description="选中的 API 列表")
    base_url: Optional[str] = Field(None, description="基础 URL")
