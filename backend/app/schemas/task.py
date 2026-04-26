from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel
from app.schemas.scene import SceneOut


class InputImageIn(BaseModel):
    storage_key: str
    role: str = "single"


class GenerationParamsIn(BaseModel):
    aspect_ratio: str = "3:4"
    quality: str = "hd"
    output_count: int = 2
    style_strength: int = 7
    custom_prompt: str | None = None
    custom_negative_prompt: str | None = None


class TaskCreate(BaseModel):
    scene_id: str
    ai_model: str
    input_images: list[InputImageIn]
    params: GenerationParamsIn = GenerationParamsIn()


class CreateTaskResponse(BaseModel):
    task_id: str
    status: str
    queue_position: int
    estimated_wait_s: int
    credits_to_consume: int


class GeneratedImageOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    task_id: str
    original_url: str = ""
    thumbnail_url: str = ""
    width: int | None = None
    height: int | None = None
    file_size: int | None = None
    format: str | None = None
    is_favorited: bool = False
    user_rating: int | None = None
    download_count: int = 0
    watermark_removed: bool = False


class TaskOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    user_id: str
    scene_id: str
    scene: SceneOut | None = None
    ai_model: str
    status: str
    progress: int = 0
    current_stage: str | None = None
    queue_position: int | None = None
    estimated_remaining_s: int | None = None
    result_images: list[GeneratedImageOut] | None = None
    error_message: str | None = None
    credits_consumed: int = 0
    generation_time_ms: int | None = None
    created_at: datetime
    completed_at: datetime | None = None


class TaskListOut(BaseModel):
    items: list[TaskOut]
    total: int
    page: int
    page_size: int
