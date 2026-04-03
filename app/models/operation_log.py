from datetime import datetime

from sqlalchemy import Column, String, INT, TIMESTAMP, UniqueConstraint, TEXT, SMALLINT

from app.enums.OperationEnum import OperationType
from app.models import Base


class PityOperationLog(Base):
    """用户操作记录表"""
    __tablename__ = 'pity_operation_log'

    id = Column(INT, primary_key=True, comment='主键ID')
    user_id = Column(INT, index=True, comment='操作人ID')
    operate_time = Column(TIMESTAMP, comment='操作时间')
    title = Column(String(128), nullable=False, comment='操作标题')
    description = Column(TEXT, comment='操作描述')
    tag = Column(String(24), comment='操作标签')
    mode = Column(SMALLINT, comment='操作类型')
    key = Column(INT, nullable=True, comment='关键ID(目录ID/用例ID等)')

    def __init__(self, user_id, mode: OperationType, title, tag, description, key=None):
        self.user_id = user_id
        self.tag = tag
        self.mode = mode.value
        self.title = title
        self.key = key
        self.description = description
        self.operate_time = datetime.now()
