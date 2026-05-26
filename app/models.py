"""
Pydantic 请求 / 响应模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# 上传接口
# ──────────────────────────────────────────────────────────────────────────────
class UploadResponse(BaseModel):
    success: bool
    message: str
    filename: str
    chunks_added: int


# ──────────────────────────────────────────────────────────────────────────────
# 对话接口
# ──────────────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str = Field(..., description="用户输入的问题或指令", min_length=1)
    session_id: Optional[str] = Field(None, description="会话 ID，为空时自动创建新会话")


class Citation(BaseModel):
    source: str = Field(..., description="文件名")
    page: int = Field(default=0, description="页码（从 1 开始）")
    chunk_id: str = Field(default="", description="文档片段 ID")
    text: str = Field(default="", description="引用文本摘要")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Agent 生成的回答")
    session_id: str = Field(..., description="当前会话 ID")
    citations: List[Citation] = Field(default=[], description="引用来源列表")
    tools_used: List[str] = Field(default=[], description="本次调用的工具名称")


# ──────────────────────────────────────────────────────────────────────────────
# 工具列表接口
# ──────────────────────────────────────────────────────────────────────────────
class ToolInfo(BaseModel):
    name: str
    description: str


class ToolsResponse(BaseModel):
    tools: List[ToolInfo]


# ──────────────────────────────────────────────────────────────────────────────
# 清空接口
# ──────────────────────────────────────────────────────────────────────────────
class ClearResponse(BaseModel):
    success: bool
    message: str
