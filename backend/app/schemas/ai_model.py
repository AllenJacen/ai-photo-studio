from __future__ import annotations
from pydantic import BaseModel


class AIModelOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    display_name: str
    description: str | None = None
    capabilities: list[str] = []
    credit_multiplier: float
    avg_generation_time_s: int
    max_resolution: str | None = None
    status: str
    queue_length: int | None = None
    estimated_wait_s: int | None = None
