"""
场景流程 Schema
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class ScenarioStepSchema(BaseModel):
    """场景步骤 Schema"""
    id: Optional[int] = Field(None, description='步骤ID')
    scenario_id: int = Field(..., description='场景ID')
    case_id: int = Field(..., description='用例ID')
    step_order: int = Field(..., description='步骤顺序')
    step_name: Optional[str] = Field(None, description='步骤名称')
    input_mapping: Optional[List[dict]] = Field(None, description='输入参数映射')
    output_mapping: Optional[List[dict]] = Field(None, description='输出参数映射')
    condition: Optional[str] = Field(None, description='执行条件')
    condition_field: Optional[str] = Field(None, description='条件字段')
    timeout_ms: int = Field(30000, description='超时时间（毫秒）')
    retry_count: int = Field(0, description='失败重试次数')
    retry_interval_ms: int = Field(1000, description='重试间隔（毫秒）')


class ScenarioStepUpdateSchema(BaseModel):
    """场景步骤更新 Schema"""
    id: int = Field(..., description='步骤ID')
    scenario_id: Optional[int] = Field(None, description='场景ID')
    case_id: Optional[int] = Field(None, description='用例ID')
    step_order: Optional[int] = Field(None, description='步骤顺序')
    step_name: Optional[str] = Field(None, description='步骤名称')
    input_mapping: Optional[List[dict]] = Field(None, description='输入参数映射')
    output_mapping: Optional[List[dict]] = Field(None, description='输出参数映射')
    condition: Optional[str] = Field(None, description='执行条件')
    condition_field: Optional[str] = Field(None, description='条件字段')
    timeout_ms: Optional[int] = Field(None, description='超时时间（毫秒）')
    retry_count: Optional[int] = Field(None, description='失败重试次数')
    retry_interval_ms: Optional[int] = Field(None, description='重试间隔（毫秒）')


class ScenarioSchema(BaseModel):
    """场景流程 Schema"""
    id: Optional[int] = Field(None, description='场景ID')
    name: str = Field(..., description='场景名称')
    description: Optional[str] = Field(None, description='场景描述')
    project_id: int = Field(..., description='所属项目ID')
    case_type: str = Field(..., description='用例类型: api | functional | ui')
    source: str = Field('manual', description='来源: manual | ai | import')
    variables: Optional[dict] = Field(None, description='全局变量')
    is_active: int = Field(1, description='是否启用')
    tags: Optional[str] = Field(None, description='标签')


class ScenarioUpdateSchema(BaseModel):
    """场景流程更新 Schema"""
    id: int = Field(..., description='场景ID')
    name: Optional[str] = Field(None, description='场景名称')
    description: Optional[str] = Field(None, description='场景描述')
    project_id: Optional[int] = Field(None, description='所属项目ID')
    case_type: Optional[str] = Field(None, description='用例类型')
    source: Optional[str] = Field(None, description='来源')
    variables: Optional[dict] = Field(None, description='全局变量')
    is_active: Optional[int] = Field(None, description='是否启用')
    tags: Optional[str] = Field(None, description='标签')
