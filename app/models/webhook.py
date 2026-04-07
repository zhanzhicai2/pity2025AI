"""
Webhook 模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, BIGINT

from app.models.basic import Base


class WebhookConfig(Base):
    """Webhook 配置"""
    __tablename__ = "webhook_config"
    __table_args__ = {'comment': 'Webhook配置表', 'mysql_charset': 'utf8mb4'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="创建者ID")
    name = Column(String(100), nullable=False, comment="Webhook名称")
    url = Column(String(500), nullable=False, comment="回调地址")
    method = Column(String(10), nullable=False, default="POST", comment="请求方法")
    headers = Column(Text, nullable=True, comment="自定义请求头JSON")
    secret = Column(String(100), nullable=True, comment="签名密钥")
    event_type = Column(String(50), nullable=False, comment="触发事件类型")
    content_type = Column(String(50), nullable=True, default="json", comment="Content-Type")
    template = Column(Text, nullable=True, comment="消息模板")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
    is_default = Column(Boolean, nullable=False, default=False, comment="是否默认配置")
    created_at = Column(BIGINT, nullable=False, default=0, comment="创建时间戳")
    updated_at = Column(BIGINT, nullable=False, default=0, comment="更新时间戳")


class NotificationHistory(Base):
    """通知发送历史"""
    __tablename__ = "notification_history"
    __table_args__ = {'comment': '通知发送历史表', 'mysql_charset': 'utf8mb4'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(Integer, nullable=False, index=True, comment="Webhook配置ID")
    title = Column(String(200), nullable=False, comment="通知标题")
    content = Column(Text, nullable=True, comment="通知内容")
    status = Column(String(20), nullable=False, default="pending", comment="发送状态: pending/success/failed")
    error_message = Column(Text, nullable=True, comment="错误信息")
    response_data = Column(Text, nullable=True, comment="响应数据")
    sent_at = Column(BIGINT, nullable=True, comment="发送时间戳")
    created_at = Column(BIGINT, nullable=False, default=0, comment="创建时间戳")


class TaskNotificationSetting(Base):
    """任务通知设置"""
    __tablename__ = "task_notification_setting"
    __table_args__ = {'comment': '任务通知设置表', 'mysql_charset': 'utf8mb4'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, nullable=False, index=True, comment="任务ID")
    task_type = Column(String(20), nullable=False, comment="任务类型: test_plan/scheduler")
    config_id = Column(Integer, nullable=False, comment="Webhook配置ID")
    is_enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
    notify_on_success = Column(Boolean, nullable=False, default=False, comment="成功时通知")
    notify_on_failure = Column(Boolean, nullable=False, default=True, comment="失败时通知")
    created_at = Column(BIGINT, nullable=False, default=0, comment="创建时间戳")
    updated_at = Column(BIGINT, nullable=False, default=0, comment="更新时间戳")
