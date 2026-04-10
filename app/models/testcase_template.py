from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, BigInteger, Index
from app.models.basic import PityBase


class PityTestcaseTemplate(PityBase):
    """测试用例模板表"""
    __tablename__ = 'pity_testcase_template'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='模板名称')
    description = Column(Text, comment='模板描述')

    # 分类维度
    test_type = Column(String(16), nullable=False, default='api', comment='测试类型: api | functional | ui')
    source = Column(String(16), nullable=False, default='manual', comment='来源: manual | ai | import | legacy')

    # 核心字段定义（JSON）
    field_mapping = Column(JSON, nullable=False, comment='字段映射配置')

    # 状态
    is_default = Column(Boolean, default=False, comment='是否默认模板')
    is_active = Column(Boolean, default=True, comment='是否启用')

    # 索引
    __table_args__ = (
        Index('idx_test_type', 'test_type'),
        Index('idx_is_active', 'is_active'),
    )

    __tag__ = "测试用例模板"
    __fields__ = (id, name, description, test_type, source, field_mapping, is_default, is_active)

    def __init__(self, name, test_type, field_mapping, create_user,
                 description=None, source='manual', is_default=False, is_active=True, id=None):
        super().__init__(create_user, id)
        self.name = name
        self.description = description
        self.test_type = test_type
        self.source = source
        self.field_mapping = field_mapping
        self.is_default = is_default
        self.is_active = is_active
