from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.container import session_manager, web_manager, unity_manager, character_registry
from app.models.base import async_session_factory
from app.crud import SessionCRUD, MessageCRUD

# ============================================================
# Infrastructure 依赖
# ============================================================
def get_session_manager():
    return session_manager

def get_web_manager():
    return web_manager

def get_unity_manager():
    return unity_manager

def get_character_registry():
    return character_registry


# ============================================================
# Database 依赖
# ============================================================
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session_crud() -> AsyncGenerator[SessionCRUD, None]:
    """获取 Session CRUD"""
    async with async_session_factory() as session:
        try:
            yield SessionCRUD(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_message_crud() -> AsyncGenerator[MessageCRUD, None]:
    """获取 Message CRUD"""
    async with async_session_factory() as session:
        try:
            yield MessageCRUD(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
