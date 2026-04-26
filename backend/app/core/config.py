from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "AI Photo Studio"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-use-strong-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/aiphoto"

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Storage (S3/OSS compatible)
    STORAGE_BUCKET: str = "ai-photo-studio"
    STORAGE_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    STORAGE_ENDPOINT_URL: str = ""  # For OSS/MinIO, empty = AWS S3
    CDN_BASE_URL: str = ""

    # AI Model API Keys
    REPLICATE_API_TOKEN: str = ""    # Flux Kontext 等 BFL 模型
    OPENAI_API_KEY: str = ""          # GPT Image 1
    GEMINI_API_KEY: str = ""          # Nano Banana / Imagen
    ARK_API_KEY: str = ""             # 字节火山方舟(Seedream)
    DASHSCOPE_API_KEY: str = ""       # 阿里通义(Qwen-Image)
    KLING_ACCESS_KEY: str = ""        # 快手可灵
    KLING_SECRET_KEY: str = ""
    MIDJOURNEY_API_KEY: str = ""      # MJ 官方 / GoAPI
    ZHIPU_API_KEY: str = ""           # 智谱 CogView-3-Flash(完全免费)/ CogView-4

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
