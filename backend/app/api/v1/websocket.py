from __future__ import annotations
"""WebSocket endpoint for real-time task progress updates via Redis pub/sub."""

import json
import asyncio
import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.config import settings
from app.core.security import decode_token
from app.core.database import SessionLocal
from app.models.task import GenerationTask

router = APIRouter()


@router.websocket("/ws/tasks/{task_id}")
async def task_progress_ws(websocket: WebSocket, task_id: str, token: str = ""):
    await websocket.accept()

    # Authenticate
    payload = decode_token(token)
    if not payload:
        await websocket.send_json({"event": "error", "data": {"message": "未授权"}})
        await websocket.close(code=4001)
        return

    user_id = payload.get("sub")

    # Verify task ownership
    db = SessionLocal()
    try:
        task = db.query(GenerationTask).filter(
            GenerationTask.id == task_id,
            GenerationTask.user_id == user_id,
        ).first()
        if not task:
            await websocket.send_json({"event": "error", "data": {"message": "任务不存在"}})
            await websocket.close(code=4004)
            return

        # Send current state immediately
        await websocket.send_json({
            "event": "task_update",
            "data": {
                "task_id": task_id,
                "status": task.status,
                "progress": task.progress,
                "current_stage": task.current_stage,
                "queue_position": task.queue_position,
            },
        })

        if task.status in ("completed", "failed", "cancelled"):
            await websocket.close()
            return
    finally:
        db.close()

    # Subscribe to Redis pub/sub channel
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"task:{task_id}")

    try:
        async def listen():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
                    if data.get("event") in ("task_completed", "task_failed"):
                        return

        # Run listener with timeout (30 min max)
        await asyncio.wait_for(listen(), timeout=1800)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(f"task:{task_id}")
        await redis_client.aclose()
