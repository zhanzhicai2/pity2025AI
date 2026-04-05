"""
RAG 路由
"""
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form
from starlette.responses import JSONResponse

from app.crud.knowledge_base.KnowledgeBaseDao import KnowledgeBaseDao
from app.routers import Permission
from app.schema.knowledge_base_schema import (
    KnowledgeBaseResponse,
    KnowledgeBaseCreate,
    RetrievalResponse,
    RetrievalResult,
)
from app.schema.context_compress import CompressionRequest, CompressionResponse
from app.services.cache_service import CacheService
from app.services.document_parser import DocumentParser
from app.services.rag_service import VectorStoreService
from app.core.ai.context_compressor import context_compressor, hierarchical_compressor
from config import Config
from app.handler.fatcory import PityResponse

router = APIRouter(prefix="/rag", tags=["RAG"])


def get_current_user(user_info=Depends(Permission())):
    """获取当前用户"""
    return user_info


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    name: str = Form(...),
    user_info: dict = Depends(get_current_user),
):
    """上传文档到知识库"""
    user_id = user_info.get("id")
    # 1. 保存文件
    upload_dir = Path(Config.APP_PATH).parent / "uploads" / "knowledge"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        return PityResponse.failed(f"文件保存失败: {e}")

    # 2. 解析文档
    parser = DocumentParser()
    try:
        text = parser.parse(str(file_path))
    except Exception as e:
        os.remove(file_path)
        return PityResponse.failed(f"文档解析失败: {e}")

    # 3. 计算 hash 检查是否重复
    content_hash = parser.compute_hash(text)

    # 4. 切分文本
    chunks = parser.split_text(text)

    # 5. 存入向量库
    try:
        vector_store = VectorStoreService.get_instance()
        doc_id = str(uuid.uuid4())
        chunk_count = vector_store.add_documents(
            doc_id=doc_id,
            texts=chunks,
            metadata={
                "name": name,
                "file_type": file.content_type or "unknown",
                "doc_id": doc_id,
                "create_user": user_id,
            },
        )
    except Exception as e:
        os.remove(file_path)
        return PityResponse.failed(f"向量存储失败: {e}")

    # 6. 保存到数据库
    try:
        await KnowledgeBaseDao.insert_knowledge(
            name=name,
            file_type=file.content_type or "unknown",
            file_path=str(file_path),
            file_size=len(content),
            content_hash=content_hash,
            status="ready",
            chunk_count=chunk_count,
            doc_metadata={"original_filename": file.filename},
            user_id=user_id,
        )
    except Exception as e:
        # 回滚向量库
        try:
            VectorStoreService.get_instance().delete_document(doc_id)
        except Exception:
            pass
        os.remove(file_path)
        return PityResponse.failed(f"数据库记录失败: {e}")

    return PityResponse.success({"chunk_count": chunk_count}, msg="文档上传成功")


@router.post("/search")
async def search_knowledge(
    body: dict,
    user_info: dict = Depends(get_current_user),
):
    query: str = body.get("query", "")
    top_k: int = body.get("top_k", 10)
    use_cache: bool = body.get("use_cache", True)
    """检索知识库"""
    # 检查缓存
    if use_cache:
        try:
            cache = CacheService()
            cached = cache.get("search", query)
            if cached:
                return PityResponse.success(cached)
        except Exception:
            pass  # Redis 不可用时跳过缓存

    # 检索
    try:
        vector_store = VectorStoreService.get_instance()
        results = vector_store.similarity_search(query, top_k=top_k)
    except Exception as e:
        return PityResponse.failed(f"检索失败: {e}")

    # 构造返回
    docs = []
    if results.get("documents"):
        for i, doc in enumerate(results["documents"][0]):
            docs.append(
                RetrievalResult(
                    content=doc,
                    metadata=results["metadatas"][0][i] if results.get("metadatas") else {},
                    distance=results["distances"][0][i] if results.get("distances") else None,
                )
            )

    response = {"query": query, "results": docs, "count": len(docs)}

    # 写入缓存
    if use_cache:
        try:
            cache = CacheService()
            cache.set("search", query, response, ttl=3600)
        except Exception:
            pass

    return PityResponse.success(response)


@router.post("/search-v2")
async def search_knowledge_v2(
    body: dict,
    user_info: dict = Depends(get_current_user),
):
    """检索知识库（带 Rerank 精排）"""
    query: str = body.get("query", "")
    top_k: int = body.get("top_k", 10)
    initial_k: int = body.get("initial_k", 50)
    use_cache: bool = body.get("use_cache", False)  # Rerank 结果默认不缓存

    try:
        vector_store = VectorStoreService.get_instance()
        results = vector_store.similarity_search_with_rerank(
            query, top_k=top_k, initial_k=initial_k
        )
    except Exception as e:
        return PityResponse.failed(f"检索失败: {e}")

    return PityResponse.success(results)


