from pydantic import field_validator, BaseModel

from app.schema.base import PityModel


class DatabaseForm(BaseModel):
    id: int = None
    name: str
    host: str
    port: int = None
    username: str
    password: str
    database: str
    sql_type: int
    env: int

    @field_validator("name", "host", "port", "username", "password", "database", "sql_type", "env")
    def data_not_empty(cls, v):
        return PityModel.not_empty(v)
