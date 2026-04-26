from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, JSON, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AIModelConfig(Base):
    __tablename__ = "ai_model_configs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(500))
    provider: Mapped[str] = mapped_column(String(50))
    endpoint_url: Mapped[Optional[str]] = mapped_column(String(500))
    api_key_env: Mapped[Optional[str]] = mapped_column(String(100))
    model_type: Mapped[str] = mapped_column(String(20), default="image2image")
    capabilities: Mapped[List] = mapped_column(JSON, default=list)
    credit_multiplier: Mapped[float] = mapped_column(Numeric(3, 1), default=1.0)
    avg_generation_time_s: Mapped[int] = mapped_column(Integer, default=60)
    max_resolution: Mapped[Optional[str]] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_local: Mapped[bool] = mapped_column(Boolean, default=False)
    config_params: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="available")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
