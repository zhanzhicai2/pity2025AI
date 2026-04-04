"""
LangGraph 状态定义
"""
from typing import Optional, List
from typing_extensions import TypedDict


class CaseGenerationState(TypedDict):
    """用例生成状态"""
    # 输入
    api_description: str  # API 描述
    user_id: int  # 用户ID
    use_rag: bool  # 是否使用 RAG

    # 中间状态
    rag_docs: List[str]  # RAG 检索到的文档
    generated_case: Optional[dict]  # 生成的用例
    review_result: Optional[dict]  # 审查结果
    error: Optional[str]  # 错误信息

    # 输出
    final_case: Optional[dict]  # 最终用例
    success: bool  # 是否成功
