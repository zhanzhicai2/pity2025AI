from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime
from sqlalchemy.sql import func

from app.models.basic import Base


class DataPoolRecord(Base):
    """数据池记录"""
    __tablename__ = "data_pool_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    tool_name = Column(String(100), nullable=False, index=True, comment="工具名称")
    tool_category = Column(String(50), nullable=False, index=True, comment="工具分类")
    input_data = Column(JSON, nullable=True, comment="输入参数")
    output_data = Column(JSON, nullable=True, comment="输出数据")
    tags = Column(JSON, nullable=True, comment="标签")
    is_favorite = Column(Boolean, default=False, comment="是否收藏")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    update_user = Column(Integer, nullable=True, comment="更新人")
