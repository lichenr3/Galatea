"""
Message Repository — 消息表的数据访问层
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.models.message import DBMessage
from app.core.logger import get_logger

logger = get_logger(__name__)


class MessageRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._sf = session_factory

    async def save(self, session_id: int, role: str, content: str) -> None:
        """保存一条消息"""
        async with self._sf() as session:
            message = DBMessage(
                session_id=session_id,
                role=role,
                content=content,
            )
            session.add(message)
            await session.commit()

    async def get_by_session(self, session_id: int) -> list[DBMessage]:
        """获取某个会话的全部消息（按时间正序）"""
        async with self._sf() as session:
            result = await session.execute(
                select(DBMessage)
                .where(DBMessage.session_id == session_id)
                .order_by(DBMessage.created_at.asc())
            )
            return list(result.scalars().all())

    async def count_by_session(self, session_id: int) -> int:
        """获取某个会话的消息数量（不含 system prompt）"""
        async with self._sf() as session:
            result = await session.execute(
                select(func.count())
                .select_from(DBMessage)
                .where(DBMessage.session_id == session_id, DBMessage.role != "system")
            )
            return result.scalar_one()

    async def get_recent_with_system(self, session_id: int, limit: int = 20) -> list[DBMessage]:
        """
        获取 system prompt + 最近 N 条非 system 消息。
        用于恢复内存中的滑动窗口。
        """
        async with self._sf() as session:
            # 1. 取 system message
            system_result = await session.execute(
                select(DBMessage)
                .where(DBMessage.session_id == session_id, DBMessage.role == "system")
                .order_by(DBMessage.created_at.asc())
                .limit(1)
            )
            system_msg = system_result.scalar_one_or_none()

            # 2. 取最近 N 条非 system 消息（倒序取再反转）
            recent_result = await session.execute(
                select(DBMessage)
                .where(DBMessage.session_id == session_id, DBMessage.role != "system")
                .order_by(DBMessage.created_at.desc())
                .limit(limit)
            )
            recent_msgs = list(reversed(recent_result.scalars().all()))

            # 3. 拼接：system + recent
            messages = []
            if system_msg:
                messages.append(system_msg)
            messages.extend(recent_msgs)
            return messages

    async def get_last_message(self, session_id: int) -> DBMessage | None:
        """获取会话的最后一条非 system 消息"""
        async with self._sf() as session:
            result = await session.execute(
                select(DBMessage)
                .where(DBMessage.session_id == session_id, DBMessage.role != "system")
                .order_by(DBMessage.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()
