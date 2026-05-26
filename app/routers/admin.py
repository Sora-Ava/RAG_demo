"""
DELETE /clear —— 清空向量知识库
"""
from fastapi import APIRouter
from loguru import logger

from app.models import ClearResponse
from app.rag.vector_store import get_vector_store

router = APIRouter()


@router.delete(
    "/clear",
    response_model=ClearResponse,
    summary="清空知识库",
    description="删除向量库中所有已索引的文档片段，操作不可撤销。",
)
async def clear_knowledge_base():
    try:
        get_vector_store().clear()
        logger.info("[Admin] 知识库已清空")
        return ClearResponse(success=True, message="知识库已成功清空")
    except Exception as exc:
        logger.exception(f"[Admin] 清空知识库失败: {exc}")
        return ClearResponse(success=False, message=f"清空失败: {exc}")
