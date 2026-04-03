from sqlalchemy import INT, Column, String, UniqueConstraint

from app.models.basic import PityBase
from app.models.environment import Environment


class PityDatabase(PityBase):
    __tablename__ = "pity_database_info"
    __table_args__ = (
        UniqueConstraint('env', 'name', 'deleted_at'),
    )

    env = Column(INT, nullable=False, comment='对应环境ID')
    name = Column(String(24), nullable=False, comment='数据库描述名称')
    host = Column(String(64), nullable=False, comment='数据库主机地址')
    port = Column(INT, nullable=False, comment='数据库端口')
    username = Column(String(36), nullable=False, comment='用户名')
    password = Column(String(64), nullable=False, comment='密码')
    database = Column(String(36), nullable=False, comment='数据库名')
    sql_type = Column(INT, nullable=False, comment="0: mysql 1: postgresql 2: mongo")
    env_info: Environment

    def __init__(self, env, name, host, port, username, password, database, sql_type, user, id=None):
        super().__init__(user, id)
        self.env = env
        self.name = name
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.sql_type = sql_type
