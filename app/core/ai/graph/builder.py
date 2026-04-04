"""
LangGraph 用例生成工作流构建器
"""
from langgraph.graph import StateGraph, END

from app.core.ai.graph.state import CaseGenerationState
from app.core.ai.graph.nodes import CaseGraphNodes


def build_case_generation_graph():
    """构建用例生成工作流图（简化版：无重试）"""

    graph = StateGraph(CaseGenerationState)

    # 添加节点
    graph.add_node("retrieval", CaseGraphNodes.retrieval)
    graph.add_node("generate", CaseGraphNodes.generate)
    graph.add_node("review", CaseGraphNodes.review)

    # 设置入口
    graph.set_entry_point("retrieval")

    # 线性流程：retrieval -> generate -> review -> end
    graph.add_edge("retrieval", "generate")
    graph.add_edge("generate", "review")
    graph.add_edge("review", END)

    return graph.compile()
