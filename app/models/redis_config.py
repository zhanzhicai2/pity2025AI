from sqlalchemy import Column, INT, String, Boolean, UniqueConstraint

from app.models.basic import PityBase


class PityRedis(PityBase):
    __tablename__ = "pity_redis_info"
    __table_args__ = (
        UniqueConstraint('env', 'name', 'deleted_at'),
    )

    env = Column(INT, nullable=False, comment='对应环境ID')
    name = Column(String(24), nullable=False, comment='Redis描述名称')
    addr = Column(String(128), nullable=False, comment='Redis连接地址')
    username = Column(String(36), nullable=False, comment='用户名')
    password = Column(String(64), nullable=False, comment='密码')
    db = Column(INT, nullable=False, comment='数据库编号')
    cluster = Column(Boolean, default=False, nullable=False, comment='是否为集群模式')

    __tag__ = "Redis配置"
    __fields__ = (name, env, addr, username, password, db, cluster)
    __alias__ = dict(name="连接名称", env="环境", addr="连接地址", username="用户名",
                     password="用户密码", db="库号", cluster="集群")

    def __init__(self, env, name, addr, cluster, user, username='', password='', db=0, id=None):
        super().__init__(user, id=id)
        self.env = env
        self.name = name
        self.addr = addr
        self.password = password
        self.username = username
        self.db = db
        self.cluster = cluster
