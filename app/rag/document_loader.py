"""
文档解析器 —— 支持 PDF / Word / TXT
返回统一格式：List[{"text": str, "metadata": dict}]
"""
import os
from pathlib import Path
from typing import List, Dict, Any

import PyPDF2
from docx import Document as DocxDocument
from loguru import logger


# ──────────────────────────────────────────────────────────────────────────────
# 内部解析函数
# ──────────────────────────────────────────────────────────────────────────────

def _load_pdf(file_path: str) -> List[Dict[str, Any]]:
    """逐页解析 PDF，保留页码元数据"""
    pages = []
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append({
                    "text": text,
                    "metadata": {
                        "source": Path(file_path).name,
                        "page": page_num,
                        "file_type": "pdf",
                    },
                })
    logger.info(f"PDF 解析完成: {Path(file_path).name}，共 {len(pages)} 页")
    return pages


def _load_docx(file_path: str) -> List[Dict[str, Any]]:
    """解析 Word 文档，按段落聚合（每 20 段一组以模拟页）"""
    doc = DocxDocument(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    # 每 20 个段落视为「一页」
    batch_size = 20
    pages = []
    for i in range(0, len(paragraphs), batch_size):
        chunk_text = "\n".join(paragraphs[i: i + batch_size])
        pages.append({
            "text": chunk_text,
            "metadata": {
                "source": Path(file_path).name,
                "page": i // batch_size + 1,
                "file_type": "docx",
            },
        })
    logger.info(f"Word 解析完成: {Path(file_path).name}，共 {len(pages)} 组")
    return pages


def _load_txt(file_path: str) -> List[Dict[str, Any]]:
    """解析纯文本，整个文件作为第 1 页"""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read().strip()
    logger.info(f"TXT 解析完成: {Path(file_path).name}")
    return [
        {
            "text": text,
            "metadata": {
                "source": Path(file_path).name,
                "page": 1,
                "file_type": "txt",
            },
        }
    ]


# ──────────────────────────────────────────────────────────────────────────────
# 公共入口
# ──────────────────────────────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}


def load_document(file_path: str) -> List[Dict[str, Any]]:
    """
    加载文档并返回 List[{"text": str, "metadata": dict}]
    支持 PDF / DOCX / TXT，不支持的格式抛出 ValueError
    """
    ext = Path(file_path).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"不支持的文件格式: {ext}，仅支持 {SUPPORTED_EXTENSIONS}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if ext == ".pdf":
        return _load_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return _load_docx(file_path)
    elif ext == ".txt":
        return _load_txt(file_path)
    else:
        raise ValueError(f"解析器未实现: {ext}")
