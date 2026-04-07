from sqlalchemy import Column, String, INT, UniqueConstraint

from app.models.basic import PityBase


class PityTestCaseOutParameters(PityBase):
    """用例出参数据，与用例绑定"""
    __tablename__ = 'pity_out_parameters'
    __table_args__ = (
        {'comment': '用例出参表', 'mysql_charset': 'utf8mb4'},
        UniqueConstraint('case_id', 'name', 'deleted_at'),
    )

    case_id = Column(INT, nullable=False, comment='用例ID')
    name = Column(String(24), nullable=False, comment='参数名')
    source = Column(INT, nullable=False, default=0, comment="0: Body(TEXT) 1: Body(JSON) 2: Header 3: Cookie 4: HTTP状态码")
    expression = Column(String(128), comment='提取表达式')
    match_index = Column(String(16), comment='获取结果索引')

    def __init__(self, name, source, case_id, user_id, expression=None, match_index=None, id=None):
        super().__init__(user_id, id)
        self.name = name
        self.case_id = case_id
        self.expression = expression
        self.match_index = match_index
        self.source = source
