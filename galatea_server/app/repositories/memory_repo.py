"""
Memory Repository — 记忆表的数据访问层

当前为占位实现，向量记忆功能将在 LangGraph 阶段完善。
"""
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.core.logger import get_logger

logger = get_logger(__name__)


class MemoryRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._sf = session_factory

    # TODO: 后续实现
    # async def save(self, character_id, content, embedding, ...) -> None
    # async def search_similar(self, character_id, query_embedding, top_k) -> list
    # async def get_important_facts(self, character_id, min_importance) -> list
