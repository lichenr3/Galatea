"""
Message 消息模型

存储对话历史，每条消息关联一个会话。
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.session import Session


class Message(Base):
    """
    消息模型
    
    存储每条对话消息，包括用户消息和 AI 回复。
    """
    __tablename__ = "messages"
    
    # 主键：自增 ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 外键：关联会话
    session_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 消息角色：system | user | assistant | tool
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # 消息内容
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 消息 ID（用于前端追踪，可选）
    message_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # 工具调用相关（可选）
    tool_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tool_call_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # 关联：多条消息属于一个会话
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="messages"
    )
    
    def __repr__(self) -> str:
        content_preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"<Message(id={self.id}, role={self.role}, content={content_preview})>"
    
    def to_langchain_format(self) -> dict:
        """转换为 LangChain 消息格式"""
        return {
            "role": self.role,
            "content": self.content
        }
