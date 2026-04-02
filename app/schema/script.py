from pydantic import BaseModel, field_validator

from app.schema.base import PityModel


class PyScriptForm(BaseModel):
    command: str
    value: str

    @field_validator("command")
    def name_not_empty(cls, v):
        return PityModel.not_empty(v)
