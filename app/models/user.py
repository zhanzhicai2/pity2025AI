from datetime import datetime

from sqlalchemy import Column, String, INT, TIMESTAMP, Boolean, BIGINT

from app.models import Base


class User(Base):
    __tablename__ = "pity_user"

    id = Column(INT, primary_key=True, comment='主键ID')
    username = Column(String(16), unique=True, index=True, comment='用户名')
    name = Column(String(16), index=True, comment='姓名')
    password = Column(String(32), unique=False, comment='密码哈希')
    email = Column(String(64), unique=True, nullable=False, comment='邮箱')
    role = Column(INT, default=0, comment="0: 普通用户 1: 组长 2: 超级管理员")
    phone = Column(String(12), unique=True, comment='手机号')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.now(), comment='更新时间')
    deleted_at = Column(BIGINT, nullable=False, default=0, comment='删除时间戳')
    update_user = Column(INT, nullable=True, comment='更新人ID')
    last_login_at = Column(TIMESTAMP, comment='最后登录时间')
    avatar = Column(String(128), nullable=True, default=None, comment='头像URL')
    is_valid = Column(Boolean, nullable=False, default=True, comment="是否合法")

    def __init__(self, username, name, password, email, avatar=None, phone=None, is_valid=True):
        self.username = username
        self.password = password
        self.email = email
        self.name = name
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.role = 0
        self.phone = phone
        self.avatar = avatar
        self.is_valid = is_valid
        self.deleted_at = 0
