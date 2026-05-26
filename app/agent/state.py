"""
LangGraph Agent 状态定义
"""
from typing import Annotated, List, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    LangGraph 节点间传递的状态对象。

    messages:   对话消息列表，使用 add_messages reducer 自动追加
    session_id: 当前会话 ID（仅作标记，MemorySaver 通过 thread_id 隔离历史）
    citations:  本次 Agent 运行中从 RAG 工具提取的引用来源
    tools_used: 本次调用过的工具名称列表
    """
    messages: Annotated[List[Any], add_messages]
    session_id: str
    citations: List[Dict[str, Any]]
    tools_used: List[str]
