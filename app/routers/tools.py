"""
GET /tools —— 返回 Agent 当前支持的工具列表
"""
from fastapi import APIRouter

from app.models import ToolInfo, ToolsResponse
from app.agent.graph import ALL_TOOLS

router = APIRouter()


@router.get(
    "/tools",
    response_model=ToolsResponse,
    summary="查询 Agent 支持的工具列表",
    description="返回当前 Agent 可调用的所有工具的名称与功能描述。",
)
async def list_tools():
    tools = [
        ToolInfo(
            name=t.name,
            description=(t.description or "").strip(),
        )
        for t in ALL_TOOLS
    ]
    return ToolsResponse(tools=tools)
