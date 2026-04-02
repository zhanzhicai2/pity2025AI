from pydantic import field_validator, BaseModel

from app.schema.base import PityModel


class RedisConfigForm(BaseModel):
    id: int = None
    name: str
    addr: str
    db: int = 0
    # username: str = ''
    password: str = ''
    cluster: bool = False
    env: int

    @field_validator("name", "addr", "cluster", "db", "env")
    def data_not_empty(cls, v):
        return PityModel.not_empty(v)
