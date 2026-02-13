from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.deps import init_dependencies, shutdown_dependencies, get_tts_server
from app.core.logger import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup: 初始化所有依赖（数据库、服务、从 DB 恢复会话）---
    await init_dependencies()
    get_tts_server().start()
    
    yield
    
    # --- Shutdown ---
    get_tts_server().stop()
    await shutdown_dependencies()
