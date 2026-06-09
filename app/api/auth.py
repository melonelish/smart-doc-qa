from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
import jwt

from app.core.config import get_settings
from app.db.database import get_db
from app.models.user import User
from app.api.deps import get_current_user

settings = get_settings()
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    user_id: str


def _create_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {
        "sub": user.id,
        "username": user.username,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    user = User(
        username=body.username,
        password_hash=bcrypt.hash(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=_create_token(user),
        username=user.username,
        user_id=user.id,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not bcrypt.verify(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return TokenResponse(
        access_token=_create_token(user),
        username=user.username,
        user_id=user.id,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(current_user: User = Depends(get_current_user)):
    return TokenResponse(
        access_token=_create_token(current_user),
        username=current_user.username,
        user_id=current_user.id,
    )


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }
