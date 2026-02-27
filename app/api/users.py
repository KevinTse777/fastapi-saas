"""
用户相关 API：
- /me：返回当前登录用户信息（需要 access token）
"""

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(tags=["users"])


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    # 注意：不要返回 password_hash
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "created_at": current_user.created_at,
    }
