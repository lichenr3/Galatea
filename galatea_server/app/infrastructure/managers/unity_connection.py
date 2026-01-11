"""Unity 客户端连接管理服务"""
from fastapi import WebSocket
from typing import Set, Optional
from app.schemas.unity_protocol import (
    UnityBaseMessage, UnityMessageType, SwitchCharacterPayload
)
from app.core.logger import get_logger
import time

logger = get_logger(__name__)


class UnityConnectionManager:
    """管理所有 Unity 客户端的连接"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.pending_character_id: Optional[str] = None  # 待切换的角色 ID
    
    async def connect(self, websocket: WebSocket):
        """接受新的 Unity 客户端连接"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"✅ Unity Client Connected. Total: {len(self.active_connections)}")
        
        # 如果有待加载的角色，立即发送切换角色消息
        if self.pending_character_id:
            logger.info(f"🎭 检测到待加载角色: {self.pending_character_id}，立即发送切换指令")
            await self.notify_character_switch(self.pending_character_id)
            self.pending_character_id = None  # 清除标记
            logger.info("✅ 角色切换指令已发送，清除待加载标记")
        else:
            logger.info("ℹ️ 没有待加载角色，Unity 保持空白状态")
    
    def disconnect(self, websocket: WebSocket):
        """断开 Unity 客户端连接"""
        self.active_connections.discard(websocket)
        logger.info(f"❌ Unity Client Disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: UnityBaseMessage):
        """广播消息给所有 Unity 客户端（通常只有一个）"""
        disconnected = set()
        
        for ws in self.active_connections:
            try:
                await ws.send_text(message.model_dump_json())
            except Exception as e:
                logger.error(f"Failed to send to unity client: {e}")
                disconnected.add(ws)
        
        # 清理断开的连接
        for ws in disconnected:
            self.disconnect(ws)
    
    async def send_command(self, message: UnityBaseMessage):
        """发送指令给 Unity（如果有多个实例，发给所有）"""
        if not self.has_active_client:
            logger.warning("No active Unity client to send command to")
            return
        
        await self.broadcast(message)
        logger.debug(f"📤 Sent command to Unity: {message.type}")
    
    @property
    def has_active_client(self) -> bool:
        """检查是否有活跃的 Unity 客户端"""
        return len(self.active_connections) > 0
    
    @property
    def connection_count(self) -> int:
        """返回当前活跃连接数"""
        return len(self.active_connections)
    
    async def notify_character_switch(self, character_id: str):
        """通知Unity切换角色"""
        if not self.has_active_client:
            logger.warning("⚠️ 没有活跃的Unity连接，无法切换角色")
            return
        
        message = UnityBaseMessage(
            type=UnityMessageType.SWITCH_CHARACTER,
            data=SwitchCharacterPayload(character_id=character_id).model_dump(),
            timestamp=time.time()
        )
        
        await self.broadcast(message)
        logger.info(f"🎭 已通知Unity切换到角色: {character_id}")
