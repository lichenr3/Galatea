"""
Session Repository — 会话表的数据访问层
"""
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from datetime import datetime
from app.models.session import DBSession
from app.core.logger import get_logger

logger = get_logger(__name__)


class SessionRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._sf = session_factory

    async def create(self, character_id: str) -> int:
        """创建会话记录，返回自增 ID"""
        async with self._sf() as session:
            db_session = DBSession(
                character_id=character_id,
            )
            session.add(db_session)
            await session.flush()  # flush 后拿到自增 ID
            new_id = db_session.id
            await session.commit()
        logger.debug(f"💾 Session persisted: {new_id}")
        return new_id

    async def delete(self, session_id: int) -> None:
        """删除会话（消息通过 CASCADE 自动删除）"""
        async with self._sf() as session:
            await session.execute(
                delete(DBSession).where(DBSession.id == session_id)
            )
            await session.commit()
        logger.debug(f"💾 Session deleted: {session_id}")

    async def update_last_active(self, session_id: int) -> None:
        """更新会话的最后活跃时间"""
        async with self._sf() as session:
            await session.execute(
                update(DBSession)
                .where(DBSession.id == session_id)
                .values(last_active=datetime.now())
            )
            await session.commit()

    async def get_character_id(self, session_id: int) -> str | None:
        """根据会话 ID 获取角色 ID，不存在返回 None"""
        async with self._sf() as session:
            result = await session.execute(
                select(DBSession.character_id).where(DBSession.id == session_id)
            )
            return result.scalar_one_or_none()

    async def get_all_ordered(self) -> list[DBSession]:
        """
        获取所有会话，按 last_active 降序排列（最近的在前）。
        用于 app 启动时恢复内存状态。
        """
        async with self._sf() as session:
            result = await session.execute(
                select(DBSession).order_by(DBSession.last_active.desc())
            )
            return list(result.scalars().all())
