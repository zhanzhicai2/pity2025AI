from typing import Optional

from pydantic import BaseModel, field_validator, ConfigDict

# 都可以为空，为空则不进行更改
from app.exception.error import ParamsError
from app.schema.base import PityModel


class UserUpdateForm(BaseModel):
    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[int] = None
    is_valid: Optional[bool] = None

    @field_validator('id')
    def id_not_empty(cls, v):
        return PityModel.not_empty(v)


class UserDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    password: str
    username: str
    email: str

    @field_validator('name', 'password', 'username', 'email')
    def field_not_empty(cls, v):
        if isinstance(v, str) and len(v.strip()) == 0:
            raise ParamsError("不能为空")
        return v


class UserForm(BaseModel):
    username: str
    password: str

    @field_validator('password', 'username')
    def name_not_empty(cls, v):
        if isinstance(v, str) and len(v.strip()) == 0:
            raise ParamsError("不能为空")
        return v


class ResetPwdForm(BaseModel):
    password: str
    token: str

    @field_validator('token', 'password')
    def name_not_empty(cls, v):
        if isinstance(v, str) and len(v.strip()) == 0:
            raise ParamsError("不能为空")
        return v
