from __future__ import annotations
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.task import GenerationTask, GeneratedImage
from app.models.scene import Scene
from app.models.ai_model import AIModelConfig
from app.models.credit import CreditTransaction
from app.schemas.task import TaskCreate, TaskOut, TaskListOut, CreateTaskResponse, GeneratedImageOut
from app.services.storage import get_public_url

router = APIRouter(prefix="/tasks", tags=["生成任务"])


def _enrich_task(task: GenerationTask) -> TaskOut:
    """Add signed URLs to result images before serializing."""
    if task.images:
        result_images = []
        for img in task.images:
            out = GeneratedImageOut.model_validate(img)
            try:
                out.original_url = get_public_url(img.storage_key)
                if img.thumbnail_key:
                    out.thumbnail_url = get_public_url(img.thumbnail_key)
            except Exception:
                out.original_url = f"/mock/{img.storage_key}"
                out.thumbnail_url = out.original_url
            result_images.append(out)
        task.__dict__["result_images"] = result_images
    return TaskOut.model_validate(task)


@router.post("", response_model=CreateTaskResponse)
def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scene = db.query(Scene).filter(Scene.id == data.scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")

    ai_model = db.query(AIModelConfig).filter(AIModelConfig.id == data.ai_model, AIModelConfig.is_active.is_(True)).first()
    if not ai_model:
        raise HTTPException(status_code=400, detail="AI 模型不可用")

    credits_needed = int(scene.credit_cost * float(ai_model.credit_multiplier) * data.params.output_count)
    if current_user.credits < credits_needed:
        raise HTTPException(status_code=402, detail=f"积分不足，需要 {credits_needed} 积分，当前余额 {current_user.credits}")

    # Build final prompt
    final_prompt = scene.prompt_template
    if data.params.custom_prompt:
        final_prompt += f", {data.params.custom_prompt}"

    task = GenerationTask(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        scene_id=data.scene_id,
        input_images=[img.model_dump() for img in data.input_images],
        ai_model=data.ai_model,
        final_prompt=final_prompt,
        negative_prompt=data.params.custom_negative_prompt or scene.negative_prompt,
        generation_params=data.params.model_dump(),
        status="pending",
        credits_consumed=credits_needed,
    )
    db.add(task)

    # Deduct credits
    current_user.credits -= credits_needed
    tx = CreditTransaction(
        user_id=current_user.id,
        amount=-credits_needed,
        type="generation",
        ref_id=task.id,
        description=f"生成任务：{scene.name}",
        balance_after=current_user.credits,
    )
    db.add(tx)
    db.commit()
    db.refresh(task)

    # Dispatch: thread for memory broker (preview), Celery otherwise
    import threading
    from app.core.config import settings as _settings
    from app.workers.generation_worker import run_generation_sync, run_generation_task
    if _settings.CELERY_BROKER_URL.startswith(("redis://", "amqp://", "sqs://")):
        try:
            run_generation_task.delay(task.id)
        except Exception:
            threading.Thread(target=run_generation_sync, args=(task.id,), daemon=True).start()
    else:
        threading.Thread(target=run_generation_sync, args=(task.id,), daemon=True).start()

    # Estimate queue position
    pending_count = db.query(GenerationTask).filter(GenerationTask.status == "pending").count()

    return CreateTaskResponse(
        task_id=task.id,
        status="pending",
        queue_position=pending_count,
        estimated_wait_s=ai_model.avg_generation_time_s * data.params.output_count,
        credits_to_consume=credits_needed,
    )


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(GenerationTask).filter(
        GenerationTask.id == task_id,
        GenerationTask.user_id == current_user.id,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _enrich_task(task)


@router.post("/{task_id}/cancel")
def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(GenerationTask).filter(
        GenerationTask.id == task_id,
        GenerationTask.user_id == current_user.id,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status not in ("pending",):
        raise HTTPException(status_code=400, detail="只有排队中的任务可以取消")

    task.status = "cancelled"
    # Refund credits
    refund = task.credits_consumed
    current_user.credits += refund
    tx = CreditTransaction(
        user_id=current_user.id,
        amount=refund,
        type="refund",
        ref_id=task.id,
        description="取消任务退款",
        balance_after=current_user.credits,
    )
    db.add(tx)
    db.commit()
    return {"success": True, "credits_refunded": refund}


@router.get("/{task_id}/results", response_model=list[GeneratedImageOut])
def get_results(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(GenerationTask).filter(
        GenerationTask.id == task_id,
        GenerationTask.user_id == current_user.id,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    enriched = _enrich_task(task)
    return enriched.result_images or []
