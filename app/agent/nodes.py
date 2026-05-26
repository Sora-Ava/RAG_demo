"""
LangGraph 节点实现
- agent_node:                LLM 决策节点（是否需要工具）
- create_tool_node_with_retry: 带重试的工具执行节点工厂
"""
import json
import time
from typing import List, Dict, Any

from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from loguru import logger

from app.agent.state import AgentState
from app.config import settings

# RAG 工具输出中引用标记（与 rag_tool.py 保持一致）
_CITATION_MARKER = "[CITATIONS_JSON]:"


# ──────────────────────────────────────────────────────────────────────────────
# LLM 单例
# ──────────────────────────────────────────────────────────────────────────────

def build_llm() -> ChatOpenAI:
    """构建 OpenAI 兼容的 LLM 实例"""
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0.1,  # 低随机性，保证工具调用准确
        streaming=False,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Agent 节点：LLM 决策
# ──────────────────────────────────────────────────────────────────────────────

def make_agent_node(llm_with_tools):
    """
    返回绑定了工具的 agent 节点函数。
    LLM 根据对话历史自主决定：直接回答 或 调用某个工具。
    """
    def agent_node(state: AgentState) -> Dict[str, Any]:
        logger.debug(f"[Agent] 调用 LLM，消息数: {len(state['messages'])}")
        response: AIMessage = llm_with_tools.invoke(state["messages"])
        logger.debug(f"[Agent] LLM 响应: tool_calls={bool(response.tool_calls)}")
        return {"messages": [response]}

    return agent_node


# ──────────────────────────────────────────────────────────────────────────────
# 工具节点：带重试执行
# ──────────────────────────────────────────────────────────────────────────────

def create_tool_node_with_retry(tools: list, max_retries: int = None):
    """
    工厂函数：返回带自动重试逻辑的工具执行节点。

    参数:
        tools:       工具列表（@tool 装饰的函数）
        max_retries: 最大重试次数（默认读取 settings.max_tool_retries）
    """
    max_retries = max_retries if max_retries is not None else settings.max_tool_retries
    tools_by_name: Dict[str, Any] = {t.name: t for t in tools}

    def tool_node(state: AgentState) -> Dict[str, Any]:
        last_message: AIMessage = state["messages"][-1]
        tool_messages: List[ToolMessage] = []
        all_citations: List[Dict] = []
        tools_used: List[str] = list(state.get("tools_used", []))

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]

            tool_fn = tools_by_name.get(tool_name)
            if tool_fn is None:
                tool_messages.append(ToolMessage(
                    content=f"未找到工具: {tool_name}",
                    tool_call_id=tool_call_id,
                    name=tool_name,
                ))
                continue

            # ── 重试执行 ─────────────────────────────────────────────────────
            result_content: str | None = None
            last_error: str = ""
            for attempt in range(max_retries + 1):
                try:
                    raw = tool_fn.invoke(tool_args)
                    result_content = str(raw) if not isinstance(raw, str) else raw
                    break
                except Exception as exc:
                    last_error = str(exc)
                    if attempt < max_retries:
                        wait = 0.5 * (attempt + 1)
                        logger.warning(
                            f"[Tool] {tool_name} 执行失败（第 {attempt + 1} 次）: {exc}，"
                            f"{wait}s 后重试..."
                        )
                        time.sleep(wait)
                    else:
                        logger.error(
                            f"[Tool] {tool_name} 已重试 {max_retries} 次，最终失败: {exc}"
                        )

            if result_content is None:
                result_content = (
                    f"⚠️ 工具 [{tool_name}] 调用失败（已重试 {max_retries} 次）。\n"
                    f"错误信息: {last_error}\n"
                    f"请稍后再试，或换一种方式提问。"
                )
            else:
                # ── 从 RAG 工具响应中提取 citations ───────────────────────
                if tool_name == "rag_search" and _CITATION_MARKER in result_content:
                    parts = result_content.split(_CITATION_MARKER, 1)
                    result_content = parts[0].strip()  # 去掉 JSON 尾部给 LLM 看
                    try:
                        citations = json.loads(parts[1].strip())
                        all_citations.extend(citations)
                    except json.JSONDecodeError:
                        logger.warning("[Tool] 解析 RAG citations JSON 失败")

            if tool_name not in tools_used:
                tools_used.append(tool_name)

            logger.info(f"[Tool] {tool_name} 执行成功，结果长度: {len(result_content)}")
            tool_messages.append(ToolMessage(
                content=result_content,
                tool_call_id=tool_call_id,
                name=tool_name,
            ))

        return {
            "messages": tool_messages,
            "citations": all_citations,
            "tools_used": tools_used,
        }

    return tool_node
