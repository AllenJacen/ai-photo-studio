from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.ai_model import AIModelConfig
from app.schemas.ai_model import AIModelOut

router = APIRouter(prefix="/ai-models", tags=["AI 模型"])


@router.get("", response_model=list[AIModelOut])
def list_models(db: Session = Depends(get_db)):
    return db.query(AIModelConfig).filter(AIModelConfig.is_active.is_(True)).all()


@router.get("/{model_id}/status")
def model_status(model_id: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    model = db.query(AIModelConfig).filter(AIModelConfig.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return {
        "status": model.status,
        "queue_length": 0,
        "estimated_wait_s": model.avg_generation_time_s,
    }
