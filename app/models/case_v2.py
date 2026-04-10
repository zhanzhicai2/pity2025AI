from sqlalchemy import Column, Integer, String, Text, BigInteger, Index, ForeignKey
from app.models.basic import PityBase


class PityCaseV2(PityBase):
    """测试用例主表（动态模板版本）"""
    __tablename__ = 'pity_case_v2'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基础信息
    name = Column(String(100), nullable=False, comment='用例名称')
    case_no = Column(String(64), comment='用例编号')
    priority = Column(String(3), default='P2', comment='P0/P1/P2/P3/P4')
    status = Column(Integer, default=1, comment='状态')
    directory_id = Column(Integer, comment='所属目录')
    tag = Column(String(256), comment='标签')

    # 模板系统核心
    template_id = Column(Integer, nullable=False, comment='关联模板ID')
    case_type = Column(String(16), nullable=False, comment='api | functional | ui')
    source = Column(String(16), default='manual', comment='manual | ai | import | legacy')

    # 测试内容（通用字段）
    preconditions = Column(Text, comment='前置条件')
    expected_result = Column(Text, comment='预期结果')
    test_steps = Column(Text, comment='测试步骤')

    # AI 生成信息
    ai_model = Column(String(64), comment='AI生成模型')
    ai_prompt = Column(Text, comment='原始提示词')
    ai_generated_at = Column(BigInteger, comment='AI生成时间戳')
    parent_task_id = Column(Integer, comment='改写自生成任务ID')
    parent_case_id = Column(Integer, comment='改写自用例ID')

    # 索引
    __table_args__ = (
        Index('idx_template_source_type', 'template_id', 'source', 'case_type'),
        Index('idx_directory_status_priority', 'directory_id', 'status', 'priority'),
        Index('idx_case_type', 'case_type'),
        Index('idx_case_no', 'case_no'),
        Index('idx_ai_task', 'parent_task_id'),
        Index('idx_source', 'source'),
    )

    __tag__ = "测试用例V2"
    __fields__ = (id, name, case_no, priority, status, directory_id, tag, template_id, case_type, source, preconditions, expected_result, test_steps)

    def __init__(self, name, template_id, case_type, create_user,
                 case_no=None, priority='P2', status=1, directory_id=None, tag=None,
                 source='manual', preconditions=None, expected_result=None, test_steps=None,
                 ai_model=None, ai_prompt=None, ai_generated_at=None,
                 parent_task_id=None, parent_case_id=None, id=None):
        super().__init__(create_user, id)
        self.name = name
        self.case_no = case_no
        self.priority = priority
        self.status = status
        self.directory_id = directory_id
        self.tag = tag
        self.template_id = template_id
        self.case_type = case_type
        self.source = source
        self.preconditions = preconditions
        self.expected_result = expected_result
        self.test_steps = test_steps
        self.ai_model = ai_model
        self.ai_prompt = ai_prompt
        self.ai_generated_at = ai_generated_at
        self.parent_task_id = parent_task_id
        self.parent_case_id = parent_case_id
