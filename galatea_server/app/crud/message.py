"""
Message CRUD

消息数据的 CRUD 操作。
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import BaseCRUD
from app.models.message import Message


class MessageCRUD(BaseCRUD[Message]):
    """
    消息 CRUD
    
    提供消息相关的数据库操作。
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(Message, session)
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_call_id: Optional[str] = None
    ) -> Message:
        """添加消息"""
        return await self.create(
            session_id=session_id,
            role=role,
            content=content,
            message_id=message_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id
        )
    
    async def get_messages_by_session(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Message]:
        """获取会话的所有消息"""
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
        )
        if limit:
            stmt = stmt.limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_recent_messages(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Message]:
        """
        获取会话的最近 N 条消息
        
        用于构建 LLM 上下文（滑动窗口）。
        """
        # 先获取最近的消息（倒序）
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        
        # 反转为正序
        return list(reversed(messages))
    
    async def get_messages_with_system(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Message]:
        """
        获取系统消息 + 最近的用户/助手消息
        
        保持 System Prompt + 滑动窗口。
        """
        # 获取 system 消息
        system_stmt = (
            select(Message)
            .where(and_(
                Message.session_id == session_id,
                Message.role == "system"
            ))
            .order_by(Message.created_at.asc())
            .limit(1)
        )
        system_result = await self.session.execute(system_stmt)
        system_messages = list(system_result.scalars().all())
        
        # 获取非 system 的最近消息
        recent_stmt = (
            select(Message)
            .where(and_(
                Message.session_id == session_id,
                Message.role != "system"
            ))
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        recent_result = await self.session.execute(recent_stmt)
        recent_messages = list(reversed(list(recent_result.scalars().all())))
        
        return system_messages + recent_messages
    
    async def get_message_count(self, session_id: str) -> int:
        """获取会话的消息数量"""
        stmt = (
            select(func.count(Message.id))
            .where(Message.session_id == session_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def delete_messages_by_session(self, session_id: str) -> int:
        """删除会话的所有消息"""
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        
        count = len(messages)
        for msg in messages:
            await self.session.delete(msg)
        
        await self.session.flush()
        return count
    
    async def to_langchain_messages(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[dict]:
        """
        获取消息并转换为 LangChain 格式
        
        返回格式：[{"role": "user", "content": "..."}]
        """
        messages = await self.get_messages_with_system(session_id, limit)
        return [msg.to_langchain_format() for msg in messages]
