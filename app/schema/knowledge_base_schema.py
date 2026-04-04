"""
KnowledgeBase Pydantic Schema
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    file_type: str
    file_path: str
    file_size: Optional[int] = None
    content_hash: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = {}
    status: str
    chunk_count: int
    error_msg: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    create_user: Optional[int] = None


class KnowledgeBaseCreate(BaseModel):
    name: str
    file_type: str
    file_path: str
    file_size: Optional[int] = None
    content_hash: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = {}
    status: str = "pending"
    chunk_count: int = 0


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    chunk_count: Optional[int] = None
    error_msg: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    file_type: str
    file_size: Optional[int] = None
    status: str
    chunk_count: int
    created_at: Optional[datetime] = None
    create_user: Optional[int] = None


class RetrievalResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    distance: Optional[float] = None


class RetrievalResponse(BaseModel):
    query: str
    results: List[RetrievalResult]
    count: int
