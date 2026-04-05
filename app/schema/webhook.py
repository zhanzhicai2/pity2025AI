"""
Webhook Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class WebhookConfigForm(BaseModel):
    """创建/更新 Webhook 配置"""
    name: str = Field(..., description="Webhook名称")
    url: str = Field(..., description="回调地址")
    method: str = Field(default="POST", description="请求方法")
    headers: Optional[str] = Field(None, description="自定义请求头JSON字符串")
    secret: Optional[str] = Field(None, description="签名密钥")
    event_type: str = Field(..., description="触发事件类型")
    content_type: Optional[str] = Field(default="json", description="Content-Type")
    template: Optional[str] = Field(None, description="消息模板")
    enabled: bool = Field(default=True, description="是否启用")
    is_default: bool = Field(default=False, description="是否默认配置")


class WebhookTestForm(BaseModel):
    """测试 Webhook"""
    url: str = Field(..., description="回调地址")
    method: str = Field(default="POST", description="请求方法")
    headers: Optional[str] = Field(None, description="自定义请求头JSON字符串")
    secret: Optional[str] = Field(None, description="签名密钥")
    content_type: Optional[str] = Field(default="json", description="Content-Type")
    body: Optional[str] = Field(None, description="测试消息体")


class TaskNotificationSettingForm(BaseModel):
    """任务通知设置"""
    task_id: int = Field(..., description="任务ID")
    task_type: str = Field(..., description="任务类型: test_plan/scheduler")
    config_id: int = Field(..., description="Webhook配置ID")
    is_enabled: bool = Field(default=True, description="是否启用")
    notify_on_success: bool = Field(default=False, description="成功时通知")
    notify_on_failure: bool = Field(default=True, description="失败时通知")


class NotificationHistoryQuery(BaseModel):
    """通知历史查询"""
    config_id: Optional[int] = Field(None, description="Webhook配置ID")
    status: Optional[str] = Field(None, description="发送状态")
    days: int = Field(default=7, ge=1, le=30, description="最近天数")
