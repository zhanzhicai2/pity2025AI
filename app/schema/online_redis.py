from pydantic import BaseModel, field_validator

from app.schema.base import PityModel


class OnlineRedisForm(BaseModel):
    id: int = None
    command: str

    @field_validator("command", 'id')
    def name_not_empty(cls, v):
        return PityModel.not_empty(v)
