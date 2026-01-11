from fastapi import APIRouter
from app.api.v1.endpoints import web_websocket, unity_websocket, session, unity_client, tts

api_router = APIRouter()

# Web 前端 WebSocket 端点
api_router.include_router(web_websocket.router,tags=["web"])
# Unity 客户端 WebSocket 端点
api_router.include_router(unity_websocket.router,tags=["unity"])
# Unity 客户端管理端点
api_router.include_router(unity_client.router, prefix="/unity", tags=["unity"])
# 会话管理端点
api_router.include_router(session.router, prefix="/session", tags=["session"])
# TTS 模型管理端点
api_router.include_router(tts.router, prefix="/tts", tags=["tts"])