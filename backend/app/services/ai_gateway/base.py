from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class ProviderStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    MAINTENANCE = "maintenance"


@dataclass
class ImageData:
    url: str | None = None
    base64: str | None = None
    role: str = "single"


@dataclass
class GenerationParams:
    width: int = 1024
    height: int = 1536
    steps: int = 30
    cfg_scale: float = 7.5
    style_strength: float = 0.75
    output_count: int = 2
    seed: int | None = None
    extra: dict = field(default_factory=dict)


@dataclass
class GenerationResult:
    image_urls: list[str] = field(default_factory=list)
    image_base64s: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    generation_time_ms: int = 0


class AIProviderBase(ABC):
    """Strategy pattern base class for all AI providers."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        ...

    @abstractmethod
    async def generate(
        self,
        source_images: list[ImageData],
        prompt: str,
        negative_prompt: str,
        params: GenerationParams,
    ) -> GenerationResult:
        ...

    @abstractmethod
    async def health_check(self) -> ProviderStatus:
        ...
