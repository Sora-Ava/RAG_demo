"""
会话管理器 —— 跟踪活跃 session_id 列表
（实际消息历史由 LangGraph MemorySaver 存储，此模块仅做辅助元数据管理）
"""
import time
from typing import Dict, Optional
from loguru import logger


class SessionManager:
    """
    轻量级会话元数据管理：
    - 记录 session_id 创建时间、最后活跃时间、消息轮数
    - 提供会话清理（超时 TTL）
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._sessions: Dict[str, dict] = {}
        self._ttl = ttl_seconds

    def touch(self, session_id: str) -> None:
        """创建或刷新会话记录"""
        now = time.time()
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "created_at": now,
                "last_active": now,
                "turns": 0,
            }
            logger.info(f"[Session] 新建会话: {session_id}")
        else:
            self._sessions[session_id]["last_active"] = now
            self._sessions[session_id]["turns"] += 1

    def get_info(self, session_id: str) -> Optional[dict]:
        """获取会话元数据，不存在返回 None"""
        return self._sessions.get(session_id)

    def list_sessions(self) -> list:
        """返回所有活跃会话列表"""
        self._cleanup_expired()
        return [
            {"session_id": sid, **info}
            for sid, info in self._sessions.items()
        ]

    def _cleanup_expired(self) -> None:
        """清理超时会话"""
        now = time.time()
        expired = [
            sid for sid, info in self._sessions.items()
            if now - info["last_active"] > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]
            logger.debug(f"[Session] 会话超时清理: {sid}")

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False


# 全局单例
session_manager = SessionManager()
