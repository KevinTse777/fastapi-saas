"""
RBAC 工具：
- 角色等级定义（用于 min_role 判断）
- require_role：统一的权限依赖（比你之前的 require_workspace_owner 更通用）
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.workspace import WorkspaceMember, WorkspaceRole


# 角色等级：数值越大权限越高
ROLE_RANK: dict[WorkspaceRole, int] = {
    WorkspaceRole.GUEST: 10,
    WorkspaceRole.MEMBER: 20,
    WorkspaceRole.ADMIN: 30,
    WorkspaceRole.OWNER: 40,
}


def require_role(
    workspace_id: int,
    min_role: WorkspaceRole,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WorkspaceMember:
    """
    统一权限依赖：
    - 用户必须是 workspace 成员
    - 且其角色等级 >= min_role
    """
    m = db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    ).scalar_one_or_none()

    if not m:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a workspace member")

    if ROLE_RANK[m.role] < ROLE_RANK[min_role]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires role >= {min_role.value}",
        )

    return m
