"""
会话表 — 对应一次对话
"""
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.models.base import Base


class DBSession(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    character_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    last_active: Mapped[datetime] = mapped_column(default=datetime.now)
