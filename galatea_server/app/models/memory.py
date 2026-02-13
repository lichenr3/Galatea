"""
记忆表 — 角色的长期记忆（向量化存储）

记忆是角色级的（character_id），不是会话级的。
session_id 仅用于追溯记忆来源。
"""
from sqlalchemy import BigInteger, String, Text, ForeignKey, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from pgvector.sqlalchemy import Vector
from app.models.base import Base


class DBMemory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    character_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    session_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding = mapped_column(Vector(1536), nullable=True)  # 向量嵌入（维度随 embedding 模型调整）
    memory_type: Mapped[str] = mapped_column(String(20), default="conversation")  # fact / preference / event
    importance: Mapped[int] = mapped_column(SmallInteger, default=5)  # 1-10
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(nullable=True)
