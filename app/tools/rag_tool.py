"""
RAG 检索工具 —— Agent 从企业知识库检索相关内容
返回格式化文本（含引用元数据 JSON），供工具节点提取 citations
"""
import json
from langchain_core.tools import tool
from loguru import logger

from app.rag.vector_store import get_vector_store

# 分隔符，工具节点依赖此标记解析 citations
_CITATION_MARKER = "[CITATIONS_JSON]:"


@tool
def rag_search(query: str) -> str:
    """
    从企业知识库中检索与用户问题最相关的文档内容。
    当用户提出需要查阅内部文档、规章制度、产品手册等知识型问题时使用此工具。

    Args:
        query: 用于检索的查询语句，应尽量精炼、语义清晰
    """
    logger.info(f"[RAG] 检索: {query!r}")
    vs = get_vector_store()

    if vs.count() == 0:
        return "知识库当前为空，请先上传文档。"

    results = vs.search(query)

    if not results:
        return "知识库中未找到与您问题相关的内容，请换个关键词或上传更多文档。"

    citations = []
    content_parts = []

    for doc, score in results:
        meta = doc.metadata
        source = meta.get("source", "未知文件")
        page = meta.get("page", 0)
        chunk_id = meta.get("chunk_id", "")

        citations.append({
            "source": source,
            "page": page,
            "chunk_id": chunk_id,
            "text": doc.page_content[:200],  # 摘要前 200 字
            "score": round(float(score), 4),
        })
        content_parts.append(
            f"【来源: {source} | 第 {page} 页 | 相关度: {score:.2%}】\n{doc.page_content}"
        )

    retrieved_text = "\n\n" + "─" * 40 + "\n\n".join(content_parts)
    # 附加引用 JSON，供 tool_node 解析
    citation_json = json.dumps(citations, ensure_ascii=False)
    return f"{retrieved_text}\n\n{_CITATION_MARKER} {citation_json}"
