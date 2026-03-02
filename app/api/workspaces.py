"""
Workspace API（Day3）
- POST /workspaces：创建 workspace（创建者自动成为 OWNER）
- GET  /workspaces：列出当前用户加入的 workspaces
- GET  /workspaces/{id}/members：列出 workspace 成员（要求是成员）
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.schemas.workspace import WorkspaceCreateIn, WorkspaceOut, MemberOut
from app.core.workspace_deps import require_workspace_member
from app.services.audit import write_audit
router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceOut, status_code=201)
def create_workspace(
    payload: WorkspaceCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    创建 workspace：
    1) 插入 workspaces
    2) 插入 workspace_members，把创建者设为 OWNER
    """
    ws = Workspace(name=payload.name, owner_id=user.id)
    db.add(ws)
    db.commit()
    db.refresh(ws)

    owner_member = WorkspaceMember(
        workspace_id=ws.id,
        user_id=user.id,
        role=WorkspaceRole.OWNER,
    )
    db.add(owner_member)
    db.commit()
    # 记录审计日志
    write_audit(
        db=db,
        workspace_id=ws.id,
        actor_id=user.id,
        action="WORKSPACE_CREATE",
        entity_type="workspace",
        entity_id=ws.id,
        meta={"name": ws.name},
    )
    db.commit()

    return WorkspaceOut(id=ws.id, name=ws.name, owner_id=ws.owner_id, created_at=ws.created_at)


@router.get("", response_model=list[WorkspaceOut])
def list_my_workspaces(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    查询我加入的所有 workspaces（通过 workspace_members 联表）
    """
    rows = db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user.id)
        .order_by(Workspace.id.desc())
    ).scalars().all()

    return [WorkspaceOut(id=w.id, name=w.name, owner_id=w.owner_id, created_at=w.created_at) for w in rows]


@router.get("/{workspace_id}/members", response_model=list[MemberOut])
def list_members(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    列出 workspace 成员：
    - 必须是成员才能查看
    """
    _ = require_workspace_member(workspace_id, db, user)

    members = db.execute(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
    ).scalars().all()

    return [
        MemberOut(user_id=m.user_id, role=m.role.value, created_at=m.created_at)
        for m in members
    ]


@router.get("/{workspace_id}/me")
def workspace_me(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    返回我在该 workspace 的成员信息（用于调试/前端判断权限）
    - 非成员：403
    """
    m = require_workspace_member(workspace_id, db, user)
    return {
        "workspace_id": m.workspace_id,
        "user_id": m.user_id,
        "role": m.role.value,
        "created_at": m.created_at,
    }