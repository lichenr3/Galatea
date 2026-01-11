"""
Galatea Server - AI Desktop Pet Backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

主应用入口，负责：
- FastAPI 应用初始化
- 中间件配置
- 路由注册
- 静态文件服务
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.events import lifespan
from app.core.config import settings
from app.core.logger import get_logger
from app.core.startup import print_startup_banner, print_available_endpoints
from app.core.static_files import mount_static_files
from app.core.exception_handler import register_exception_handlers
from app.api.v1.api_router import api_router
from app.core.container import tts_server

logger = get_logger(__name__)

# ==================== 应用初始化 ====================

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI Desktop Pet Backend Service with WebSocket support",
    version="1.0.0",
    lifespan=lifespan  # TODO: 启用生命周期管理
)

# ==================== 中间件配置 ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源，生产环境改为 settings.CORS_ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 异常处理 ====================

register_exception_handlers(app)

# ==================== 路由注册 ====================

app.include_router(api_router, prefix=settings.API_V1_STR)

# ==================== 静态文件服务 ====================

mount_static_files(app)

# ==================== 健康检查端点 ====================

@app.get("/", tags=["Health"])
def health_check():
    """服务健康检查"""
    return {
        "status": "running",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "tts_status": "running" if tts_server.is_running() else "stopped"
    }

@app.get("/ping", tags=["Health"])
def ping():
    """简单的 Ping/Pong 测试"""
    return {"message": "pong"}

# ==================== 启动事件 ====================

@app.on_event("startup")
async def on_startup():
    """应用启动时执行"""
    print_startup_banner()
    logger.info("✅ Galatea Server 启动成功")
    print_available_endpoints()

@app.on_event("shutdown")
async def on_shutdown():
    """应用关闭时执行"""
    logger.info("👋 Galatea Server 正在关闭...")
    # TODO: 清理资源（如关闭 TTS 进程）
