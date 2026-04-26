"""
需求文件数据模型（关联需求文档的上传文件）
"""
from sqlalchemy import Column, String, Integer, Text, Boolean

from app.models.basic import PityBase


class RequirementFile(PityBase):
    """需求文件模型 - 关联到需求文档下的具体上传文件"""
    __tablename__ = "sys_requirement_file"
    __table_args__ = {'comment': '需求文件表', 'mysql_charset': 'utf8mb4'}
    __fields__ = (PityBase.id,)
    __tag__ = "需求文件"
    __alias__ = dict(name="文件名")

    def __init__(self, user, requirement_id=None, file_name=None, file_path=None,
                 file_size=None, file_type=None, description=None, is_public=True, id=None):
        super().__init__(user, id)
        self.requirement_id = requirement_id
        self.file_name = file_name
        self.file_path = file_path
        self.file_size = file_size
        self.file_type = file_type
        self.description = description
        self.is_public = is_public
        self.download_count = 0

    # 关联需求文档 ID
    requirement_id = Column(Integer, nullable=False, comment="关联需求文档ID")

    # 原始文件名
    file_name = Column(String(255), nullable=False, comment="文件名")

    # 文件存储路径
    file_path = Column(String(500), nullable=True, comment="文件存储路径")

    # 文件大小（字节）
    file_size = Column(Integer, nullable=True, comment="文件大小(bytes)")

    # 文件类型/扩展名（如 pdf、docx、md）
    file_type = Column(String(50), nullable=True, comment="文件类型")

    # 文件描述
    description = Column(Text, nullable=True, comment="文件描述")

    # 是否公开
    is_public = Column(Boolean, default=True, comment="是否公开")

    # 下载次数
    download_count = Column(Integer, default=0, comment="下载次数")

    def __repr__(self):
        return f'<RequirementFile {self.file_name}>'
