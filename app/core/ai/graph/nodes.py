"""
LangGraph 节点定义
"""
import json
from typing import Optional

from langchain_core.messages import HumanMessage, AIMessage
from loguru import logger

from app.core.ai.factory import get_ai_service
from app.services.rag_service import VectorStoreService
from config import Config


class CaseGraphNodes:
    """用例生成 Graph 节点"""

    @staticmethod
    async def retrieval(state: dict) -> dict:
        """检索节点：RAG 知识库检索"""
        api_desc = state.get("api_description", "")
        use_rag = state.get("use_rag", False)

        if not use_rag:
            logger.bind(name=Config.PITY_INFO).info("RAG 检索跳过（use_rag=False）")
            return {"rag_docs": [], "retry_count": 0}

        try:
            vs = VectorStoreService.get_instance()
            results = vs.similarity_search_with_rerank(api_desc, top_k=5, initial_k=20)
            docs = []
            if results.get("results"):
                docs = [r["content"] for r in results["results"]]
                logger.bind(name=Config.PITY_INFO).info(f"RAG 检索到 {len(docs)} 条文档")
            return {"rag_docs": docs, "retry_count": 0}
        except Exception as e:
            logger.bind(name=Config.PITY_ERROR).warning(f"RAG 检索失败: {e}")
            return {"rag_docs": [], "retry_count": 0}

    @staticmethod
    async def generate(state: dict) -> dict:
        """生成节点：调用 AI 生成用例"""
        api_desc = state.get("api_description", "")
        rag_docs = state.get("rag_docs", [])
        retry_count = state.get("retry_count", 0)
        messages = []

        # 构建消息
        if rag_docs:
            docs_text = "\n\n".join([f"【文档 {i+1}】{d}" for i, d in enumerate(rag_docs)])
            system_prompt = f"""你是一个专业的 API 测试工程师。
参考知识库文档：
{docs_text}

请根据 API 描述生成测试用例配置。"""
            messages.append(AIMessage(content=system_prompt))

        messages.append(HumanMessage(content=api_desc))

        try:
            ai_svc = await get_ai_service()
            response = await ai_svc.chat(messages)
            case = ai_svc._parse_testcase_response(response)
            logger.bind(name=Config.PITY_INFO).info(f"AI 生成用例成功（retry={retry_count}）: {case.get('name', 'unknown')}")
            return {"generated_case": case, "success": True, "retry_count": retry_count}
        except Exception as e:
            logger.bind(name=Config.PITY_ERROR).error(f"AI 生成用例失败: {e}")
            return {"error": str(e), "success": False, "retry_count": retry_count}

    @staticmethod
    async def review(state: dict) -> dict:
        """审查节点：AI 自我审查生成的用例"""
        generated_case = state.get("generated_case")
        retry_count = state.get("retry_count", 0)

        if not generated_case:
            return {"review_result": {"valid": False, "reason": "无生成用例"}, "retry_count": retry_count}

        # 构建审查 Prompt
        review_prompt = f"""请审查以下测试用例配置是否合理：

```json
{json.dumps(generated_case, ensure_ascii=False, indent=2)}
```

请输出 JSON 格式：
```json
{{
    "valid": true/false,
    "reason": "审查说明",
    "suggestions": ["建议1", "建议2"]
}}
```"""

        try:
            ai_svc = await get_ai_service()
            response = await ai_svc.chat([
                HumanMessage(content=review_prompt)
            ])
            # 解析审查结果
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                review = json.loads(response[start:end].strip())
            else:
                review = {"valid": True, "reason": response[:200]}

            # 如果审查不通过，增加重试计数
            if not review.get("valid", True):
                retry_count += 1
                review["retry_count"] = retry_count

            logger.bind(name=Config.PITY_INFO).info(f"用例审查完成: valid={review.get('valid')}, retry={retry_count}")
            return {"review_result": review, "retry_count": retry_count}
        except Exception as e:
            logger.bind(name=Config.PITY_ERROR).warning(f"用例审查失败: {e}")
            return {"review_result": {"valid": True, "reason": f"审查异常: {e}"}, "retry_count": retry_count}

    @staticmethod
    def should_regenerate(state: dict) -> str:
        """条件边：判断是否需要重新生成"""
        review = state.get("review_result", {})
        if not review.get("valid", True):
            logger.bind(name=Config.PITY_INFO).info("用例审查不通过，准备重新生成")
            return "regenerate"
        return "end"
