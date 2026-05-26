"""
统一配置管理 —— 所有参数从环境变量 / .env 文件读取
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── LLM ───────────────────────────────────────────────────────────────────
    openai_api_key: str = Field(default="sk-placeholder", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-3.5-turbo", alias="OPENAI_MODEL")

    # ── 嵌入模型 ──────────────────────────────────────────────────────────────
    embedding_model_name: str = Field(
        default="BAAI/bge-small-zh-v1.5", alias="EMBEDDING_MODEL_NAME"
    )
    embedding_device: str = Field(default="cpu", alias="EMBEDDING_DEVICE")

    # ── 向量库 ────────────────────────────────────────────────────────────────
    chroma_persist_dir: str = Field(default="/app/data/chroma", alias="CHROMA_PERSIST_DIR")
    chroma_collection_name: str = Field(default="enterprise_kb", alias="CHROMA_COLLECTION_NAME")

    # ── RAG ───────────────────────────────────────────────────────────────────
    chunk_size: int = Field(default=500, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, alias="CHUNK_OVERLAP")
    top_k: int = Field(default=5, alias="TOP_K")

    # ── 文件上传 ──────────────────────────────────────────────────────────────
    upload_dir: str = Field(default="/app/data/uploads", alias="UPLOAD_DIR")
    max_file_size: int = Field(default=50 * 1024 * 1024, alias="MAX_FILE_SIZE")

    # ── Agent ─────────────────────────────────────────────────────────────────
    max_tool_retries: int = Field(default=2, alias="MAX_TOOL_RETRIES")

    # ── 服务器 ────────────────────────────────────────────────────────────────
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # ── 会话 ──────────────────────────────────────────────────────────────────
    session_max_history: int = Field(default=20, alias="SESSION_MAX_HISTORY")

    model_config = {"env_file": ".env", "populate_by_name": True}


# 全局单例
settings = Settings()
