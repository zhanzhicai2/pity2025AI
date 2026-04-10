"""
Phase X 测试计划模型 - 独立的测试调度体系
"""
from sqlalchemy import Column, Integer, String, Text, JSON, BigInteger, Index, Boolean
from app.models.basic import PityBase


class PityPhaseXPlan(PityBase):
    """Phase X 测试计划表"""
    __tablename__ = 'pity_phasex_plan'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基础信息
    name = Column(String(100), nullable=False, comment='计划名称')
    description = Column(Text, comment='计划描述')
    project_id = Column(Integer, nullable=False, comment='所属项目ID')

    # 执行类型
    plan_type = Column(String(16), nullable=False, comment='plan_type: single | scenario | suite')
    # single: 执行单个用例
    # scenario: 执行场景流程
    # suite: 执行测试套件

    target_id = Column(Integer, comment='目标ID（用例ID/场景ID/套件ID）')
    target_name = Column(String(100), comment='目标名称（冗余存储）')

    # 环境配置
    environment_id = Column(Integer, comment='执行环境ID')

    # 调度配置
    cron_expression = Column(String(64), comment='Cron 表达式')
    is_periodic = Column(Integer, default=0, comment='是否周期执行')

    # 执行配置
    config = Column(JSON, comment='执行配置 {retry: 0, parallel: false, ...}')

    # 状态
    is_active = Column(Integer, default=1, comment='是否启用')
    tags = Column(String(256), comment='标签')

    # 上次执行
    last_execution_id = Column(Integer, comment='上次执行记录ID')

    # 索引
    __table_args__ = (
        Index('idx_project_id', 'project_id'),
        Index('idx_plan_type', 'plan_type'),
        Index('idx_is_active', 'is_active'),
        Index('idx_is_periodic', 'is_periodic'),
    )

    __tag__ = "PhaseX测试计划"
    __fields__ = (id, name, description, project_id, plan_type, target_id, target_name,
                   environment_id, cron_expression, is_periodic, config, is_active, tags)

    def __init__(self, name, project_id, plan_type, create_user,
                 description=None, target_id=None, target_name=None,
                 environment_id=None, cron_expression=None, is_periodic=0,
                 config=None, is_active=1, tags=None, last_execution_id=None, id=None):
        super().__init__(create_user, id)
        self.name = name
        self.description = description
        self.project_id = project_id
        self.plan_type = plan_type
        self.target_id = target_id
        self.target_name = target_name
        self.environment_id = environment_id
        self.cron_expression = cron_expression
        self.is_periodic = is_periodic
        self.config = config
        self.is_active = is_active
        self.tags = tags
        self.last_execution_id = last_execution_id


class PityPhaseXExecution(PityBase):
    """Phase X 执行记录表"""
    __tablename__ = 'pity_phasex_execution'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联信息
    plan_id = Column(Integer, comment='计划ID')
    scenario_id = Column(Integer, comment='场景ID（冗余）')
    case_id = Column(Integer, comment='用例ID（冗余）')

    project_id = Column(Integer, comment='项目ID')
    environment_id = Column(Integer, comment='环境ID')

    # 执行结果
    status = Column(String(16), default='pending', comment='pending | running | passed | failed | error')
    duration_ms = Column(Integer, comment='执行耗时')
    executor = Column(String(64), comment='执行人')

    # 详细数据
    request_data = Column(JSON, comment='请求数据')
    response_data = Column(JSON, comment='响应数据')
    error_message = Column(Text, comment='错误信息')
    logs = Column(Text, comment='执行日志')

    # 步骤结果（用于场景流程）
    step_results = Column(JSON, comment='场景步骤结果')

    # 索引
    __table_args__ = (
        Index('idx_plan_id', 'plan_id'),
        Index('idx_status', 'status'),
        Index('idx_project_id', 'project_id'),
        Index('idx_created_at', 'created_at'),
    )

    __tag__ = "PhaseX执行记录"
    __fields__ = (id, plan_id, scenario_id, case_id, project_id, environment_id,
                   status, duration_ms, executor, request_data, response_data,
                   error_message, logs, step_results)

    def __init__(self, plan_id, project_id, create_user,
                 scenario_id=None, case_id=None, environment_id=None,
                 status='pending', duration_ms=None, executor=None,
                 request_data=None, response_data=None, error_message=None,
                 logs=None, step_results=None, id=None):
        super().__init__(create_user, id)
        self.plan_id = plan_id
        self.scenario_id = scenario_id
        self.case_id = case_id
        self.project_id = project_id
        self.environment_id = environment_id
        self.status = status
        self.duration_ms = duration_ms
        self.executor = executor
        self.request_data = request_data
        self.response_data = response_data
        self.error_message = error_message
        self.logs = logs
        self.step_results = step_results


class PityPhaseXReport(PityBase):
    """Phase X 测试报告表"""
    __tablename__ = 'pity_phasex_report'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 报告信息
    name = Column(String(100), nullable=False, comment='报告名称')
    project_id = Column(Integer, nullable=False, comment='项目ID')

    # 统计汇总
    total_runs = Column(Integer, default=0, comment='总执行次数')
    total_passed = Column(Integer, default=0, comment='总通过次数')
    total_failed = Column(Integer, default=0, comment='总失败次数')
    total_error = Column(Integer, default=0, comment='总错误次数')

    # 趋势数据（JSON）
    trend_data = Column(JSON, comment='趋势数据 [{date, passed, failed, error}, ...]')

    # 平均耗时
    avg_duration_ms = Column(Integer, comment='平均执行耗时')

    # 通过率
    pass_rate = Column(String(8), comment='通过率')

    # 索引
    __table_args__ = (
        Index('idx_project_id', 'project_id'),
        Index('idx_name', 'name'),
    )

    __tag__ = "PhaseX测试报告"
    __fields__ = (id, name, project_id, total_runs, total_passed,
                   total_failed, total_error, trend_data, avg_duration_ms, pass_rate)

    def __init__(self, name, project_id, create_user,
                 total_runs=0, total_passed=0, total_failed=0, total_error=0,
                 trend_data=None, avg_duration_ms=None, pass_rate=None, id=None):
        super().__init__(create_user, id)
        self.name = name
        self.project_id = project_id
        self.total_runs = total_runs
        self.total_passed = total_passed
        self.total_failed = total_failed
        self.total_error = total_error
        self.trend_data = trend_data
        self.avg_duration_ms = avg_duration_ms
        self.pass_rate = pass_rate
