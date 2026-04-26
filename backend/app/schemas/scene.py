from __future__ import annotations
from pydantic import BaseModel


class SceneOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    category: str
    description: str | None = None
    thumbnail_url: str | None = None
    preview_urls: list[str] = []
    recommended_model: str | None = None
    supported_models: list[str] = []
    default_params: dict = {}
    credit_cost: int
    is_premium: bool
    tags: list[str] = []


class SceneCategoryOut(BaseModel):
    id: str
    name: str
    icon: str
    count: int


class PaginatedScenes(BaseModel):
    items: list[SceneOut]
    total: int
    page: int
    page_size: int
