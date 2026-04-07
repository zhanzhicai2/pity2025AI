"""
需求文档数据模型
"""
from sqlalchemy import Column, String, Integer, Text

from app.models.basic import PityBase


class RequirementDocument(PityBase):
    """需求文档模型"""
    __tablename__ = "sys_requirement_document"
    __table_args__ = {'comment': '需求文档表', 'mysql_charset': 'utf8mb4'}
    __fields__ = (id,)
    __tag__ = "需求文档"
    __alias__ = dict(name="文档名称")

    def __init__(self, user, name=None, doc_type=None, project_id=None,
                 file_path=None, file_name=None, content=None, id=None):
        super().__init__(user, id)
        self.name = name
        self.doc_type = doc_type
        self.project_id = project_id
        self.file_path = file_path
        self.file_name = file_name
        self.content = content

    # 文档名称
    name = Column(String(255), nullable=False, comment="文档名称")

    # 文档类型：prd/需求文档/设计文档/其他
    doc_type = Column(String(50), nullable=False, comment="文档类型")

    # 关联项目ID
    project_id = Column(Integer, nullable=True, comment="关联项目ID")

    # 文件路径
    file_path = Column(String(500), nullable=True, comment="文件路径")

    # 文件名
    file_name = Column(String(255), nullable=True, comment="文件名")

    # 文档内容（提取的文本）
    content = Column(Text, nullable=True, comment="文档内容")

    def __repr__(self):
        return f'<RequirementDocument {self.name}>'
