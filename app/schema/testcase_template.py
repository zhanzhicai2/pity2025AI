from typing import Optional, List, Any
from pydantic import BaseModel, Field


class TestcaseTemplateSchema(BaseModel):
    """模板 Schema"""
    id: Optional[int] = Field(None, description='模板ID')
    name: str = Field(..., description='模板名称')
    description: Optional[str] = Field(None, description='模板描述')
    test_type: str = Field(default='api', description='测试类型: api | functional | ui')
    source: str = Field(default='manual', description='来源: manual | ai | import | legacy')
    field_mapping: Any = Field(..., description='字段映射配置')
    is_default: bool = Field(default=False, description='是否默认模板')
    is_active: bool = Field(default=True, description='是否启用')
