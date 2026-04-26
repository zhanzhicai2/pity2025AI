"""
需求文件 Schema
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RequirementFileOutSchema(BaseModel):
    """需求文件输出 Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    requirement_id: int
    file_name: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    description: Optional[str] = None
    is_public: bool = True
    download_count: int = 0
    create_user: int
    created_at: Optional[str] = None
