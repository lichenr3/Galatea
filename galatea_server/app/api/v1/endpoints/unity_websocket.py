"""Unity 客户端专用 WebSocket 端点"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.api.deps import get_unity_manager
from app.infrastructure.managers.unity_connection import UnityConnectionManager
from app.schemas.unity_protocol import (
    UnityBaseMessage, UnityMessageType,
    AnimationCompletePayload, StateUpdatePayload
)
from app.core.logger import get_logger
import json

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/ws/unity")
async def unity_websocket_endpoint(
    websocket: WebSocket,
    unity_connection_manager: UnityConnectionManager = Depends(get_unity_manager)
):
    """Unity 客户端 WebSocket 连接端点"""
    await unity_connection_manager.connect(websocket)
    logger.info("🎮 Unity client connected to /ws/unity")
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                msg_dict = json.loads(data)
                msg = UnityBaseMessage(**msg_dict)
            except Exception as e:
                logger.error(f"Invalid Unity message format: {e}")
                continue
            
            # 处理 Unity 发送的反馈消息
            if msg.type == UnityMessageType.ANIMATION_COMPLETE:
                await handle_animation_complete(msg)
            
            elif msg.type == UnityMessageType.STATE_UPDATE:
                await handle_state_update(msg)
            
            elif msg.type == UnityMessageType.HEARTBEAT:
                # 心跳回应（可选）
                logger.debug("💓 Unity heartbeat received")
    
    except WebSocketDisconnect:
        logger.info("🎮 Unity client disconnected normally")
        unity_connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Unity WebSocket error: {e}", exc_info=True)
        unity_connection_manager.disconnect(websocket)


async def handle_animation_complete(msg: UnityBaseMessage):
    """处理动画完成反馈"""
    try:
        payload = AnimationCompletePayload(**msg.data)
        
        if payload.success:
            logger.info(f"🎬 Animation completed: {payload.animation_name}")
        else:
            logger.warning(
                f"⚠️ Animation failed: {payload.animation_name} - {payload.error_message}"
            )
    except Exception as e:
        logger.error(f"Error handling animation complete: {e}")


async def handle_state_update(msg: UnityBaseMessage):
    """处理状态更新反馈"""
    try:
        payload = StateUpdatePayload(**msg.data)
        
        logger.debug(
            f"🎮 Unity State - Animation: {payload.current_animation}, "
            f"Expression: {payload.current_expression}, "
            f"Busy: {payload.is_busy}"
        )
        
        # 这里可以根据 Unity 的状态做一些逻辑处理
        # 例如：如果 Unity 忙碌，可以暂停发送新指令
        
    except Exception as e:
        logger.error(f"Error handling state update: {e}")

