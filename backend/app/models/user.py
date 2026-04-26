import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(50))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(20))
    oauth_id: Mapped[Optional[str]] = mapped_column(String(255))
    membership_type: Mapped[str] = mapped_column(String(20), default="free")
    membership_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    credits: Mapped[int] = mapped_column(Integer, default=5)
    total_generated: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
