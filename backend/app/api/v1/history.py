from __future__ import annotations
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.task import GenerationTask
from app.schemas.task import TaskOut, TaskListOut
from app.api.v1.tasks import _enrich_task

router = APIRouter(prefix="/history", tags=["历史记录"])


@router.get("", response_model=TaskListOut)
def list_history(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(GenerationTask).filter(GenerationTask.user_id == current_user.id)
    if status:
        q = q.filter(GenerationTask.status == status)
    total = q.count()
    tasks = q.order_by(GenerationTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return TaskListOut(
        items=[_enrich_task(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/{task_id}")
def delete_task(
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
    db.delete(task)
    db.commit()
    return {"success": True}


@router.delete("")
def batch_delete(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 兼容前端 camelCase (taskIds) 与后端约定 snake_case (task_ids)
    task_ids = body.get("task_ids") or body.get("taskIds") or []
    if not task_ids:
        return {"deleted_count": 0}
    # 不能用 query.delete() 批量删 — 会绕过 ORM cascade,
    # 导致 generated_images.task_id 被 SET NULL 触发 NOT NULL 违约
    # 必须逐个 db.delete() 让 cascade="all, delete-orphan" 起作用
    tasks = db.query(GenerationTask).filter(
        GenerationTask.id.in_(task_ids),
        GenerationTask.user_id == current_user.id,
    ).all()
    for t in tasks:
        db.delete(t)
    db.commit()
    deleted = len(tasks)
    return {"deleted_count": deleted}
