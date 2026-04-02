from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, field_validator


class ExecutionMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


# ==================== TestSuite ====================

class TestSuiteBase(BaseModel):
    name: str
    description: Optional[str] = None
    project_id: int
    env_id: Optional[int] = None
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    retry_on_failure: bool = False
    stop_on_failure: bool = False
    notify_on_failure: bool = False


class TestSuiteCreate(TestSuiteBase):
    pass


class TestSuiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    env_id: Optional[int] = None
    execution_mode: Optional[ExecutionMode] = None
    retry_on_failure: Optional[bool] = None
    stop_on_failure: Optional[bool] = None
    notify_on_failure: Optional[bool] = None


class TestSuiteResponse(TestSuiteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class TestSuiteListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    project_id: int
    env_id: Optional[int] = None
    execution_mode: str
    created_at: datetime
    updated_at: datetime


# ==================== TestSuiteCase ====================

class TestSuiteCaseBase(BaseModel):
    case_id: int
    order: int = 0
    enabled: bool = True
    timeout: Optional[int] = None
    retry: int = 0


class TestSuiteCaseCreate(TestSuiteCaseBase):
    pass


class TestSuiteCaseUpdate(BaseModel):
    order: Optional[int] = None
    enabled: Optional[bool] = None
    timeout: Optional[int] = None
    retry: Optional[int] = None


class TestSuiteCaseResponse(TestSuiteCaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    suite_id: int
    created_at: datetime
    updated_at: datetime


class TestSuiteCaseReorderRequest(BaseModel):
    """批量排序请求"""
    cases: List[dict]  # [{"id": 1, "order": 1}, {"id": 2, "order": 2}]


# ==================== TestSuiteVariable ====================

class VarType(str, Enum):
    STRING = "string"
    JSON = "json"
    YAML = "yaml"


class TestSuiteVariableBase(BaseModel):
    key: str
    value: Optional[str] = None
    var_type: VarType = VarType.STRING
    description: Optional[str] = None


class TestSuiteVariableCreate(TestSuiteVariableBase):
    pass


class TestSuiteVariableUpdate(BaseModel):
    value: Optional[str] = None
    var_type: Optional[VarType] = None
    description: Optional[str] = None


class TestSuiteVariableResponse(TestSuiteVariableBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    suite_id: int
    created_at: datetime
    updated_at: datetime


# ==================== TestSuiteExecution ====================

class TestSuiteExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    suite_id: int
    trace_id: Optional[str] = None
    status: str
    total_cases: int
    passed: int
    failed: int
    error: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    executor: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class TestSuiteRunRequest(BaseModel):
    """套件执行请求"""
    executor: Optional[int] = 0
    params: Optional[dict] = None


class TestSuiteRunResponse(BaseModel):
    execution_id: int
    trace_id: str
    status: str
    message: str
