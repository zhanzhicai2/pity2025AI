from sqlalchemy import Column, Integer, String, Text, BigInteger, JSON, Index
from app.models.basic import PityBase


class PityCaseExecution(PityBase):
    """用例执行记录表"""
    __tablename__ = 'pity_case_execution'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联信息
    case_id = Column(Integer, nullable=False, comment='用例ID（关联 pity_case_v2）')
    template_id = Column(Integer, comment='关联模板ID')
    case_type = Column(String(16), nullable=False, comment='api | functional | ui')
    suite_id = Column(Integer, comment='关联测试套件ID')

    # 执行结果
    status = Column(String(16), nullable=False, default='pending', comment='pending | running | passed | failed | error')
    duration_ms = Column(Integer, comment='执行耗时（毫秒）')
    executor = Column(String(64), comment='执行人')
    executed_at = Column(BigInteger, comment='执行时间戳')

    # 详细数据
    request_data = Column(JSON, comment='请求数据')
    response_data = Column(JSON, comment='响应数据')
    actual_result = Column(Text, comment='实际结果')
    expected_result = Column(Text, comment='预期结果')
    error_message = Column(Text, comment='错误信息')
    screenshots = Column(JSON, comment='截图路径列表')
    logs = Column(Text, comment='执行日志')

    # 索引
    __table_args__ = (
        Index('idx_case_id', 'case_id'),
        Index('idx_status', 'status'),
        Index('idx_executed_at', 'executed_at'),
        Index('idx_case_type', 'case_type'),
        Index('idx_template_id', 'template_id'),
    )

    __tag__ = "用例执行记录"
    __fields__ = (id, case_id, template_id, case_type, suite_id, status, duration_ms, executor, executed_at, actual_result, expected_result, error_message)

    def __init__(self, case_id, case_type, status, create_user,
                 template_id=None, suite_id=None, duration_ms=None, executor=None, executed_at=None,
                 request_data=None, response_data=None, actual_result=None, expected_result=None,
                 error_message=None, screenshots=None, logs=None, id=None):
        super().__init__(create_user, id)
        self.case_id = case_id
        self.template_id = template_id
        self.case_type = case_type
        self.suite_id = suite_id
        self.status = status
        self.duration_ms = duration_ms
        self.executor = executor
        self.executed_at = executed_at
        self.request_data = request_data
        self.response_data = response_data
        self.actual_result = actual_result
        self.expected_result = expected_result
        self.error_message = error_message
        self.screenshots = screenshots
        self.logs = logs
