from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from app.models import Base


class KnowledgeBase(Base):
    """知识库文档"""
    __tablename__ = "knowledge_base"
    __table_args__ = {'comment': '知识库文档表', 'mysql_charset': 'utf8mb4'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="文档名称")
    file_type = Column(String(50), nullable=False, comment="文件类型: pdf, docx, md, txt")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_size = Column(Integer, comment="文件大小(字节)")
    content_hash = Column(String(64), comment="内容哈希，用于去重")
    doc_metadata = Column(JSON, default={}, comment="元数据: 作者, 上传时间等")

    # 状态
    status = Column(String(20), default="pending", comment="状态: pending, processing, ready, error")
    chunk_count = Column(Integer, default=0, comment="切分后的块数")
    error_msg = Column(Text, nullable=True, comment="错误信息")

    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    create_user = Column(Integer, nullable=True, comment="创建人ID")
