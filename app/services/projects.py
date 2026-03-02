"""
Project 相关服务函数：
把“查 project + 校验 workspace 成员”封装起来，避免 API 重复写。
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.project import Project
from app.models.user import User
from app.core.workspace_deps import require_workspace_member


def get_project_and_require_member(project_id: int, db: Session, user: User) -> Project:
    """
    通过 project_id 获取 Project，并验证当前用户是该 Project 所属 workspace 的成员。
    - project 不存在：404
    - 不是成员：403
    """
    p = db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # 强制多租户隔离：必须是该 workspace 成员
    _ = require_workspace_member(p.workspace_id, db, user)

    return p
