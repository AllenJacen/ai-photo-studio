from __future__ import annotations
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.deps import get_current_user
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.services.storage import generate_presigned_upload_url

router = APIRouter(prefix="/uploads", tags=["图片上传"])

LOCAL_UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads_local"
LOCAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class PresignRequest(BaseModel):
    file_name: str
    file_size: int
    file_type: str
    purpose: str = "source"


class PresignResponse(BaseModel):
    upload_url: str
    storage_key: str
    expires_in: int


class ConfirmRequest(BaseModel):
    storage_key: str


class FaceDetectionResult(BaseModel):
    faces_found: int = 0
    quality_score: float = 0.9
    warnings: list[str] = []


class ConfirmResponse(BaseModel):
    image_id: str
    face_detection_result: FaceDetectionResult


ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
MAX_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/presign", response_model=PresignResponse)
def presign_upload(
    data: PresignRequest,
    current_user: User = Depends(get_current_user),
):
    if data.file_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="不支持的图片格式，仅支持 JPG/PNG/WEBP/HEIC")
    if data.file_size > MAX_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 20MB")

    ext = data.file_name.rsplit(".", 1)[-1].lower() if "." in data.file_name else "jpg"
    storage_key = f"uploads/{current_user.id}/{uuid.uuid4().hex}.{ext}"

    try:
        upload_url = generate_presigned_upload_url(storage_key, data.file_type)
    except Exception:
        # In dev without real S3 config, return a mock URL
        upload_url = f"/mock-upload/{storage_key}"

    return PresignResponse(upload_url=upload_url, storage_key=storage_key, expires_in=3600)


@router.put("/local/{storage_key:path}")
async def local_upload(storage_key: str, request: Request):
    """预览模式专用: 接收前端 PUT 上传的文件,落盘到 backend/uploads_local/。
    生产模式下走真实 OSS 预签名 URL,不会到这里。"""
    # 只在没配置真实 S3 时启用
    if settings.AWS_ACCESS_KEY_ID:
        raise HTTPException(status_code=404, detail="生产模式不允许本地上传")
    # 防止路径穿越
    if ".." in storage_key or storage_key.startswith("/"):
        raise HTTPException(status_code=400, detail="非法路径")
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="空文件")
    target = LOCAL_UPLOAD_DIR / storage_key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    return JSONResponse({"ok": True, "size": len(body), "key": storage_key})


@router.post("/confirm", response_model=ConfirmResponse)
def confirm_upload(
    data: ConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # TODO: integrate InsightFace for real face detection
    # For now, return mock detection result
    face_result = FaceDetectionResult(
        faces_found=1,
        quality_score=0.85,
        warnings=[],
    )
    return ConfirmResponse(
        image_id=uuid.uuid4().hex,
        face_detection_result=face_result,
    )
