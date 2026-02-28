"""
Workspace 相关依赖：
- require_workspace_member：要求当前用户必须是 workspace 成员
- require_workspace_owner：要求当前用户是 OWNER（Day3 先简单做）
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.workspace import WorkspaceMember, WorkspaceRole


def require_workspace_member(workspace_id: int, db: Session, user: User) -> WorkspaceMember:
    """
    检查 user 是否是 workspace 成员。
    不通过就抛 403（避免泄露 workspace 是否存在，Day5 可做更细致处理）
    """
    m = db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    ).scalar_one_or_none()

    if not m:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a workspace member")

    return m


def require_workspace_owner(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WorkspaceMember:
    """
    依赖注入版本：要求当前用户必须是 OWNER。
    Day5 我们会升级成 require_role(min_role=...)
    """
    m = require_workspace_member(workspace_id, db, user)
    if m.role != WorkspaceRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner role required")
    return m
