"""Web 客户端连接管理服务"""
from fastapi import WebSocket
from typing import Set
from app.schemas.web_protocol import WebServerMessage
from app.core.logger import get_logger

logger = get_logger(__name__)


class WebConnectionManager:
    """管理所有 Web 客户端的连接"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """接受新的 Web 客户端连接"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"✅ Web Client Connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """断开 Web 客户端连接"""
        self.active_connections.discard(websocket)
        logger.info(f"❌ Web Client Disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: WebServerMessage):
        """广播消息给所有 Web 客户端"""
        disconnected = set()
        
        for ws in self.active_connections:
            try:
                await ws.send_text(message.model_dump_json())
            except Exception as e:
                logger.error(f"Failed to send to web client: {e}")
                disconnected.add(ws)
        
        # 清理断开的连接
        for ws in disconnected:
            self.disconnect(ws)
    
    async def send_to_client(self, websocket: WebSocket, message: WebServerMessage):
        """发送消息给指定的 Web 客户端"""
        try:
            await websocket.send_text(message.model_dump_json())
        except Exception as e:
            logger.error(f"Failed to send to web client: {e}")
            self.disconnect(websocket)
            raise
    
    @property
    def connection_count(self) -> int:
        """返回当前活跃连接数"""
        return len(self.active_connections)
    
    @property
    def has_active_client(self) -> bool:
        """检查是否有活跃的 Web 客户端"""
        return len(self.active_connections) > 0