"""
FastAPI 应用入口
启动: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
文档: http://localhost:8000/docs
"""
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

from app.config import settings
from app.routers import upload, chat, tools, admin

# ──────────────────────────────────────────────────────────────────────────────
# 日志配置
# ──────────────────────────────────────────────────────────────────────────────
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
)
logger.add(
    "/app/data/app.log",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
    encoding="utf-8",
)

# ──────────────────────────────────────────────────────────────────────────────
# FastAPI 应用
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="企业 RAG 知识库 + 多工具 Agent",
    description=(
        "基于 LangGraph + Chroma + BGE-small 的企业级智能知识库系统。\n\n"
        "**功能亮点**\n"
        "- 上传 PDF/Word/TXT → 自动向量化入库\n"
        "- LangGraph Agent 自主决策调用工具（RAG / 天气 / HTTP）\n"
        "- 多轮对话记忆（session_id）\n"
        "- 答案附带原文引用来源"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS（开发阶段允许所有来源，生产按需收紧）──────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 路由注册 ───────────────────────────────────────────────────────────────────
app.include_router(upload.router, tags=["📄 文档上传"])
app.include_router(chat.router, tags=["💬 对话"])
app.include_router(tools.router, tags=["🔧 工具"])
app.include_router(admin.router, tags=["⚙️ 管理"])

# ── 静态文件（前端页面）──────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ──────────────────────────────────────────────────────────────────────────────
# 启动事件：预热模型，避免第一次请求超时
# ──────────────────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("企业 RAG + Agent 系统启动中...")
    logger.info(f"LLM 模型: {settings.openai_model}  BaseURL: {settings.openai_base_url}")
    logger.info(f"嵌入模型: {settings.embedding_model_name}")

    # 确保数据目录存在
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    os.makedirs(settings.upload_dir, exist_ok=True)

    # 预热嵌入模型 + 向量库
    from app.rag.vector_store import get_vector_store
    vs = get_vector_store()
    logger.info(f"向量库就绪，当前片段数: {vs.count()}")

    # 预热 Agent 图
    from app.agent.graph import get_agent_graph
    get_agent_graph()

    logger.info("系统启动完成，访问 /docs 查看接口文档")
    logger.info("=" * 60)


@app.get("/", include_in_schema=False)
async def root():
    """根路由：返回前端页面"""
    return FileResponse("app/static/index.html")


@app.get("/health", tags=["⚙️ 管理"], summary="健康检查")
async def health():
    from app.rag.vector_store import get_vector_store
    return {
        "status": "ok",
        "knowledge_base_chunks": get_vector_store().count(),
    }
