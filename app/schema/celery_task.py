"""
Celery 任务状态 Schema
"""
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class TaskResultRequest(BaseModel):
    """任务结果请求"""
    task_id: str


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AsyncGenerateRequest(BaseModel):
    """异步生成请求"""
    content: str
    input_type: str = "text"  # text/curl/openapi
    directory_id: int
    model: Optional[str] = None
    priority: str = "P2"
    status: int = 1

    class Config:
        json_schema_extra = {
            "example": {
                "content": "用户登录接口：POST /api/user/login",
                "input_type": "text",
                "directory_id": 1,
                "priority": "P2",
                "status": 1,
            }
        }


class AsyncEnhanceRequest(BaseModel):
    """异步增强断言请求"""
    case_id: int
    response_sample: str
    model: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "case_id": 1,
                "response_sample": '{"code": 0, "data": {"token": "xxx"}}',
            }
        }


class AsyncBatchGenerateRequest(BaseModel):
    """异步批量生成请求"""
    openapi_spec: str
    directory_id: int
    max_cases: int = 20
    model: Optional[str] = None
    priority: str = "P2"
    status: int = 1

    class Config:
        json_schema_extra = {
            "example": {
                "openapi_spec": '{"paths": {"/api/user": {"post": {"summary": "用户登录"}}}}',
                "directory_id": 1,
                "max_cases": 20,
            }
        }


class AsyncTaskResponse(BaseModel):
    """异步任务响应"""
    task_id: str
    status: str
    message: str
