from __future__ import annotations
"""
Celery worker for async image generation.

Flow:
  1. Fetch task from DB
  2. Update status → processing
  3. Push WebSocket progress updates via Redis pub/sub
  4. Call AI Gateway
  5. Download generated images → upload to storage
  6. Save GeneratedImage records
  7. Update task status → completed / failed
"""

import asyncio
import uuid
import time
import json
import httpx
import redis as redis_sync
from datetime import datetime, timezone

from app.workers.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.task import GenerationTask, GeneratedImage
from app.services.ai_gateway.base import ImageData, GenerationParams
from app.services.ai_gateway.registry import route_model

try:
    _redis_client = redis_sync.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1)
except Exception:
    _redis_client = None


def _push_progress(task_id: str, event: str, data: dict) -> None:
    if _redis_client is None:
        return
    try:
        payload = json.dumps({"event": event, "data": data})
        _redis_client.publish(f"task:{task_id}", payload)
    except Exception:
        pass


def _update_task(db, task: GenerationTask, **kwargs) -> None:
    for k, v in kwargs.items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)


def run_generation_sync(task_id: str) -> dict:
    """Synchronous version for preview/local mode without Celery worker."""
    db = SessionLocal()
    task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()

    if not task or task.status not in ("pending",):
        db.close()
        return {"status": "skipped"}

    try:
        # --- Stage 1: preprocessing ---
        _update_task(db, task, status="processing", progress=5, current_stage="preprocessing",
                     started_at=datetime.now(timezone.utc))
        _push_progress(task_id, "task_update", {
            "task_id": task_id, "status": "processing", "progress": 5,
            "current_stage": "preprocessing",
        })

        # Build source images — 关键修复:把上传的本地图读取为 base64,
        # 这样图生图模型(Gemini Nano Banana / GPT Image 2 edits / Flux Kontext)
        # 才能拿到用户的脸,生成的人物才会像。
        from pathlib import Path as _Path
        import base64 as _b64
        _UPLOAD_DIR = _Path(__file__).resolve().parents[2] / "uploads_local"
        source_images = []
        for img in (task.input_images or []):
            sk = img.get("storage_key") or ""
            role = img.get("role", "single")
            url = None
            b64 = None
            if sk.startswith(("http://", "https://")):
                url = sk
            else:
                # 相对路径 → 读本地文件
                local = _UPLOAD_DIR / sk
                if local.exists():
                    raw = local.read_bytes()
                    b64 = _b64.b64encode(raw).decode("ascii")
            source_images.append(ImageData(url=url, base64=b64, role=role))

        # Fetch scene for params
        from app.models.scene import Scene
        scene = db.query(Scene).filter(Scene.id == task.scene_id).first()

        params_dict = task.generation_params or {}
        aspect = params_dict.get("aspect_ratio", "3:4")
        w, h = {
            "1:1": (1024, 1024), "4:3": (1024, 768),
            "3:4": (1024, 1365), "16:9": (1280, 720),
        }.get(aspect, (1024, 1365))

        gen_params = GenerationParams(
            width=w, height=h,
            style_strength=params_dict.get("style_strength", 7) / 10,
            output_count=params_dict.get("output_count", 2),
        )

        # --- Stage 2: generating ---
        _update_task(db, task, progress=20, current_stage="generating")
        _push_progress(task_id, "task_update", {
            "task_id": task_id, "status": "processing", "progress": 20,
            "current_stage": "generating",
        })

        provider = asyncio.run(route_model(
            task.ai_model,
            scene_recommended=scene.recommended_model if scene else None,
            scene_supported=scene.supported_models if scene else None,
        ))
        result = asyncio.run(provider.generate(
            source_images=source_images,
            prompt=task.final_prompt or "",
            negative_prompt=task.negative_prompt or "",
            params=gen_params,
        ))

        # --- Stage 3: postprocessing ---
        _update_task(db, task, progress=80, current_stage="postprocessing")
        _push_progress(task_id, "task_update", {
            "task_id": task_id, "status": "processing", "progress": 80,
            "current_stage": "postprocessing",
        })

        # Save result images
        # 保留 provider 返回的真实 URL (外部 CDN / 智谱 ufileos / OpenAI / picsum mock 等):
        # 直接用 URL 本身作为 storage_key,这样 _enrich_task 取出来就是真实 URL。
        # 真要把图迁移到自己 OSS,可以在这里下载 url 内容上传到 OSS,然后用 OSS key 替换。
        result_images_out = []
        for url in result.image_urls:
            img_record = GeneratedImage(
                id=str(uuid.uuid4()),
                task_id=task_id,
                user_id=task.user_id,
                storage_key=url,  # 直接存外部 URL
                format="jpg",
            )
            db.add(img_record)
            result_images_out.append({
                "id": img_record.id,
                "url": url,
                "thumbnail_url": url,
            })

        # Update user stats
        from app.models.user import User
        user = db.query(User).filter(User.id == task.user_id).first()
        if user:
            user.total_generated += len(result.image_urls)

        _update_task(db, task,
                     status="completed",
                     progress=100,
                     current_stage=None,
                     completed_at=datetime.now(timezone.utc),
                     generation_time_ms=result.generation_time_ms)

        _push_progress(task_id, "task_completed", {
            "task_id": task_id,
            "status": "completed",
            "result_images": result_images_out,
        })
        return {"status": "completed", "image_count": len(result.image_urls)}

    except Exception as exc:
        error_msg = str(exc)
        _update_task(db, task,
                     status="failed",
                     error_message=error_msg,
                     progress=0)

        # Refund credits
        from app.models.user import User
        from app.models.credit import CreditTransaction
        user = db.query(User).filter(User.id == task.user_id).first()
        if user:
            user.credits += task.credits_consumed
            tx = CreditTransaction(
                user_id=task.user_id,
                amount=task.credits_consumed,
                type="refund",
                ref_id=task_id,
                description="生成失败自动退款",
                balance_after=user.credits,
            )
            db.add(tx)
            db.commit()

        _push_progress(task_id, "task_failed", {
            "task_id": task_id,
            "status": "failed",
            "error_message": error_msg,
            "credits_refunded": task.credits_consumed,
        })
        return {"status": "failed", "error": error_msg}
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def run_generation_task(self, task_id: str) -> dict:
    """Celery entry — delegates to sync function."""
    return run_generation_sync(task_id)
