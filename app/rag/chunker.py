"""
文本分片器 —— 递归字符切分，保留来源元数据
"""
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from app.config import settings


def chunk_documents(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    将解析后的页面列表切分为更小的片段。

    参数:
        pages: load_document() 的输出，每项含 text 和 metadata

    返回:
        List[{"text": str, "metadata": dict}]，每项新增 chunk_id
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
    )

    chunks: List[Dict[str, Any]] = []
    for page in pages:
        sub_texts = splitter.split_text(page["text"])
        for idx, sub_text in enumerate(sub_texts):
            chunk_id = f"{page['metadata']['source']}_p{page['metadata']['page']}_c{idx}"
            chunks.append({
                "text": sub_text,
                "metadata": {
                    **page["metadata"],
                    "chunk_id": chunk_id,
                },
            })

    logger.info(f"文本分片完成，共 {len(chunks)} 个片段")
    return chunks
