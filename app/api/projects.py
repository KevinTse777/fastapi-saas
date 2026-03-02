"""
Project API（RBAC 版）
- POST /workspaces/{workspace_id}/projects：创建项目（MEMBER+）
- GET  /workspaces/{workspace_id}/projects：列出项目（GUEST+）
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.rbac import require_role
from app.models.user import User
from app.models.project import Project
from app.models.workspace import WorkspaceRole
from app.schemas.project import ProjectCreateIn, ProjectOut

router = APIRouter(prefix="/workspaces/{workspace_id}/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    workspace_id: int,
    payload: ProjectCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # ✅ 写操作：至少 MEMBER
    _ = require_role(workspace_id, WorkspaceRole.MEMBER, db, user)

    p = Project(
        workspace_id=workspace_id,
        name=payload.name,
        description=payload.description,
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    return ProjectOut(
        id=p.id,
        workspace_id=p.workspace_id,
        name=p.name,
        description=p.description,
        created_at=p.created_at,
    )


@router.get("", response_model=list[ProjectOut])
def list_projects(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # ✅ 读操作：GUEST 也允许（只要是成员）
    _ = require_role(workspace_id, WorkspaceRole.GUEST, db, user)

    rows = db.execute(
        select(Project)
        .where(Project.workspace_id == workspace_id)
        .order_by(Project.id.desc())
    ).scalars().all()

    return [
        ProjectOut(
            id=p.id,
            workspace_id=p.workspace_id,
            name=p.name,
            description=p.description,
            created_at=p.created_at,
        )
        for p in rows
    ]
