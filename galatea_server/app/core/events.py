from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.container import tts_server, checkpointer_manager
from app.core.logger import get_logger
from app.models.base import init_db, close_db

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("🚀 应用启动中...")
    
    # 初始化数据库
    try:
        await init_db()
        logger.info("✅ 数据库初始化完成")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        # 数据库失败不阻止启动，允许降级运行
    
    # 启动 TTS 服务
    tts_server.start()
    
    logger.info("✅ 应用启动完成")
    
    yield
    
    # --- Shutdown ---
    logger.info("🛑 应用关闭中...")
    
    # 关闭 TTS 服务
    tts_server.stop()
    
    # 关闭 Checkpointer 连接池
    await checkpointer_manager.close()
    
    # 关闭数据库连接
    await close_db()
    
    logger.info("✅ 应用已关闭")
