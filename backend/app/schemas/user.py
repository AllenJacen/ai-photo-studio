from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    email: str | None = None
    phone: str | None = None
    nickname: str | None = None
    avatar_url: str | None = None
    membership_type: str
    membership_expires_at: datetime | None = None
    credits: int
    total_generated: int


class UserCreate(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None
    password: str | None = None
    sms_code: str | None = None
    nickname: str | None = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str | None) -> str | None:
        if v is not None and len(v) < 8:
            raise ValueError("密码至少 8 位")
        return v


class UserLogin(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None
    password: str | None = None
    sms_code: str | None = None


class TokenResponse(BaseModel):
    user: UserOut
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
