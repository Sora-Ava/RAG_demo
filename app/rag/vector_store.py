"""
Chroma 向量库封装 —— 持久化存储，支持增量写入与检索
"""
import os
from typing import List, Dict, Any, Tuple

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from loguru import logger

from app.config import settings
from app.rag.embedder import get_embedder


class VectorStore:
    """
    对 Chroma 的轻量封装，提供:
    - add_chunks()  向量化写入
    - search()      相似度检索（带分数）
    - clear()       清空集合
    - count()       文档片段总数
    """

    def __init__(self) -> None:
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        self._embedder = get_embedder()
        self._db = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=self._embedder,
            persist_directory=settings.chroma_persist_dir,
        )
        logger.info(
            f"向量库初始化完成，集合: {settings.chroma_collection_name}，"
            f"现有片段数: {self._db._collection.count()}"
        )

    # ── 写入 ──────────────────────────────────────────────────────────────────

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        将文档片段向量化并写入 Chroma。

        参数:
            chunks: chunker.chunk_documents() 的输出

        返回:
            实际写入的片段数量
        """
        if not chunks:
            return 0

        documents = [
            Document(page_content=c["text"], metadata=c["metadata"])
            for c in chunks
        ]
        ids = [c["metadata"]["chunk_id"] for c in chunks]

        # Chroma 的 add_documents 会跳过已存在的 id
        self._db.add_documents(documents=documents, ids=ids)
        logger.info(f"向量库写入 {len(chunks)} 个片段")
        return len(chunks)

    # ── 检索 ──────────────────────────────────────────────────────────────────

    def search(
        self, query: str, top_k: int | None = None
    ) -> List[Tuple[Document, float]]:
        """
        相似度检索，返回 (Document, score) 列表，score 越高越相关。

        参数:
            query:  查询字符串
            top_k:  返回数量，默认使用 settings.top_k
        """
        k = top_k or settings.top_k
        results = self._db.similarity_search_with_relevance_scores(query, k=k)
        logger.debug(f"检索到 {len(results)} 个相关片段")
        return results

    # ── 管理 ──────────────────────────────────────────────────────────────────

    def clear(self) -> None:
        """清空整个集合"""
        self._db._client.delete_collection(settings.chroma_collection_name)
        # 重建空集合
        self._db = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=self._embedder,
            persist_directory=settings.chroma_persist_dir,
        )
        logger.info("向量库已清空")

    def count(self) -> int:
        """返回当前集合中的片段总数"""
        return self._db._collection.count()


# ── 全局单例 ─────────────────────────────────────────────────────────────────
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
