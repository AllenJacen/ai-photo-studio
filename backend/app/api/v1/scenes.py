from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.scene import Scene
from app.schemas.scene import SceneOut, SceneCategoryOut, PaginatedScenes

router = APIRouter(prefix="/scenes", tags=["场景"])

CATEGORY_META = {
    "wedding": {"name": "婚纱系列", "icon": "💒"},
    "portrait": {"name": "时尚写真", "icon": "📸"},
    "chinese_style": {"name": "中国风", "icon": "🏯"},
    "artistic": {"name": "艺术风格", "icon": "🎨"},
    "fantasy": {"name": "奇幻主题", "icon": "✨"},
    "professional": {"name": "商务证件", "icon": "💼"},
}


@router.get("", response_model=PaginatedScenes)
def list_scenes(
    category: str | None = Query(None),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    q = db.query(Scene).filter(Scene.is_active.is_(True))
    if category:
        q = q.filter(Scene.category == category)
    if keyword:
        q = q.filter(Scene.name.ilike(f"%{keyword}%"))
    total = q.count()
    items = q.order_by(Scene.sort_order.asc(), Scene.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedScenes(items=items, total=total, page=page, page_size=page_size)


@router.get("/categories", response_model=list[SceneCategoryOut])
def list_categories(db: Session = Depends(get_db)):
    from sqlalchemy import func
    counts = dict(
        db.query(Scene.category, func.count(Scene.id))
        .filter(Scene.is_active.is_(True))
        .group_by(Scene.category)
        .all()
    )
    return [
        SceneCategoryOut(id=k, name=v["name"], icon=v["icon"], count=counts.get(k, 0))
        for k, v in CATEGORY_META.items()
    ]


@router.get("/recommended", response_model=list[SceneOut])
def recommended_scenes(db: Session = Depends(get_db)):
    return db.query(Scene).filter(Scene.is_active.is_(True), "热门" == Scene.tags.any_()).limit(8).all()


@router.get("/{scene_id}", response_model=SceneOut)
def get_scene(scene_id: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
    return scene
