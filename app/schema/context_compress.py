"""
上下文压缩 Schema
"""
from typing import List, Optional, Any
from pydantic import BaseModel, Field


class CompressionRequest(BaseModel):
    """压缩请求"""
    query: str = Field(..., description="用户查询")
    documents: List[dict] = Field(..., description="要压缩的文档列表")
    max_context_length: int = Field(4000, description="最大上下文长度")
    compression_level: str = Field("auto", description="压缩级别: auto, paragraph, sentence")


class CompressedChunk(BaseModel):
    """压缩后的文档块"""
    content: str
    relevance_score: float
    original_index: int
    source: Optional[str] = None


class CompressionResponse(BaseModel):
    """压缩响应"""
    compressed_chunks: List[CompressedChunk]
    summary: str
    original_count: int
    compressed_count: int
