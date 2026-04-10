from typing import Optional, List, Any
from pydantic import BaseModel, Field


class CaseV2Schema(BaseModel):
    """用例主表 Schema"""
    id: Optional[int] = Field(None, description='用例ID')
    name: str = Field(..., description='用例名称')
    case_no: Optional[str] = Field(None, description='用例编号')
    priority: str = Field(default='P2', description='P0/P1/P2/P3/P4')
    status: int = Field(default=1, description='状态')
    directory_id: Optional[int] = Field(None, description='所属目录')
    tag: Optional[str] = Field(None, description='标签')
    template_id: int = Field(..., description='关联模板ID')
    case_type: str = Field(..., description='api | functional | ui')
    source: str = Field(default='manual', description='manual | ai | import | legacy')
    preconditions: Optional[str] = Field(None, description='前置条件')
    expected_result: Optional[str] = Field(None, description='预期结果')
    test_steps: Optional[str] = Field(None, description='测试步骤')
    ai_model: Optional[str] = Field(None, description='AI生成模型')
    ai_prompt: Optional[str] = Field(None, description='原始提示词')
    ai_generated_at: Optional[int] = Field(None, description='AI生成时间戳')
    parent_task_id: Optional[int] = Field(None, description='改写自生成任务ID')
    parent_case_id: Optional[int] = Field(None, description='改写自用例ID')


class CaseV2WithFieldsSchema(CaseV2Schema):
    """用例 + 扩展字段"""
    fields: Optional[List[dict]] = Field(None, description='扩展字段列表')
