"""
会话管理服务
管理每个用户的对话历史和角色状态
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import asyncio
from app.utils.prompts import load_persona
from app.core.config import settings
from app.core.logger import get_logger
from app.infrastructure.managers.character_registry import CharacterRegistry

logger = get_logger(__name__)


@dataclass
class ChatSession:
    """聊天会话"""
    session_id: str
    character: str
    history: List[Dict[str, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str):
        """添加消息到历史"""
        self.history.append({"role": role, "content": content})
        self.last_active = datetime.now()
        
        # 滑动窗口：保持 System + 最近 20 条消息
        if len(self.history) > 21:
            self.history = [self.history[0]] + self.history[-20:]
    
    def get_messages(self) -> List[Dict[str, str]]:
        """获取当前会话的所有消息"""
        return self.history.copy()
    
    def clear_history(self, keep_system: bool = True):
        """清空历史记录"""
        if keep_system and self.history:
            self.history = [self.history[0]]  # 保留 system prompt
        else:
            self.history = []


class SessionManager:
    """
    会话管理服务
    
    两级排序结构：
    1. 角色层：按最近交互排序（最新交互的角色在前）
    2. 会话层：同一角色下的会话按最近交互排序
    """
    
    def __init__(self, character_registry: CharacterRegistry):
        # 存储所有会话（Dict 用于 O(1) 查找）
        self.sessions: Dict[str, ChatSession] = {}
        self.character_registry = character_registry
        
        # 角色的最近使用顺序（最新的在最前面 index=0）
        self.character_order: deque[str] = deque()
        
        # 每个角色下的会话列表（也按最近使用排序，最新的在前）
        self.character_sessions: Dict[str, deque[str]] = {}
        
        # 每个会话的音频队列（用于 TTS 流式播放）
        self.audio_queues: Dict[str, asyncio.Queue] = {}
        
        logger.info("✅ 会话管理服务已初始化")
    
    def create_session(
        self, 
        session_id: str,
        character_id: str,
        language: str = "zh"
    ) -> ChatSession:
        """
        创建新会话
        
        Args:
            session_id: 会话ID
            character_id: 角色ID
            language: 会话语言
        """
        # 加载角色人设
        persona = load_persona(character_id, self.character_registry, language=language)
        
        # 创建会话，初始化 system prompt
        session = ChatSession(
            session_id=session_id,
            character=character_id,
            history=[{"role": "system", "content": persona}]
        )
        
        self.sessions[session_id] = session
        
        # 创建该会话的音频队列
        self.audio_queues[session_id] = asyncio.Queue(maxsize=10)  # 限制队列大小，防止内存溢出
        
        # 确保该角色的会话列表存在
        if character_id not in self.character_sessions:
            self.character_sessions[character_id] = deque()
        
        # 新建会话自动添加到最前面（两级排序）
        self.move_to_front(session_id)
        
        logger.info(f"🆕 创建会话: {session_id} (角色: {character_id})")
        
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def get_or_create_session(
        self, 
        session_id: str, 
        character: Optional[str] = None
    ) -> ChatSession:
        """获取或创建会话"""
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id, character)
        return session
    
    def remove_session(self, session_id: str):
        """删除会话"""
        session = self.sessions.get(session_id)
        if not session:
            return
        
        character_id = session.character
        
        # 从会话字典中删除
        del self.sessions[session_id]
        
        # 清理音频队列
        if session_id in self.audio_queues:
            del self.audio_queues[session_id]
        
        # 从角色的会话列表中移除
        if character_id in self.character_sessions:
            if session_id in self.character_sessions[character_id]:
                self.character_sessions[character_id].remove(session_id)
            
            # 如果该角色没有会话了，从角色列表中移除
            if len(self.character_sessions[character_id]) == 0:
                del self.character_sessions[character_id]
                if character_id in self.character_order:
                    self.character_order.remove(character_id)
        
        logger.info(f"🗑️ 删除会话: {session_id} (角色: {character_id})")
    
    def get_session_count(self) -> int:
        """获取当前活跃会话数"""
        return len(self.sessions)
    
    def move_to_front(self, session_id: str):
        """
        将会话移到最前面（更新两级通讯录顺序）
        
        应该在业务逻辑层调用，例如：
        - 用户发送消息时
        - 用户切换到该会话时
        
        不应该在：
        - 仅查询历史记录时
        - 系统内部读取会话时
        """
        session = self.sessions.get(session_id)
        if not session:
            return
        
        character_id = session.character
        
        # 1. 将该角色移到角色列表的最前面
        if character_id in self.character_order:
            self.character_order.remove(character_id)
        self.character_order.appendleft(character_id)
        
        # 2. 将该会话移到该角色会话列表的最前面
        if character_id not in self.character_sessions:
            self.character_sessions[character_id] = deque()
        
        if session_id in self.character_sessions[character_id]:
            self.character_sessions[character_id].remove(session_id)
        self.character_sessions[character_id].appendleft(session_id)
        
        logger.debug(f"📌 会话 {session_id} (角色: {character_id}) 移到最前面")
    
    def get_recent_sessions(self, limit: Optional[int] = None) -> List[ChatSession]:
        """
        获取最近活跃的会话列表（按两级排序）
        
        返回结构：先按角色排序，再按会话排序
        例如：[角色A的会话1, 角色A的会话2, 角色B的会话1, ...]
        
        Args:
            limit: 返回的最大数量，None 表示返回全部
        """
        sessions = []
        count = 0
        
        for character_id in self.character_order:
            if limit and count >= limit:
                break
            
            # 获取该角色下的所有会话（已排序）
            session_ids = self.character_sessions.get(character_id, deque())
            for session_id in session_ids:
                if limit and count >= limit:
                    break
                
                session = self.sessions.get(session_id)
                if session:
                    sessions.append(session)
                    count += 1
        
        return sessions
    
    def get_contacts_grouped_by_character(self) -> Dict[str, List[ChatSession]]:
        """
        获取按角色分组的通讯录（用于前端显示）
        
        返回格式：
        {
            "character_id": [session1, session2, ...],  # 按最近交互排序
            ...
        }
        角色顺序也按最近交互排序
        """
        contacts = {}
        
        for character_id in self.character_order:
            session_ids = self.character_sessions.get(character_id, deque())
            character_sessions = []
            
            for session_id in session_ids:
                session = self.sessions.get(session_id)
                if session:
                    character_sessions.append(session)
            
            if character_sessions:
                contacts[character_id] = character_sessions
        
        return contacts
    
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
    
    # def cleanup_inactive_sessions(self, max_inactive_minutes: int = 30):
    #     """清理不活跃的会话"""
    #     now = datetime.now()
    #     to_remove = []
        
    #     for session_id, session in self.sessions.items():
    #         inactive_minutes = (now - session.last_active).total_seconds() / 60
    #         if inactive_minutes > max_inactive_minutes:
    #             to_remove.append(session_id)
        
    #     for session_id in to_remove:
    #         self.remove_session(session_id)
        
    #     if to_remove:
    #         logger.info(f"🧹 清理了 {len(to_remove)} 个不活跃会话")

