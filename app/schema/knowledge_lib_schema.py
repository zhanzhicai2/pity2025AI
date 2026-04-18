"""KnowledgeLib Pydantic v2 Schema"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeLibCreate(BaseModel):
    name: str = Field(..., max_length=50, description="知识库名称")
    description: Optional[str] = Field(None, max_length=200, description="描述")
    chunk_size: int = Field(500, ge=100, le=2000, description="分块大小")
    overlap: int = Field(50, ge=0, le=500, description="重叠大小")
    project_id: int = Field(..., description="所属项目ID")


class KnowledgeLibUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    chunk_size: Optional[int] = Field(None, ge=100, le=2000)
    overlap: Optional[int] = Field(None, ge=0, le=500)


class KnowledgeLibResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    chunk_size: int = 500
    overlap: int = 50
    project_id: int
    document_count: int = 0
    create_user: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
