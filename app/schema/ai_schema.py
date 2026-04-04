from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


# ==================== 请求 Schema ====================

class AIGenerateRequest(BaseModel):
    """AI 生成用例请求"""
    model_config = ConfigDict(str_strip_whitespace=True)

    directory_id: int
    input_type: str = "text"  # text, openapi, curl, har
    content: str
    model: Optional[str] = None  # 覆盖默认模型
    priority: str = "P3"
    status: int = 3  # 1=调试中 2=关闭 3=正常
    use_rag: bool = False  # 是否使用 RAG 知识库检索增强


class AIEnhanceRequest(BaseModel):
    """AI 增强用例断言请求"""
    model_config = ConfigDict(str_strip_whitespace=True)

    case_id: int
    response_sample: str  # 响应示例 JSON
    model: Optional[str] = None


class BatchGenerateRequest(BaseModel):
    """批量生成请求（OpenAPI）"""
    model_config = ConfigDict(str_strip_whitespace=True)

    directory_id: int
    openapi_spec: str  # OpenAPI JSON/YAML
    model: Optional[str] = None
    priority: str = "P3"
    status: int = 3
    max_cases: int = 20  # 最大用例数量


class CURLParseRequest(BaseModel):
    """cURL 解析请求"""
    model_config = ConfigDict(str_strip_whitespace=True)

    directory_id: int
    curl_command: str
    model: Optional[str] = None
    priority: str = "P3"
    status: int = 3


# ==================== 响应 Schema ====================

class GeneratedCaseResponse(BaseModel):
    """生成的用例响应"""
    model_config = ConfigDict(from_attributes=True)

    case_id: int
    name: str
    url: str
    request_method: str
    body_type: int
    body: Optional[str] = None
    request_headers: Optional[str] = None
    asserts: List[Dict[str, Any]] = []


class AIGenerateResponse(BaseModel):
    """AI 生成响应"""
    generation_id: Optional[int] = None
    case: GeneratedCaseResponse
    model: str
    tokens_used: Optional[int] = None


class BatchGenerateResponse(BaseModel):
    """批量生成响应"""
    total: int
    cases: List[GeneratedCaseResponse]
    model: str
    failed_count: int = 0


class AIModelInfo(BaseModel):
    """AI 模型信息"""
    name: str
    display_name: str
    description: str
    is_default: bool = False


class AIModelsResponse(BaseModel):
    """模型列表响应"""
    models: List[AIModelInfo]
    default_model: str
