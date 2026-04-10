from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class MockRuleSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[int] = Field(None, description='规则ID（更新时必填）')
    name: str = Field(..., description='规则名称')
    project_id: int = Field(..., description='关联项目ID')
    url_pattern: str = Field(..., description='URL 正则匹配')
    method: str = Field(..., description='请求方法')
    description: Optional[str] = Field(None, description='描述')
    response_status: int = Field(default=200, description='HTTP 状态码')
    response_body: str = Field(default="", description='响应体')
    response_headers: Optional[str] = Field(default="{}", description='响应头 JSON')
    response_delay: int = Field(default=0, description='延迟 ms')
    request_headers: Optional[str] = Field(default="{}", description='请求头条件 JSON')
    request_body_pattern: Optional[str] = Field(None, description='请求体正则')
    is_active: bool = Field(default=True, description='是否启用')
