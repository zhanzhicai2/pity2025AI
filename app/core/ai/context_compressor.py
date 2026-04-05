"""
上下文压缩器
优化 RAG 检索效果，压缩无关内容，保留关键信息
"""
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from loguru import logger

from app.core.ai.openai_service import ai_service


@dataclass
class CompressedChunk:
    """压缩后的文档块"""
    content: str
    relevance_score: float
    original_index: int
    source: Optional[str] = None


class ContextCompressor:
    """
    上下文压缩器
    使用 LLM 判断每个 chunk 的相关性，移除无关内容
    """

    def __init__(self, compression_model: Optional[str] = None):
        """
        初始化压缩器

        Args:
            compression_model: 用于压缩的模型（默认使用配置的 AI 模型）
        """
        self.compression_model = compression_model

    async def compress(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        max_context_length: int = 4000
    ) -> Dict[str, Any]:
        """
        压缩文档列表，保留与查询最相关的内容

        Args:
            query: 用户查询
            documents: 检索到的文档列表，每项包含 content, metadata, distance 等
            max_context_length: 最大上下文长度（token 估算）

        Returns:
            压缩后的结果，包含 compressed_chunks 和 summary
        """
        if not documents:
            return {
                "compressed_chunks": [],
                "summary": "",
                "original_count": 0,
                "compressed_count": 0,
            }

        # 1. 评估每个文档与查询的相关性
        relevance_scores = await self._score_relevance(query, documents)

        # 2. 根据相关性筛选和压缩
        compressed = []
        total_length = 0

        for i, doc in enumerate(documents):
            score = relevance_scores[i]
            if score < 0.3:  # 相关性低于阈值则跳过
                continue

            content = doc.get("content", "")
            # 简单估算 token 数（中文约 2 字符 ≈ 1 token，英文约 4 字符 ≈ 1 token）
            estimated_tokens = self._estimate_tokens(content)

            # 如果加上这个文档会超出限制，尝试压缩
            if total_length + estimated_tokens > max_context_length:
                # 尝试压缩到剩余空间
                remaining = max_context_length - total_length
                if remaining < 100:  # 剩余空间太小，停止添加
                    break
                content = await self._compress_single(query, content, remaining)
                estimated_tokens = self._estimate_tokens(content)

            if total_length + estimated_tokens <= max_context_length:
                compressed.append(CompressedChunk(
                    content=content,
                    relevance_score=score,
                    original_index=i,
                    source=doc.get("metadata", {}).get("source")
                ))
                total_length += estimated_tokens
            else:
                # 最后一个文档，尝试压缩后添加
                remaining = max_context_length - total_length
                if remaining >= 100:
                    compressed_content = await self._compress_single(query, content, remaining)
                    compressed.append(CompressedChunk(
                        content=compressed_content,
                        relevance_score=score,
                        original_index=i,
                        source=doc.get("metadata", {}).get("source")
                    ))
                break

        return {
            "compressed_chunks": [
                {
                    "content": c.content,
                    "relevance_score": c.relevance_score,
                    "original_index": c.original_index,
                    "source": c.source
                }
                for c in compressed
            ],
            "summary": f"从 {len(documents)} 个文档中压缩为 {len(compressed)} 个相关块",
            "original_count": len(documents),
            "compressed_count": len(compressed),
        }

    async def _score_relevance(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> List[float]:
        """
        使用 LLM 评估每个文档与查询的相关性

        Args:
            query: 用户查询
            documents: 文档列表

        Returns:
            每个文档的相关性分数列表
        """
        if not documents:
            return []

        # 构造评分 prompt
        doc_summaries = []
        for i, doc in enumerate(documents):
            content = doc.get("content", "")[:500]  # 只取前 500 字符用于评分
            doc_summaries.append(f"[文档 {i+1}]\n{content}")

        separator = "\n\n"
        joined_docs = separator.join(doc_summaries)

        prompt = f"""你是一个相关性评估助手。请评估每个文档与用户查询的相关程度。

用户查询: {query}

{joined_docs}

请以 JSON 格式返回评估结果：
{{
    "scores": [0.0-1.0 之间的分数，按文档顺序]
}}

只返回一个 JSON 对象，不要有其他内容。分数说明：
- 1.0: 完全相关，直接回答问题
- 0.7-0.9: 高度相关，包含重要参考信息
- 0.4-0.6: 中度相关，可能有一定帮助
- 0.1-0.3: 低度相关，信息有限
- 0.0: 完全不相关，与问题无关
"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await ai_service.chat(
                messages,
                model=self.compression_model,
                temperature=0.1,  # 低温度保证稳定性
                max_tokens=1000
            )

            # 解析 JSON 响应
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            result = json.loads(response)
            scores = result.get("scores", [])

            # 确保分数数量与文档数量一致
            while len(scores) < len(documents):
                scores.append(0.0)
            return scores[:len(documents)]

        except Exception as e:
            logger.bind(name=None).warning(f"相关性评估失败: {e}")
            # 失败时返回均匀分数
            return [0.5] * len(documents)

    async def _compress_single(
        self,
        query: str,
        content: str,
        max_tokens: int
    ) -> str:
        """
        压缩单个文档到指定长度

        Args:
            query: 用户查询
            content: 原始内容
            max_tokens: 最大 token 数（估算）

        Returns:
            压缩后的内容
        """
        # 估算字符数（假设 2 字符 ≈ 1 token）
        max_chars = max_tokens * 2

        if len(content) <= max_chars:
            return content

        prompt = f"""你是一个文本压缩助手。请压缩以下文本，保留与用户查询最相关的部分。

用户查询: {query}

原始文本:
{content}

请在 {max_chars} 个字符内，保留最相关的信息，生成简洁的摘要。
直接返回压缩后的文本，不要有其他解释。"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await ai_service.chat(
                messages,
                model=self.compression_model,
                temperature=0.3,
                max_tokens=max_tokens
            )
            return response.strip()
        except Exception as e:
            logger.bind(name=None).warning(f"文本压缩失败: {e}")
            # 压缩失败时直接截断
            return content[:max_chars]

    def _estimate_tokens(self, text: str) -> int:
        """
        估算文本的 token 数量

        Args:
            text: 文本

        Returns:
            估算的 token 数量
        """
        # 简单估算：中文约 2 字符 ≈ 1 token，英文约 4 字符 ≈ 1 token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return chinese_chars // 2 + other_chars // 4


