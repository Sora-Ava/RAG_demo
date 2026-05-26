"""
LangGraph Agent 工作流编排
流程：
  用户输入
    ↓
  [agent 节点] LLM 判断是否需要工具
    ├─ 需要工具 → [tools 节点] 执行工具（含重试）→ 回到 agent
    └─ 不需要   → END，返回最终答案
支持 MemorySaver 多轮上下文记忆
"""
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger

from app.agent.state import AgentState
from app.agent.nodes import build_llm, make_agent_node, create_tool_node_with_retry
from app.tools.rag_tool import rag_search
from app.tools.weather_tool import weather_query
from app.tools.api_tool import http_request
from app.config import settings

# ──────────────────────────────────────────────────────────────────────────────
# 工具注册表（新增工具在此列表追加即可）
# ──────────────────────────────────────────────────────────────────────────────
ALL_TOOLS = [rag_search, weather_query, http_request]


def build_agent_graph():
    """
    构建并编译 LangGraph Agent 图。
    返回已编译的 CompiledGraph，可直接调用 .invoke() 或 .stream()。
    """
    logger.info("构建 LangGraph Agent 图...")

    # LLM 绑定工具（function calling）
    llm = build_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    # 节点函数
    agent_fn = make_agent_node(llm_with_tools)
    tool_fn = create_tool_node_with_retry(ALL_TOOLS, max_retries=settings.max_tool_retries)

    # ── 图定义 ────────────────────────────────────────────────────────────────
    graph = StateGraph(AgentState)

    # 节点注册
    graph.add_node("agent", agent_fn)
    graph.add_node("tools", tool_fn)

    # 入口
    graph.set_entry_point("agent")

    # 条件路由：agent → tools（有 tool_calls）或 END（无 tool_calls）
    graph.add_conditional_edges(
        "agent",
        tools_condition,           # langgraph.prebuilt 内置：检查 last message.tool_calls
        {"tools": "tools", END: END},
    )

    # tools → agent（工具执行完毕后回到 LLM 继续决策）
    graph.add_edge("tools", "agent")

    # ── 编译（附加内存检查点，支持多轮对话）───────────────────────────────────
    memory = MemorySaver()
    compiled = graph.compile(checkpointer=memory)

    logger.info("LangGraph Agent 图编译完成")
    return compiled


# ── 全局单例 ─────────────────────────────────────────────────────────────────
_agent_graph = None


def get_agent_graph():
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = build_agent_graph()
    return _agent_graph
