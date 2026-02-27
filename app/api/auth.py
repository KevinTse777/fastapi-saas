"""
认证相关 API：
- /auth/register
- /auth/login
- /auth/refresh  (rotation)
- /auth/logout   (revoke refresh)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterIn, LoginIn, TokenOut, RefreshIn
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    rotate_refresh,
    revoke_refresh,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    # 1) 检查邮箱是否已注册
    exists = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Email already registered")

    # 2) 创建用户（存 password_hash）
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 3) 直接签发 tokens（注册即登录，简化体验）
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return TokenOut(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    # 1) 查用户
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 2) 校验密码
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 3) 签发 tokens
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return TokenOut(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenOut)
def refresh(payload: RefreshIn):
    # 1) 解析 refresh token
    try:
        data = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 2) 必须是 refresh
    if data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    # 3) rotation：旧 refresh 只能用一次
    try:
        new_refresh = rotate_refresh(data)
    except PermissionError:
        raise HTTPException(status_code=401, detail="Refresh token reused/revoked")

    user_id = int(data["sub"])
    new_access = create_access_token(user_id)

    return TokenOut(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout")
def logout(payload: RefreshIn):
    """
    登出：作废 refresh token（从 Redis allowlist 删除）
    注意：access token 是短期的，一般不强制撤销（除非你要做 access blacklist）。
    """
    try:
        data = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    if data.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Not a refresh token")

    revoke_refresh(data["jti"])
    return {"status": "ok"}
