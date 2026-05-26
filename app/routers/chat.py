"""
POST /chat —— 多轮对话接口
支持:
- session_id 上下文记忆（基于 LangGraph MemorySaver）
- 工具自主调用（RAG / 天气 / 外部 API）
- 答案引用来源返回
"""
import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from loguru import logger

from app.agent.graph import get_agent_graph
from app.memory.session import session_manager
from app.models import ChatRequest, ChatResponse, Citation

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="多轮对话",
    description=(
        "发送消息并获取 Agent 回答。"
        "传入相同 session_id 可延续上下文；不传则自动创建新会话。"
    ),
)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    session_manager.touch(session_id)

    logger.info(f"[Chat] session={session_id}  msg={request.message[:80]!r}")

    # LangGraph 通过 thread_id 隔离多轮历史
    config = {"configurable": {"thread_id": session_id}}

    try:
        result = get_agent_graph().invoke(
            {
                "messages": [HumanMessage(content=request.message)],
                "session_id": session_id,
                "citations": [],
                "tools_used": [],
            },
            config=config,
        )
    except Exception as exc:
        logger.exception(f"[Chat] Agent 执行异常: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent 执行失败: {exc}",
        )

    # ── 提取最终 AI 回答（最后一条无 tool_calls 的 AIMessage）────────────────
    answer = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
            answer = msg.content
            break

    if not answer:
        answer = "抱歉，Agent 未能生成有效回答，请重试。"

    # ── 提取引用来源 ──────────────────────────────────────────────────────────
    raw_citations: List[dict] = result.get("citations", [])
    citations = [
        Citation(
            source=c.get("source", ""),
            page=int(c.get("page", 0)),
            chunk_id=c.get("chunk_id", ""),
            text=c.get("text", ""),
        )
        for c in raw_citations
    ]

    tools_used: List[str] = result.get("tools_used", [])

    logger.info(
        f"[Chat] 回答生成完毕，引用数={len(citations)}，工具={tools_used}"
    )

    return ChatResponse(
        answer=answer,
        session_id=session_id,
        citations=citations,
        tools_used=tools_used,
    )
