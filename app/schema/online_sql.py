from typing import Optional

from pydantic import BaseModel, field_validator

from app.schema.base import PityModel


class OnlineSQLForm(BaseModel):
    id: Optional[int] = None
    sql: str

    @field_validator("sql", 'id')
    def name_not_empty(cls, v):
        return PityModel.not_empty(v)
