from sqlalchemy import Column, Integer, String, Text, BigInteger, Index, UniqueConstraint
from app.models.basic import PityBase


class PityTestcaseField(PityBase):
    """用例扩展字段表（行模式，存模板自定义字段）"""
    __tablename__ = 'pity_testcase_field'

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, nullable=False, comment='用例ID（关联 pity_case_v2）')
    field_name = Column(String(64), nullable=False, comment='字段名（对应 template.field_mapping.name）')
    field_value = Column(Text, comment='字段值')

    # 索引
    __table_args__ = (
        UniqueConstraint('case_id', 'field_name', name='uk_case_field'),
        Index('idx_field_name', 'field_name'),
        Index('idx_case_id', 'case_id'),
    )

    __tag__ = "用例扩展字段"
    __fields__ = (id, case_id, field_name, field_value)

    def __init__(self, case_id, field_name, create_user, field_value=None, id=None):
        super().__init__(create_user, id)
        self.case_id = case_id
        self.field_name = field_name
        self.field_value = field_value
