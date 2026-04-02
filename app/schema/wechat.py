from pydantic import BaseModel

from app.schema.base import PityModel


class WechatForm(BaseModel):
    signature: str
    timestamp: int
    nonce: str
    echostr: str
