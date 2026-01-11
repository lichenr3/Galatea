from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.container import tts_server
from app.core.logger import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    tts_server.start()
    
    yield
    
    # --- Shutdown ---
    tts_server.stop()