@router.get("/list")
async def list_documents(
    page: int = 1,
    size: int = 20,
    name: Optional[str] = None,
    status: Optional[str] = None,
    user_info: dict = Depends(get_current_user),
):
    """列出知识库文档"""
    try:
        data, total = await KnowledgeBaseDao.list_knowledge(
            page=page, size=size, name=name, status=status
        )
        return PityResponse.success(
            {"list": [KnowledgeBaseResponse.model_validate(d) for d in data], "total": total}
        )
    except Exception as e:
        return PityResponse.failed(f"查询失败: {e}")


@router.get("/{doc_id}")
async def get_document(
    doc_id: int,
    user_info: dict = Depends(get_current_user),
):
    """获取文档详情"""
    try:
        from app.crud import Mapper

        record = await Mapper.query_record(KnowledgeBaseDao, id=doc_id)
        if record is None:
            return PityResponse.failed("文档不存在")
        return PityResponse.success(KnowledgeBaseResponse.model_validate(record))
    except Exception as e:
        return PityResponse.failed(f"查询失败: {e}")


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    user_info: dict = Depends(get_current_user),
):
    """删除文档"""
    user_id = user_info.get("id")
    try:
        from app.crud import Mapper

        record = await Mapper.query_record(KnowledgeBaseDao, id=doc_id)
        if record is None:
            return PityResponse.failed("文档不存在")

        # 删除向量库中的 chunks
        try:
            vector_store = VectorStoreService.get_instance()
            vector_store.delete_document(record.content_hash)
        except Exception:
            pass

        # 删除文件
        try:
            if os.path.exists(record.file_path):
                os.remove(record.file_path)
        except Exception:
            pass

        # 软删除数据库记录
        await Mapper.delete_record_by_id(KnowledgeBaseDao, session=None, user=user_id, value=doc_id)
        return PityResponse.success(msg="删除成功")
    except Exception as e:
        return PityResponse.failed(f"删除失败: {e}")


@router.post("/compress")
async def compress_context(
    body: CompressionRequest,
    user_info: dict = Depends(get_current_user),
):
    """压缩上下文 - Phase 16"""
    try:
        # 根据压缩级别选择压缩器
        if body.compression_level == "sentence":
            compressor = hierarchical_compressor
            result = await compressor.compress_hierarchical(
                query=body.query,
                documents=body.documents,
                max_context_length=body.max_context_length,
                level="sentence"
            )
        elif body.compression_level == "paragraph":
            compressor = hierarchical_compressor
            result = await compressor.compress_hierarchical(
                query=body.query,
                documents=body.documents,
                max_context_length=body.max_context_length,
                level="paragraph"
            )
        else:  # auto
            result = await context_compressor.compress(
                query=body.query,
                documents=body.documents,
                max_context_length=body.max_context_length
            )

        return PityResponse.success(result)
    except Exception as e:
        return PityResponse.failed(f"上下文压缩失败: {e}")


@router.post("/search-with-compress")
async def search_with_compress(
    body: dict,
    user_info: dict = Depends(get_current_user),
):
    """检索并压缩 - Phase 16"""
    query: str = body.get("query", "")
    top_k: int = body.get("top_k", 10)
    compress: bool = body.get("compress", True)
    compression_level: str = body.get("compression_level", "auto")
    max_context_length: int = body.get("max_context_length", 4000)

    try:
        # 1. 向量检索
        vector_store = VectorStoreService.get_instance()
        results = vector_store.similarity_search_with_rerank(query, top_k=top_k)

        if not results.get("results"):
            return PityResponse.success({
                "query": query,
                "compressed_context": "",
                "chunks": [],
                "summary": "未检索到相关文档"
            })

        # 2. 提取文档列表
        documents = [
            {
                "content": r.get("content", ""),
                "metadata": r.get("metadata", {}),
                "distance": r.get("distance")
            }
            for r in results["results"]
        ]

        # 3. 压缩
        if compress:
            if compression_level == "sentence":
                compressor = hierarchical_compressor
                compressed = await compressor.compress_hierarchical(
                    query=query,
                    documents=documents,
                    max_context_length=max_context_length,
                    level="sentence"
                )
            elif compression_level == "paragraph":
                compressor = hierarchical_compressor
                compressed = await compressor.compress_hierarchical(
                    query=query,
                    documents=documents,
                    max_context_length=max_context_length,
                    level="paragraph"
                )
            else:
                compressed = await context_compressor.compress(
                    query=query,
                    documents=documents,
                    max_context_length=max_context_length
                )

            # 4. 拼接压缩后的上下文
            compressed_context = "\n\n".join([
                c["content"] for c in compressed.get("compressed_chunks", [])
            ])

            return PityResponse.success({
                "query": query,
                "compressed_context": compressed_context,
                "chunks": compressed.get("compressed_chunks", []),
                "summary": compressed.get("summary", ""),
                "original_count": compressed.get("original_count", 0),
                "compressed_count": compressed.get("compressed_count", 0),
            })
        else:
            # 不压缩，直接拼接
            raw_context = "\n\n".join([d.get("content", "") for d in documents])
            return PityResponse.success({
                "query": query,
                "compressed_context": raw_context,
                "chunks": documents,
                "summary": f"未压缩，共 {len(documents)} 个文档",
                "original_count": len(documents),
                "compressed_count": len(documents),
            })

    except Exception as e:
        return PityResponse.failed(f"检索压缩失败: {e}")
