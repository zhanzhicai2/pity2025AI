from datetime import datetime

from sqlalchemy import INT, Column, TIMESTAMP, String, BIGINT
from sqlalchemy.dialects.mysql import SMALLINT

from app.models import Base


class PityReport(Base):
    __tablename__ = 'pity_report'
    __table_args__ = {'comment': '测试报告表', 'mysql_charset': 'utf8mb4'}

    id = Column(INT, primary_key=True, comment='主键ID')
    executor = Column(INT, index=True, comment='执行人ID，0为系统')
    env = Column(INT, nullable=False, comment='执行环境ID')
    cost = Column(String(8), comment='花费时间(ms)')
    plan_id = Column(INT, index=True, nullable=True, comment='测试集合ID')
    start_at = Column(TIMESTAMP, nullable=False, comment='开始时间')
    finished_at = Column(TIMESTAMP, comment='结束时间')
    success_count = Column(INT, nullable=False, default=0, comment='成功数量')
    error_count = Column(INT, nullable=False, default=0, comment='错误数量')
    failed_count = Column(INT, nullable=False, default=0, comment='失败数量')
    skipped_count = Column(INT, nullable=False, default=0, comment='跳过数量')
    status = Column(SMALLINT, nullable=False, comment="0: pending 1: running 2: stopped 3: finished", index=True)
    mode = Column(SMALLINT, default=0, comment="0: 普通 1: 测试集 2: pipeline 3: 其他")
    deleted_at = Column(BIGINT, nullable=False, default=0, comment='删除时间戳')

    def __init__(self, executor: int, env: int, success_count: int = 0, failed_count: int = 0,
                 error_count: int = 0, skipped_count: int = 0, status: int = 0, mode: int = 0,
                 plan_id: int = None, finished_at: datetime = None, cost=None):
        self.executor = executor
        self.env = env
        self.start_at = datetime.now()
        self.success_count = success_count
        self.cost = cost
        self.failed_count = failed_count
        self.error_count = error_count
        self.skipped_count = skipped_count
        self.mode = mode
        self.status = status
        self.plan_id = plan_id
        self.finished_at = finished_at
        self.deleted_at = 0
