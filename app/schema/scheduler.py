from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, field_validator


class TaskType(str, Enum):
    HTTP = "http"
    SQL = "sql"
    REDIS = "redis"
    PYTHON = "python"
    TESTCASE = "testcase"
    TEST_PLAN = "test_plan"


class ScheduleType(str, Enum):
    CRONTAB = "crontab"
    INTERVAL = "interval"


class IntervalType(str, Enum):
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


# ==================== Crontab Schedule ====================

class CrontabScheduleBase(BaseModel):
    minute: str = "*"
    hour: str = "*"
    day_of_week: str = "*"
    day_of_month: str = "*"
    month_of_year: str = "*"
    expression: Optional[str] = None


class CrontabScheduleCreate(CrontabScheduleBase):
    pass


class CrontabScheduleResponse(CrontabScheduleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ==================== Interval Schedule ====================

class IntervalScheduleBase(BaseModel):
    interval_type: IntervalType
    interval_value: int

    @field_validator("interval_value")
    @classmethod
    def validate_interval_value(cls, v):
        if v <= 0:
            raise ValueError("interval_value must be greater than 0")
        return v


class IntervalScheduleCreate(IntervalScheduleBase):
    pass


class IntervalScheduleResponse(IntervalScheduleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ==================== Periodic Task ====================

class PeriodicTaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    task_type: TaskType
    task_config: dict = {}
    schedule_type: ScheduleType
    crontab_id: Optional[int] = None
    interval_id: Optional[int] = None
    enabled: bool = True
    project_id: Optional[int] = None
    notify_on_failure: bool = False
    max_instances: int = 1


class PeriodicTaskCreate(PeriodicTaskBase):
    crontab_data: Optional[CrontabScheduleCreate] = None
    interval_data: Optional[IntervalScheduleCreate] = None


class PeriodicTaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    task_config: Optional[dict] = None
    enabled: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    max_instances: Optional[int] = None
    crontab_id: Optional[int] = None
    interval_id: Optional[int] = None


class PeriodicTaskResponse(PeriodicTaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    next_run_time: Optional[str] = None
    state: Optional[int] = None


class PeriodicTaskListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    task_type: str
    schedule_type: str
    enabled: bool
    project_id: Optional[int] = None
    next_run_time: Optional[str] = None
    state: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# ==================== Task Execution ====================

class TaskExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    trace_id: Optional[str] = None
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[dict] = None
    error_message: Optional[str] = None
    executor: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# ==================== Task Run ====================

class TaskRunRequest(BaseModel):
    executor: Optional[int] = 0
    params: Optional[dict] = None


class TaskRunResponse(BaseModel):
    execution_id: int
    trace_id: str
    status: str
    message: str
