"""知识库容器模型"""
from sqlalchemy import Column, Integer, String, Text

from app.models.basic import PityBase


class KnowledgeLib(PityBase):
    """知识库（容器）"""
    __tablename__ = "pity_knowledge_lib"
    __table_args__ = {'comment': '知识库容器表', 'mysql_charset': 'utf8mb4'}

    name = Column(String(255), nullable=False, comment="知识库名称")
    description = Column(Text, nullable=True, comment="知识库描述")
    chunk_size = Column(Integer, default=500, comment="分块大小")
    overlap = Column(Integer, default=50, comment="重叠大小")
    project_id = Column(Integer, nullable=False, comment="所属项目ID")
    document_count = Column(Integer, default=0, comment="文档数量")