class HierarchicalCompressor(ContextCompressor):
    """
    层次化压缩器
    支持文档 → 段落 → 句子逐层压缩
    """

    def __init__(self, compression_model: Optional[str] = None):
        super().__init__(compression_model)

    async def compress_hierarchical(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        max_context_length: int = 4000,
        level: str = "paragraph"
    ) -> Dict[str, Any]:
        """
        层次化压缩

        Args:
            query: 用户查询
            documents: 文档列表
            max_context_length: 最大上下文长度
            level: 压缩级别 ("document", "paragraph", "sentence")
        """
        if level == "sentence":
            return await self._compress_to_sentences(query, documents, max_context_length)
        elif level == "paragraph":
            return await self._compress_to_paragraphs(query, documents, max_context_length)
        else:
            return await self.compress(query, documents, max_context_length)

    async def _compress_to_paragraphs(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        max_context_length: int
    ) -> Dict[str, Any]:
        """压缩到段落级别"""
        # 1. 先压缩每个文档到段落
        compressed_docs = []
        for doc in documents:
            content = doc.get("content", "")
            paragraphs = content.split("\n\n")  # 按双换行分割段落

            # 评估每个段落
            relevance_scores = await self._score_relevance(query, [
                {"content": p, "metadata": doc.get("metadata", {})}
                for p in paragraphs if p.strip()
            ])

            # 选择最相关的段落
            selected = []
            total_len = 0
            for i, para in enumerate(paragraphs):
                if not para.strip():
                    continue
                score = relevance_scores[len(selected)] if len(selected) < len(relevance_scores) else 0
                if score >= 0.4:
                    para_len = self._estimate_tokens(para)
                    if total_len + para_len <= max_context_length:
                        selected.append(para)
                        total_len += para_len

            if selected:
                compressed_docs.append({
                    "content": "\n\n".join(selected),
                    "metadata": doc.get("metadata", {}),
                    "distance": doc.get("distance")
                })

        # 2. 对整体进行二次压缩
        return await self.compress(query, compressed_docs, max_context_length)

    async def _compress_to_sentences(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        max_context_length: int
    ) -> Dict[str, Any]:
        """压缩到句子级别"""
        import re

        # 按句子分割
        all_sentences = []
        sentence_sources = []  # 记录每句话的来源

        for doc in documents:
            content = doc.get("content", "")
            # 简单按句号、问号、感叹号分割
            sentences = re.split(r'([。！？.?!])', content)
            # 重新组合句子和标点
            combined = []
            for i in range(0, len(sentences) - 1, 2):
                if i + 1 < len(sentences):
                    combined.append(sentences[i] + sentences[i + 1])
                else:
                    combined.append(sentences[i])

            for sent in combined:
                if sent.strip():
                    all_sentences.append(sent)
                    sentence_sources.append(doc.get("metadata", {}).get("source"))

        if not all_sentences:
            return {
                "compressed_chunks": [],
                "summary": "无有效句子",
                "original_count": 0,
                "compressed_count": 0,
            }

        # 评估每个句子
        docs_for_scoring = [{"content": s, "metadata": {"source": sentence_sources[i]}}
                           for i, s in enumerate(all_sentences)]
        relevance_scores = await self._score_relevance(query, docs_for_scoring)

        # 选择最相关的句子
        selected = []
        total_len = 0
        for i, sent in enumerate(all_sentences):
            score = relevance_scores[i]
            if score >= 0.5:  # 句子需要更高相关性
                sent_len = self._estimate_tokens(sent)
                if total_len + sent_len <= max_context_length:
                    selected.append({
                        "content": sent,
                        "relevance_score": score,
                        "source": sentence_sources[i]
                    })
                    total_len += sent_len

        return {
            "compressed_chunks": selected,
            "summary": f"从 {len(all_sentences)} 个句子中保留 {len(selected)} 个相关句子",
            "original_count": len(all_sentences),
            "compressed_count": len(selected),
        }


# 全局单例
context_compressor = ContextCompressor()
hierarchical_compressor = HierarchicalCompressor()
