from typing import Optional
from pydantic import BaseModel, Field


class CaseFieldSchema(BaseModel):
    """扩展字段 Schema"""
    id: Optional[int] = Field(None, description='字段ID')
    case_id: int = Field(..., description='用例ID')
    field_name: str = Field(..., description='字段名')
    field_value: Optional[str] = Field(None, description='字段值')
