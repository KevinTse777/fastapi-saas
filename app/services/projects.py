"""
Project 相关服务函数：
把“查 project + 校验 workspace 角色权限”封装起来，避免 API 重复写。
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.project import Project
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.core.rbac import require_role


def get_project_and_require_role(
    project_id: int,
    min_role: WorkspaceRole,
    db: Session,
    user: User,
) -> Project:
    """
    通过 project_id 获取 Project，并验证当前用户在该 Project 所属 workspace 的角色 >= min_role。
    - project 不存在：404
    - 角色不足/非成员：403
    """
    p = db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # ✅ 关键：RBAC 校验（比“仅成员”更严格）
    _ = require_role(p.workspace_id, min_role, db, user)

    return p
