"""
Phase X Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PhaseXPlanSchema(BaseModel):
    """Phase X 测试计划 Schema"""
    id: Optional[int] = Field(None, description='计划ID')
    name: str = Field(..., description='计划名称')
    description: Optional[str] = Field(None, description='计划描述')
    project_id: int = Field(..., description='所属项目ID')
    plan_type: str = Field(..., description='plan_type: single | scenario | suite')
    target_id: Optional[int] = Field(None, description='目标ID')
    target_name: Optional[str] = Field(None, description='目标名称')
    environment_id: Optional[int] = Field(None, description='环境ID')
    cron_expression: Optional[str] = Field(None, description='Cron表达式')
    is_periodic: int = Field(0, description='是否周期执行')
    config: Optional[Dict[str, Any]] = Field(None, description='执行配置')
    is_active: int = Field(1, description='是否启用')
    tags: Optional[str] = Field(None, description='标签')


class PhaseXPlanUpdateSchema(BaseModel):
    """Phase X 测试计划更新 Schema"""
    id: int = Field(..., description='计划ID')
    name: Optional[str] = Field(None, description='计划名称')
    description: Optional[str] = Field(None, description='计划描述')
    project_id: Optional[int] = Field(None, description='所属项目ID')
    plan_type: Optional[str] = Field(None, description='plan_type')
    target_id: Optional[int] = Field(None, description='目标ID')
    target_name: Optional[str] = Field(None, description='目标名称')
    environment_id: Optional[int] = Field(None, description='环境ID')
    cron_expression: Optional[str] = Field(None, description='Cron表达式')
    is_periodic: Optional[int] = Field(None, description='是否周期执行')
    config: Optional[Dict[str, Any]] = Field(None, description='执行配置')
    is_active: Optional[int] = Field(None, description='是否启用')
    tags: Optional[str] = Field(None, description='标签')


class PhaseXExecutionSchema(BaseModel):
    """Phase X 执行记录 Schema"""
    id: Optional[int] = Field(None, description='执行ID')
    plan_id: int = Field(..., description='计划ID')
    scenario_id: Optional[int] = Field(None, description='场景ID')
    case_id: Optional[int] = Field(None, description='用例ID')
    project_id: int = Field(..., description='项目ID')
    environment_id: Optional[int] = Field(None, description='环境ID')
    status: str = Field('pending', description='状态')
    duration_ms: Optional[int] = Field(None, description='执行耗时')
    executor: Optional[str] = Field(None, description='执行人')
    request_data: Optional[Dict[str, Any]] = Field(None, description='请求数据')
    response_data: Optional[Dict[str, Any]] = Field(None, description='响应数据')
    error_message: Optional[str] = Field(None, description='错误信息')
    logs: Optional[str] = Field(None, description='执行日志')
    step_results: Optional[List[Dict[str, Any]]] = Field(None, description='步骤结果')


class PhaseXReportSchema(BaseModel):
    """Phase X 测试报告 Schema"""
    id: Optional[int] = Field(None, description='报告ID')
    name: str = Field(..., description='报告名称')
    project_id: int = Field(..., description='项目ID')
    total_runs: int = Field(0, description='总执行次数')
    total_passed: int = Field(0, description='总通过次数')
    total_failed: int = Field(0, description='总失败次数')
    total_error: int = Field(0, description='总错误次数')
    trend_data: Optional[List[Dict[str, Any]]] = Field(None, description='趋势数据')
    avg_duration_ms: Optional[int] = Field(None, description='平均耗时')
    pass_rate: Optional[str] = Field(None, description='通过率')
