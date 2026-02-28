"""
Memory Repository — 记忆表的数据访问层
==============================================

提供向量记忆的 CRUD 操作：
- save(): 保存单条记忆（含 embedding）
- get_by_character(): 获取角色的已有记忆（用于提取时去重）
- search_similar(): 向量相似度检索
- update_memory(): 更新记忆内容
- update_last_accessed(): 更新访问时间（用于 LRU 淘汰）
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.models.memory import DBMemory
from app.core.logger import get_logger

logger = get_logger(__name__)


class MemoryRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._sf = session_factory

    async def save(
        self,
        character_id: str,
        content: str,
        embedding: list[float],
        session_id: Optional[int] = None,
        summary: Optional[str] = None,
        memory_type: str = "conversation",
        importance: int = 5,
    ) -> int:
        """
        保存单条记忆，返回自增 ID
        """
        async with self._sf() as session:
            memory = DBMemory(
                character_id=character_id,
                session_id=session_id,
                content=content,
                summary=summary or content,
                embedding=embedding,
                memory_type=memory_type,
                importance=importance,
            )
            session.add(memory)
            await session.flush()
            new_id = memory.id
            await session.commit()
        logger.debug(f"💾 Memory saved: id={new_id}, type={memory_type}")
        return new_id

    async def get_by_character(
        self,
        character_id: str,
        limit: int = 30,
        min_importance: int = 1,
    ) -> list[DBMemory]:
        """
        获取角色的已有记忆（按 importance 降序，用于提取时去重）
        """
        async with self._sf() as session:
            result = await session.execute(
                select(DBMemory)
                .where(
                    DBMemory.character_id == character_id,
                    DBMemory.importance >= min_importance,
                )
                .order_by(DBMemory.importance.desc(), DBMemory.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def search_similar(
        self,
        character_id: str,
        query_embedding: list[float],
        top_k: int = 5,
        min_importance: int = 3,
        max_distance: float = 0.5,
    ) -> list[DBMemory]:
        """
        向量相似度检索（使用余弦距离 <=>）
        max_distance 控制过滤阈值，余弦距离越小越相似 (通常小于 0.5 认为有相关性)
        """
        async with self._sf() as session:
            result = await session.execute(
                select(DBMemory)
                .where(
                    DBMemory.character_id == character_id,
                    DBMemory.importance >= min_importance,
                    DBMemory.embedding.isnot(None),
                    DBMemory.embedding.cosine_distance(query_embedding) < max_distance,
                )
                .order_by(DBMemory.embedding.cosine_distance(query_embedding))
                .limit(top_k)
            )
            return list(result.scalars().all())

    async def update_memory(
        self,
        memory_id: int,
        content: str,
        embedding: list[float],
        summary: Optional[str] = None,
        importance: Optional[int] = None,
    ) -> bool:
        """
        更新记忆内容，返回是否成功
        """
        async with self._sf() as session:
            values = {
                "content": content,
                "summary": summary or content,
                "embedding": embedding,
            }
            if importance is not None:
                values["importance"] = importance

            result = await session.execute(
                update(DBMemory)
                .where(DBMemory.id == memory_id)
                .values(**values)
            )
            await session.commit()
            success = result.rowcount > 0
        if success:
            logger.debug(f"💾 Memory updated: id={memory_id}")
        return success

    async def update_last_accessed(self, memory_ids: list[int]) -> None:
        """
        批量更新记忆的最后访问时间
        """
        if not memory_ids:
            return
        async with self._sf() as session:
            await session.execute(
                update(DBMemory)
                .where(DBMemory.id.in_(memory_ids))
                .values(last_accessed=datetime.now())
            )
            await session.commit()
        logger.debug(f"💾 Memory accessed: {len(memory_ids)} items")

    async def delete_by_session(self, session_id: int) -> int:
        """
        删除与某会话关联的记忆（返回删除数量）
        """
        async with self._sf() as session:
            result = await session.execute(
                delete(DBMemory).where(DBMemory.session_id == session_id)
            )
            await session.commit()
            count = result.rowcount
        logger.debug(f"💾 Memories deleted for session {session_id}: {count}")
        return count

    async def get_count(self, character_id: str) -> int:
        """
        获取角色的记忆总数
        """
        async with self._sf() as session:
            result = await session.execute(
                select(func.count())
                .select_from(DBMemory)
                .where(DBMemory.character_id == character_id)
            )
            return result.scalar_one()
