from typing import Optional, List, Any
from pydantic import BaseModel, Field


class AIGenerationTaskSchema(BaseModel):
    """AI 生成任务 Schema"""
    id: Optional[int] = Field(None, description='任务ID')
    name: str = Field(..., description='任务名称')
    project_id: int = Field(..., description='所属项目ID')
    template_id: int = Field(..., description='关联模板ID')
    case_type: str = Field(..., description='用例类型: api | functional | ui')
    requirement: str = Field(..., description='用户需求描述')

    # 可选字段
    source: str = Field(default='ai', description='来源')
    modules: Optional[List[dict]] = Field(None, description='AI 解析出的模块列表')
    module_count: Optional[int] = Field(None, description='模块数量')
    status: str = Field(default='pending', description='状态')
    total_cases: Optional[int] = Field(None, description='计划生成用例数')
    generated_cases: Optional[int] = Field(None, description='实际生成用例数')
    progress: int = Field(default=0, description='进度百分比')
    ai_model: Optional[str] = Field(None, description='AI模型')
    prompt_tokens: Optional[int] = Field(None, description='输入Token消耗')
    completion_tokens: Optional[int] = Field(None, description='输出Token消耗')


class AIGenerationTaskCreateSchema(AIGenerationTaskSchema):
    """创建 AI 生成任务"""
    pass


class AIGenerationTaskUpdateSchema(BaseModel):
    """更新 AI 生成任务"""
    id: int = Field(..., description='任务ID')
    name: Optional[str] = Field(None, description='任务名称')
    status: Optional[str] = Field(None, description='状态')
    modules: Optional[List[dict]] = Field(None, description='AI 解析出的模块列表')
    module_count: Optional[int] = Field(None, description='模块数量')
    total_cases: Optional[int] = Field(None, description='计划生成用例数')
    generated_cases: Optional[int] = Field(None, description='实际生成用例数')
    progress: Optional[int] = Field(None, description='进度百分比')
    ai_model: Optional[str] = Field(None, description='AI模型')
    prompt_tokens: Optional[int] = Field(None, description='输入Token消耗')
    completion_tokens: Optional[int] = Field(None, description='输出Token消耗')
