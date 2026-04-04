"""
RAG 服务：Embedding + Vector Store
"""
import hashlib
from typing import Optional

import chromadb
from chromadb.config import Settings
from dashscope import TextEmbedding, TextReRank

from config import Config
from loguru import logger


class EmbeddingService:
    """DashScope Embedding 服务"""

    def __init__(self):
        self.model = Config.EMBEDDING_MODEL
        self.api_key = Config.DASHSCOPE_API_KEY

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量向量化文本"""
        if not texts:
            return []
        response = TextEmbedding.call(model=self.model, input=texts, api_key=self.api_key)
        if response.status_code != 200:
            raise Exception(f"Embedding failed: {response.message}")
        embeddings = [item["embedding"] for item in response.output["embeddings"]]
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """向量化查询"""
        response = TextEmbedding.call(model=self.model, input=text, api_key=self.api_key)
        if response.status_code != 200:
            raise Exception(f"Embedding query failed: {response.message}")
        return response.output["embeddings"][0]["embedding"]


class VectorStoreService:
    """ChromaDB 向量存储服务"""

    _instance: Optional["VectorStoreService"] = None

    def __init__(self):
        self.client = chromadb.HttpClient(
            host=Config.CHROMA_HOST,
            port=Config.CHROMA_PORT,
            settings=Settings(
                chroma_server_host=Config.CHROMA_HOST,
                chroma_server_http_port=Config.CHROMA_PORT,
            )
        )
        self.collection_name = Config.CHROMA_COLLECTION_NAME
        self.embedding_service = EmbeddingService()
        self._ensure_collection()

    def _ensure_collection(self):
        """确保 collection 存在"""
        existing = self.client.list_collections()
        if self.collection_name not in [c.name for c in existing]:
            self.client.create_collection(name=self.collection_name)
            logger.info(f"Created collection: {self.collection_name}")

    @classmethod
    def get_instance(cls) -> "VectorStoreService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def reset_instance(self):
        """重置单例（用于测试）"""
        self._instance = None

    def add_documents(self, doc_id: str, texts: list[str], metadata: dict) -> int:
        """添加文档到向量库，返回 chunk 数量"""
        if not texts:
            return 0
        embeddings = self.embedding_service.embed_texts(texts)
        collection = self.client.get_collection(name=self.collection_name)
        ids = [f"{doc_id}_{i}" for i in range(len(texts))]
        metadatas = [{**metadata, "chunk_index": i} for i in range(len(texts))]
        collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        logger.info(f"Added {len(texts)} chunks for doc_id={doc_id}")
        return len(texts)

    def similarity_search(self, query: str, top_k: int = None) -> dict:
        """相似度检索"""
        if top_k is None:
            top_k = Config.RETRIEVAL_TOP_K
        query_embedding = self.embedding_service.embed_query(query)
        collection = self.client.get_collection(name=self.collection_name)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return results

    def similarity_search_with_rerank(self, query: str, top_k: int = None, initial_k: int = 50) -> dict:
        """向量检索 + Rerank 精排"""
        if top_k is None:
            top_k = Config.RERANK_TOP_K
        # 第一阶段：向量检索，取更多结果
        raw_results = self.similarity_search(query, top_k=initial_k)
        # 提取文档文本
        raw_docs = raw_results.get("documents", [[]])[0] if raw_results.get("documents") else []
        if not raw_docs:
            return {"query": query, "results": [], "reranked": False}
        # 提取对应的 metadata 和 distance
        metadatas = raw_results.get("metadatas", [[]])[0] if raw_results.get("metadatas") else []
        distances = raw_results.get("distances", [[]])[0] if raw_results.get("distances") else []
        # Rerank 精排
        reranker = RerankService()
        reranked = reranker.rerank(query, raw_docs, top_k=top_k)
        # 组装结果，保留原始 metadata 和 vector distance
        results = []
        for r in reranked:
            idx = r["index"]
            results.append({
                "content": r["document"],
                "metadata": metadatas[idx] if idx < len(metadatas) else {},
                "distance": distances[idx] if idx < len(distances) else None,
                "relevance_score": r["relevance_score"],
            })
        return {"query": query, "results": results, "reranked": True}

    def delete_document(self, doc_id: str):
        """删除文档的所有 chunks"""
        collection = self.client.get_collection(name=self.collection_name)
        # 查询该文档的所有 chunk ids
        result = collection.get(where={"doc_id": doc_id})
        if result and result["ids"]:
            collection.delete(ids=result["ids"])
            logger.info(f"Deleted doc_id={doc_id}, {len(result['ids'])} chunks")

    def get_collection_info(self) -> dict:
        """获取 collection 信息"""
        collection = self.client.get_collection(name=self.collection_name)
        return {
            "name": collection.name,
            "count": collection.count(),
        }


class RerankService:
    """DashScope Rerank 精排服务"""

    def __init__(self):
        self.model = Config.RERANK_MODEL
        self.api_key = Config.DASHSCOPE_API_KEY

    def rerank(self, query: str, documents: list[str], top_k: int = None) -> list[dict]:
        """对文档列表进行 Rerank 精排"""
        if top_k is None:
            top_k = Config.RERANK_TOP_K
        if not documents:
            return []
        response = TextReRank.call(
            model=self.model,
            query=query,
            documents=documents,
            top_k=min(top_k, len(documents)),
            api_key=self.api_key
        )
        if response.status_code != 200:
            raise Exception(f"Rerank failed: {response.message}")
        return [
            {
                "index": r.index,
                "relevance_score": r.relevance_score,
                "document": r.document or documents[r.index],
            }
            for r in response.output.results
        ]
