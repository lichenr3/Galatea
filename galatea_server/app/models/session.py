"""
Session 会话模型

存储会话元数据，与 LangGraph Checkpointer 配合使用。
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.message import Message


class Session(Base):
    """
    会话模型
    
    存储会话的元数据，对话内容由 Message 模型存储。
    LangGraph 的状态（包括 messages）由 Checkpointer 管理。
    """
    __tablename__ = "sessions"
    
    # 主键：使用 UUID 字符串
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # 角色 ID
    character_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # 会话标题（可选，用于显示）
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # 会话语言
    language: Mapped[str] = mapped_column(String(10), default="zh")
    
    # 是否启用音频
    enable_audio: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        nullable=False
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # 是否已删除（软删除）
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # 关联：一个会话有多条消息
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, character={self.character_id})>"
