"""
Session CRUD

会话数据的 CRUD 操作。
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import BaseCRUD
from app.models.session import Session


class SessionCRUD(BaseCRUD[Session]):
    """
    会话 CRUD
    
    提供会话相关的数据库操作。
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(Session, session)
    
    async def create_session(
        self,
        session_id: str,
        character_id: str,
        language: str = "zh",
        enable_audio: bool = True,
        title: Optional[str] = None
    ) -> Session:
        """创建新会话"""
        return await self.create(
            id=session_id,
            character_id=character_id,
            language=language,
            enable_audio=enable_audio,
            title=title
        )
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话（不包含消息）"""
        return await self.get_by_id(session_id)
    
    async def get_session_with_messages(self, session_id: str) -> Optional[Session]:
        """获取会话（包含消息）"""
        stmt = (
            select(Session)
            .options(selectinload(Session.messages))
            .where(Session.id == session_id)
            .where(Session.is_deleted == False)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_sessions_by_character(
        self,
        character_id: str,
        limit: int = 50,
        include_deleted: bool = False
    ) -> List[Session]:
        """获取指定角色的所有会话"""
        conditions = [Session.character_id == character_id]
        if not include_deleted:
            conditions.append(Session.is_deleted == False)
        
        stmt = (
            select(Session)
            .where(and_(*conditions))
            .order_by(Session.last_active.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_recent_sessions(
        self,
        limit: int = 20,
        include_deleted: bool = False
    ) -> List[Session]:
        """获取最近活跃的会话"""
        conditions = []
        if not include_deleted:
            conditions.append(Session.is_deleted == False)
        
        stmt = select(Session)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(Session.last_active.desc()).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_contacts_grouped_by_character(
        self,
        limit_per_character: int = 10
    ) -> Dict[str, List[Session]]:
        """
        获取按角色分组的会话列表（通讯录）
        
        返回格式：
        {
            "character_id": [session1, session2, ...],
            ...
        }
        """
        # 获取所有未删除的会话，按角色和活跃时间排序
        stmt = (
            select(Session)
            .where(Session.is_deleted == False)
            .order_by(Session.character_id, Session.last_active.desc())
        )
        result = await self.session.execute(stmt)
        sessions = result.scalars().all()
        
        # 按角色分组
        grouped: Dict[str, List[Session]] = {}
        for session in sessions:
            if session.character_id not in grouped:
                grouped[session.character_id] = []
            if len(grouped[session.character_id]) < limit_per_character:
                grouped[session.character_id].append(session)
        
        return grouped
    
    async def update_last_active(self, session_id: str) -> None:
        """更新会话最后活跃时间"""
        stmt = (
            update(Session)
            .where(Session.id == session_id)
            .values(last_active=datetime.utcnow())
        )
        await self.session.execute(stmt)
    
    async def soft_delete(self, session_id: str) -> bool:
        """软删除会话"""
        stmt = (
            update(Session)
            .where(Session.id == session_id)
            .values(is_deleted=True)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
    
    async def update_title(self, session_id: str, title: str) -> Optional[Session]:
        """更新会话标题"""
        return await self.update_by_id(session_id, title=title)
