"""
测试数据表, 用来存储各个环境下的测试数据，用于数据驱动
Create Date:
"""
__author__ = "miluo"

from sqlalchemy import Column, INT, String, UniqueConstraint, TEXT

from app.models.basic import PityBase


class PityTestcaseData(PityBase):
    env = Column(INT, nullable=False, comment='环境ID')
    case_id = Column(INT, nullable=False, comment='用例ID')
    name = Column(String(32), nullable=False, comment='数据名称')
    json_data = Column(TEXT, nullable=False, comment='测试数据JSON')

    __table_args__ = (
        {'comment': '测试数据表', 'mysql_charset': 'utf8mb4'},
        UniqueConstraint('env', 'case_id', 'name', 'deleted_at'),
    )

    __tablename__ = "pity_testcase_data"

    __fields__ = [name]
    __show__ = 1

    def __init__(self, env, case_id, name, json_data, user_id, id=None):
        super().__init__(user_id, id)
        self.env = env
        self.case_id = case_id
        self.name = name
        self.json_data = json_data
