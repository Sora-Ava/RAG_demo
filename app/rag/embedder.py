"""
本地 BGE-small 嵌入模型封装

下载策略（按优先级）：
  1. ModelScope（魔搭社区，国内阿里云节点，必通）—— 首次启动自动下载
  2. 已下载的本地缓存（volume 持久化，重启后直接命中）
  3. 降级到 HuggingFace 官方源（海外环境）

模型缓存路径由环境变量 MODELSCOPE_CACHE 控制，默认 /app/models。
"""
import os
from pathlib import Path
from typing import List

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
from loguru import logger

from app.config import settings


def _resolve_model_path() -> str:
    """
    确定模型加载路径：
    - 优先使用 ModelScope 下载到本地的缓存目录
    - 若缓存不存在则触发 ModelScope 下载
    - 海外环境直接返回模型名，走 HuggingFace
    """
    model_name = settings.embedding_model_name          # e.g. BAAI/bge-small-zh-v1.5
    cache_root = Path(os.environ.get("MODELSCOPE_CACHE", "/app/models"))
    # ModelScope 本地缓存路径格式：{MODELSCOPE_CACHE}/hub/{namespace}/{model}
    local_path = cache_root / "hub" / model_name

    if local_path.exists() and any(local_path.iterdir()):
        logger.info(f"命中本地模型缓存: {local_path}")
        return str(local_path)

    # 尝试通过 ModelScope 下载
    try:
        logger.info(f"本地缓存未命中，通过 ModelScope 下载模型: {model_name}")
        from modelscope import snapshot_download          # 延迟导入，减少启动开销
        downloaded = snapshot_download(
            model_name,
            cache_dir=str(cache_root),
        )
        logger.info(f"ModelScope 下载完成: {downloaded}")
        return downloaded
    except Exception as ms_err:
        logger.warning(f"ModelScope 下载失败: {ms_err}，回退到 HuggingFace")

    # 最终回退：直接用模型名，让 sentence-transformers 自己从 HuggingFace 拉
    logger.info(f"使用 HuggingFace 源加载: {model_name}")
    return model_name


class BGEEmbeddings(Embeddings):
    """
    基于 BAAI/bge-small-zh-v1.5 的本地嵌入模型。
    首次使用通过 ModelScope 自动下载；之后从 volume 缓存加载（秒级）。
    """

    def __init__(self) -> None:
        model_path = _resolve_model_path()
        logger.info(f"加载嵌入模型: {model_path}  device={settings.embedding_device}")
        self._model = SentenceTransformer(
            model_path,
            device=settings.embedding_device,
        )
        logger.info("嵌入模型加载完成 ✓")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文档片段（BGE 建议开启 L2 归一化）"""
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """嵌入查询（BGE 加指令前缀效果更好）"""
        prefixed = f"为这个句子生成表示以用于检索相关文章：{text}"
        embedding = self._model.encode(
            [prefixed],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embedding[0].tolist()


# ── 全局单例（懒加载，不阻塞 FastAPI 启动）──────────────────────────────────────
_embedder: BGEEmbeddings | None = None


def get_embedder() -> BGEEmbeddings:
    global _embedder
    if _embedder is None:
        _embedder = BGEEmbeddings()
    return _embedder
