"""Web 客户端专用 WebSocket 端点"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.api.deps import get_web_manager, get_session_manager
from app.schemas.web_protocol import (
    WebClientMessage, WebServerMessage, WebClientMessageType, WebServerMessageType,
    UserMessagePayload, AITextStreamPayload, AIStatusPayload,
    ErrorPayload
)
from app.infrastructure.managers.web_connection import WebConnectionManager
from app.infrastructure.managers.session_manager import SessionManager
from app.services.agent_service import handle_user_message
from app.exceptions.base import GalateaException
from app.core.logger import get_logger
import json
import time
import uuid

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/ws/web")
async def web_websocket_endpoint(
    websocket: WebSocket,
    session_manager: SessionManager = Depends(get_session_manager),
    web_connection_manager: WebConnectionManager  = Depends(get_web_manager)
):
    """Web 客户端 WebSocket 连接端点"""
    await web_connection_manager.connect(websocket)
    connection_id = uuid.uuid4()
    logger.info(f"🌐 Web 客户端已连接 ( id: {connection_id} ))")
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                msg_dict = json.loads(data)
                msg = WebClientMessage(**msg_dict)
            except Exception as e:
                logger.error(f"Invalid message format: {e}")
                await send_error_message(websocket, web_connection_manager, 101, f"消息格式非法: {str(e)}")
                continue
            
            # 处理不同类型的消息
            if msg.type == WebClientMessageType.USER_MESSAGE:
                try:
                    # 使用生成器处理流式响应
                    async for response_msg in handle_user_message(msg.session_id, session_manager, msg):
                        await web_connection_manager.send_to_client(websocket, response_msg)
                    logger.info(f"✅ 完成处理用户消息 (会话: {msg.session_id})")
                except GalateaException as e:
                    # 捕获业务异常，转换成错误消息发送给客户端
                    logger.error(f"业务异常: {e.code} - {e.message}")
                    await send_error_message(websocket, web_connection_manager, e.code, e.message, e.details)
                except Exception as e:
                    # 捕获未知异常
                    logger.error(f"未知错误: {e}", exc_info=True)
                    await send_error_message(websocket, web_connection_manager, 100, f"系统内部错误: {str(e)}")
            
            elif msg.type == WebClientMessageType.HEARTBEAT:
                # 回应心跳
                await web_connection_manager.send_to_client(
                    websocket,
                    WebServerMessage(
                        type=WebServerMessageType.HEARTBEAT,
                        data={},
                        timestamp=time.time()
                    )
                )
    
    except WebSocketDisconnect:
        logger.info(f"🌐 Web 客户端断开连接 (会话: {connection_id})")
        web_connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Web WebSocket error: {e}", exc_info=True)
        web_connection_manager.disconnect(websocket)


async def send_error_message(
    websocket: WebSocket, 
    web_manager: WebConnectionManager, 
    code: int, 
    message: str, 
    details: dict = None
):
    """发送错误消息给 Web 客户端"""
    try:
        await web_manager.send_to_client(
            websocket,
            WebServerMessage(
                type=WebServerMessageType.ERROR,
                data=ErrorPayload(
                    code=code, 
                    message=message, 
                    details=details or {}
                ),
                timestamp=time.time()
            )
        )
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

