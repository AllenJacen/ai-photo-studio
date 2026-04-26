from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.models.credit import CreditTransaction
from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["认证"])


def _issue_tokens(user: User) -> TokenResponse:
    access_token = create_access_token({"sub": user.id, "type": "access"})
    refresh_token = create_access_token({"sub": user.id, "type": "refresh"})
    return TokenResponse(
        user=UserOut.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/register", response_model=TokenResponse)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if not data.email and not data.phone:
        raise HTTPException(status_code=400, detail="请提供邮箱或手机号")

    # Check existing
    if data.email and db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="该邮箱已注册")
    if data.phone and db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(status_code=400, detail="该手机号已注册")

    user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        phone=data.phone,
        nickname=data.nickname or (data.email.split("@")[0] if data.email else f"用户{uuid.uuid4().hex[:6]}"),
        password_hash=hash_password(data.password) if data.password else None,
        credits=5,
    )
    db.add(user)

    # Gift credits transaction
    tx = CreditTransaction(
        user_id=user.id,
        amount=5,
        type="gift",
        description="注册赠送积分",
        balance_after=5,
    )
    db.add(tx)
    db.commit()
    db.refresh(user)
    return _issue_tokens(user)


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user: User | None = None

    if data.email:
        user = db.query(User).filter(User.email == data.email).first()
    elif data.phone:
        user = db.query(User).filter(User.phone == data.phone).first()

    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if data.password and user.password_hash:
        if not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="密码错误")

    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: dict, db: Session = Depends(get_db)):
    from app.core.security import decode_token
    token = body.get("refresh_token", "")
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh Token 无效")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return _issue_tokens(user)


@router.post("/sms/send")
def send_sms(body: dict):
    # Placeholder - integrate with SMS service in production
    phone = body.get("phone", "")
    if not phone:
        raise HTTPException(status_code=400, detail="请提供手机号")
    return {"expires_in": 300, "message": "验证码已发送（演示模式下不发送真实短信）"}
