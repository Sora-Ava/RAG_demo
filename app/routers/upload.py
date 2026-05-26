"""
POST /upload —— 上传文档，自动解析 → 分片 → 向量化 → 存入知识库
"""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from loguru import logger

from app.config import settings
from app.models import UploadResponse
from app.rag.document_loader import load_document, SUPPORTED_EXTENSIONS
from app.rag.chunker import chunk_documents
from app.rag.vector_store import get_vector_store

router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="上传文档构建知识库",
    description="支持 PDF / Word(.docx) / TXT，文件上传后自动解析、分片、向量化入库。",
)
async def upload_document(file: UploadFile = File(...)):
    # ── 文件格式校验 ─────────────────────────────────────────────────────────
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"不支持的文件格式 '{suffix}'，仅支持: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    # ── 文件大小校验（先读一次）──────────────────────────────────────────────
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件过大，最大限制 {settings.max_file_size // 1024 // 1024} MB",
        )

    # ── 保存到磁盘 ───────────────────────────────────────────────────────────
    os.makedirs(settings.upload_dir, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    save_path = os.path.join(settings.upload_dir, safe_name)

    with open(save_path, "wb") as f:
        f.write(content)
    logger.info(f"[Upload] 文件保存: {save_path}（{len(content)} bytes）")

    # ── 解析 → 分片 → 向量化 ─────────────────────────────────────────────────
    try:
        pages = load_document(save_path)
        chunks = chunk_documents(pages)
        added = get_vector_store().add_chunks(chunks)
    except Exception as exc:
        logger.exception(f"[Upload] 处理失败: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档处理失败: {exc}",
        )

    return UploadResponse(
        success=True,
        message=f"文档 '{file.filename}' 已成功加入知识库",
        filename=file.filename or safe_name,
        chunks_added=added,
    )
