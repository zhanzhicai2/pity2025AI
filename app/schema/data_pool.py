from datetime import datetime
from typing import Any, Optional, List

from pydantic import BaseModel, field_validator

from app.schema.base import PityModel


class DataPoolRecordForm(BaseModel):
    id: int = None
    tool_name: str
    tool_category: str
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    tags: Optional[List[str]] = None
    is_favorite: bool = False

    @field_validator("tool_name", "tool_category")
    def name_not_empty(cls, v):
        return PityModel.not_empty(v)


class DataPoolGenerateForm(BaseModel):
    tool_name: str
    params: Optional[dict] = None


class DataPoolBatchGenerateForm(BaseModel):
    tool_name: str
    count: int = 10
    params: Optional[dict] = None


class DataPoolFavoriteForm(BaseModel):
    id: int
    is_favorite: bool
