"""
场景流程模型 - 用例串联和参数传递
"""
from sqlalchemy import Column, Integer, String, Text, JSON, BigInteger, Index, ForeignKey
from app.models.basic import PityBase


class PityScenario(PityBase):
    """场景流程主表"""
    __tablename__ = 'pity_scenario'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基础信息
    name = Column(String(100), nullable=False, comment='场景名称')
    description = Column(Text, comment='场景描述')
    project_id = Column(Integer, nullable=False, comment='所属项目ID')

    # 场景配置
    case_type = Column(String(16), nullable=False, comment='用例类型: api | functional | ui')
    source = Column(String(16), default='manual', comment='来源: manual | ai | import')

    # 全局变量（JSON）- 场景级别的上下文变量
    variables = Column(JSON, comment='全局变量 {key: value}')

    # 配置项
    is_active = Column(Integer, default=1, comment='是否启用')
    tags = Column(String(256), comment='标签')

    # 审计字段（复用 PityBase）
    __table_args__ = (
        Index('idx_project_id', 'project_id'),
        Index('idx_case_type', 'case_type'),
        Index('idx_is_active', 'is_active'),
    )

    __tag__ = "场景流程"
    __fields__ = (id, name, description, project_id, case_type, source, variables, is_active, tags)

    def __init__(self, name, project_id, case_type, create_user,
                 description=None, source='manual', variables=None,
                 is_active=1, tags=None, id=None):
        super().__init__(create_user, id)
        self.name = name
        self.description = description
        self.project_id = project_id
        self.case_type = case_type
        self.source = source
        self.variables = variables
        self.is_active = is_active
        self.tags = tags


class PityScenarioStep(PityBase):
    """场景步骤表 - 关联用例和参数传递"""
    __tablename__ = 'pity_scenario_step'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联信息
    scenario_id = Column(Integer, nullable=False, comment='场景ID')
    case_id = Column(Integer, nullable=False, comment='用例ID')

    # 步骤顺序
    step_order = Column(Integer, nullable=False, comment='步骤顺序')
    step_name = Column(String(100), comment='步骤名称（可自定义）')

    # 参数传递配置
    # input_mapping: 上一步的输出如何注入到当前步骤
    # 格式: [{"from_step": 1, "from_var": "token", "to_field": "headers.authorization"}]
    input_mapping = Column(JSON, comment='输入参数映射')

    # output_mapping: 当前步骤的输出如何传递给下一步
    # 格式: [{"var_name": "token", "extract_path": "$.data.token"}]
    output_mapping = Column(JSON, comment='输出参数映射')

    # 条件执行
    condition = Column(String(256), comment='执行条件（如: status == 200）')
    condition_field = Column(String(64), comment='条件字段（如: status）')

    # 超时配置
    timeout_ms = Column(Integer, default=30000, comment='超时时间（毫秒）')

    # 重试配置
    retry_count = Column(Integer, default=0, comment='失败重试次数')
    retry_interval_ms = Column(Integer, default=1000, comment='重试间隔（毫秒）')

    # 索引
    __table_args__ = (
        Index('idx_scenario_id', 'scenario_id'),
        Index('idx_case_id', 'case_id'),
        Index('idx_scenario_order', 'scenario_id', 'step_order'),
    )

    __tag__ = "场景步骤"
    __fields__ = (id, scenario_id, case_id, step_order, step_name, input_mapping,
                   output_mapping, condition, condition_field, timeout_ms, retry_count, retry_interval_ms)

    def __init__(self, scenario_id, case_id, step_order, create_user,
                 step_name=None, input_mapping=None, output_mapping=None,
                 condition=None, condition_field=None, timeout_ms=30000,
                 retry_count=0, retry_interval_ms=1000, id=None):
        super().__init__(create_user, id)
        self.scenario_id = scenario_id
        self.case_id = case_id
        self.step_order = step_order
        self.step_name = step_name
        self.input_mapping = input_mapping
        self.output_mapping = output_mapping
        self.condition = condition
        self.condition_field = condition_field
        self.timeout_ms = timeout_ms
        self.retry_count = retry_count
        self.retry_interval_ms = retry_interval_ms
