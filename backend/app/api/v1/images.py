from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.task import GeneratedImage
from app.services.storage import generate_presigned_download_url, get_public_url

router = APIRouter(prefix="/images", tags=["图片操作"])


@router.get("/{image_id}/download-url")
def download_url(
    image_id: str,
    format: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    img = db.query(GeneratedImage).filter(
        GeneratedImage.id == image_id,
        GeneratedImage.user_id == current_user.id,
    ).first()
    if not img:
        raise HTTPException(status_code=404, detail="图片不存在")
    try:
        url = generate_presigned_download_url(img.storage_key)
    except Exception:
        url = get_public_url(img.storage_key)
    return {"download_url": url, "expires_in": 3600}


@router.post("/batch-download")
def batch_download(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image_ids = body.get("image_ids", [])
    images = db.query(GeneratedImage).filter(
        GeneratedImage.id.in_(image_ids),
        GeneratedImage.user_id == current_user.id,
    ).all()
    # TODO: create zip file async and return URL
    return {"zip_url": f"/mock/batch-download/{current_user.id}", "expires_in": 3600}


@router.post("/{image_id}/favorite")
def toggle_favorite(
    image_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    img = db.query(GeneratedImage).filter(
        GeneratedImage.id == image_id,
        GeneratedImage.user_id == current_user.id,
    ).first()
    if not img:
        raise HTTPException(status_code=404, detail="图片不存在")
    img.is_favorited = not img.is_favorited
    db.commit()
    return {"is_favorited": img.is_favorited}


@router.post("/{image_id}/rate")
def rate_image(
    image_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rating = body.get("rating")
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="评分需为 1-5")
    img = db.query(GeneratedImage).filter(
        GeneratedImage.id == image_id,
        GeneratedImage.user_id == current_user.id,
    ).first()
    if not img:
        raise HTTPException(status_code=404, detail="图片不存在")
    img.user_rating = rating
    db.commit()
    return {"success": True}


@router.post("/{image_id}/share")
def share_image(
    image_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    img = db.query(GeneratedImage).filter(
        GeneratedImage.id == image_id,
        GeneratedImage.user_id == current_user.id,
    ).first()
    if not img:
        raise HTTPException(status_code=404, detail="图片不存在")
    from datetime import datetime, timedelta
    expires_hours = body.get("expires_hours", 168)
    expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
    share_token = f"share_{image_id[:8]}"
    return {
        "share_url": f"/share/{share_token}",
        "expires_at": expires_at.isoformat(),
    }
