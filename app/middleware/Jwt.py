import hashlib
from datetime import timedelta, datetime

import jwt
from jwt.exceptions import ExpiredSignatureError

from config import Config

EXPIRED_HOUR = 72


class UserToken(object):
    key = 'pityToken'

    @staticmethod
    def get_token(data):
        expire = datetime.now() + timedelta(hours=EXPIRED_HOUR)
        new_data = dict({"exp": datetime.utcnow() + timedelta(hours=EXPIRED_HOUR)}, **data)
        return expire.timestamp(), jwt.encode(new_data, key=UserToken.key)

    @staticmethod
    def parse_token(token):
        try:
            return jwt.decode(token, key=UserToken.key, algorithms=["HS256"])
        except ExpiredSignatureError:
            raise Exception("登录状态已过期, 请重新登录")
        except Exception:
            raise Exception("登录状态校验失败, 请重新登录")

    @staticmethod
    def add_salt(password):
        """
        密码加盐哈希（向后兼容 MD5）
        TODO: 后续迁移到 bcrypt（需要数据库迁移脚本）
        Salt 从配置文件读取
        """
        salt = getattr(Config, 'PASSWORD_SALT', 'pity')
        m = hashlib.md5()
        bt = f"{password}{salt}".encode("utf-8")
        m.update(bt)
        return m.hexdigest()
