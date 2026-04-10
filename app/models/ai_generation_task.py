from sqlalchemy import Column, Integer, String, Text, BigInteger, JSON, Index
from app.models.basic import PityBase


class PityAIGenerationTask(PityBase):
    """AI 生成任务表"""
    __tablename__ = 'pity_ai_generation_task'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment='任务名称')
    project_id = Column(Integer, nullable=False, comment='所属项目ID')
    template_id = Column(Integer, nullable=False, comment='关联模板ID')
    case_type = Column(String(16), nullable=False, comment='用例类型')

    # 用户输入
    requirement = Column(Text, nullable=False, comment='用户需求描述')
    source = Column(String(16), default='ai', comment='来源')

    # AI 解析结果
    modules = Column(JSON, comment='AI 解析出的模块列表')
    module_count = Column(Integer, comment='模块数量')

    # 执行状态
    status = Column(String(16), default='pending', comment='pending | parsing | generating | completed | failed')
    total_cases = Column(Integer, comment='计划生成用例数')
    generated_cases = Column(Integer, comment='实际生成用例数')
    progress = Column(Integer, default=0, comment='进度百分比')

    # AI 模型信息
    ai_model = Column(String(64), comment='AI模型')
    prompt_tokens = Column(Integer, comment='输入Token消耗')
    completion_tokens = Column(Integer, comment='输出Token消耗')

    # 索引
    __table_args__ = (
        Index('idx_project_id', 'project_id'),
        Index('idx_status', 'status'),
        Index('idx_create_user', 'create_user'),
    )

    __tag__ = "AI生成任务"
    __fields__ = (id, name, project_id, template_id, case_type, requirement, source, status, total_cases, generated_cases, progress, ai_model)

    def __init__(self, name, project_id, template_id, case_type, requirement, create_user,
                 source='ai', modules=None, module_count=None,
                 status='pending', total_cases=None, generated_cases=None, progress=0,
                 ai_model=None, prompt_tokens=None, completion_tokens=None, id=None):
        super().__init__(create_user, id)
        self.name = name
        self.project_id = project_id
        self.template_id = template_id
        self.case_type = case_type
        self.requirement = requirement
        self.source = source
        self.modules = modules
        self.module_count = module_count
        self.status = status
        self.total_cases = total_cases
        self.generated_cases = generated_cases
        self.progress = progress
        self.ai_model = ai_model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
