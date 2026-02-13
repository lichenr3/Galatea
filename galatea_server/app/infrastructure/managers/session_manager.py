"""
会话管理服务（精简版）
仅负责管理音频队列和会话 ↔ 角色的映射。
所有会话元数据（历史、时间戳、排序）由数据库负责。
"""
from typing import Dict, Optional
import asyncio
from app.core.logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """
    会话管理服务 — 仅管理音频队列与会话-角色映射

    职责：
    1. 维护 session_id → character_id 映射（供 TTS 等服务查角色）
    2. 维护每个会话的 asyncio.Queue（音频流缓冲）
    """

    def __init__(self):
        # session_id → character_id 映射
        self._sessions: Dict[str, str] = {}
        # 每个会话的音频队列（用于 TTS 流式播放）
        self.audio_queues: Dict[str, asyncio.Queue] = {}

        logger.info("✅ 会话管理服务已初始化")

    # ---- 会话注册 / 注销 ----

    def register_session(self, session_id: str, character_id: str) -> None:
        """注册会话（创建或恢复时调用）"""
        self._sessions[session_id] = character_id
        self.audio_queues[session_id] = asyncio.Queue(maxsize=10)
        logger.info(f"🆕 注册会话: {session_id} (角色: {character_id})")

    def unregister_session(self, session_id: str) -> None:
        """注销会话（删除时调用）"""
        character_id = self._sessions.pop(session_id, None)
        self.audio_queues.pop(session_id, None)
        if character_id:
            logger.info(f"🗑️ 注销会话: {session_id} (角色: {character_id})")

    # ---- 查询 ----

    def has_session(self, session_id: str) -> bool:
        """会话是否已注册"""
        return session_id in self._sessions

    def get_character_id(self, session_id: str) -> Optional[str]:
        """获取会话对应的角色 ID"""
        return self._sessions.get(session_id)

    def get_session_count(self) -> int:
        """获取当前已注册会话数"""
        return len(self._sessions)

    # ---- 音频队列 ----

    async def enqueue_audio(self, session_id: str, audio_data: bytes, timeout: float = 5.0) -> bool:
        """将音频数据加入会话队列（带超时控制）

        Args:
            session_id: 会话ID
            audio_data: 音频数据
            timeout: 超时时间（秒）

        Returns:
            bool: 是否成功入队
        """
        if session_id not in self.audio_queues:
            logger.warning(f"会话 {session_id} 不存在")
            return False

        try:
            await asyncio.wait_for(
                self.audio_queues[session_id].put(audio_data),
                timeout=timeout
            )
            return True
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ 音频队列已满，丢弃部分数据 (会话: {session_id})")
            return False
        except Exception as e:
            logger.error(f"❌ 音频入队失败: {e}")
            return False

    async def dequeue_audio(self, session_id: str, timeout: float = None) -> Optional[bytes]:
        """从会话队列中取出音频数据

        Args:
            session_id: 会话ID
            timeout: 超时时间（秒），None 表示无限等待

        Returns:
            Optional[bytes]: 音频数据，超时或出错返回 None
        """
        if session_id not in self.audio_queues:
            logger.warning(f"会话 {session_id} 不存在")
            return None

        try:
            if timeout is None:
                return await self.audio_queues[session_id].get()
            else:
                return await asyncio.wait_for(
                    self.audio_queues[session_id].get(),
                    timeout=timeout
                )
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"❌ 音频出队失败: {e}")
            return None

    def get_audio_queue_size(self, session_id: str) -> int:
        """获取音频队列大小"""
        if session_id not in self.audio_queues:
            return 0
        return self.audio_queues[session_id].qsize()
