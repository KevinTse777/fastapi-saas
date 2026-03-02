"""
Invite API（Day3）
- POST /workspaces/{id}/invites：OWNER 创建邀请
- POST /invites/accept：被邀请人接受（要求当前登录用户邮箱匹配 invite.email）
"""

from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.workspace import Invite, InviteStatus, WorkspaceMember, WorkspaceRole
from app.schemas.workspace import InviteCreateIn, InviteOut, InviteAcceptIn
from app.core.workspace_deps import require_workspace_owner
from app.core.rbac import require_role
from app.models.workspace import WorkspaceRole
from app.services.audit import write_audit
router = APIRouter(tags=["invites"])


@router.post("/workspaces/{workspace_id}/invites", response_model=InviteOut, status_code=201)
def create_invite(
    workspace_id: int,
    payload: InviteCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    创建邀请（Day3 简化：只有 OWNER 能邀请）
    - 生成随机 token
    - expires_at 统一用 UTC naive（MySQL 默认不存 tzinfo）
    """
    # 允许 OWNER/ADMIN 邀请
    _ = require_role(workspace_id, WorkspaceRole.ADMIN, db, user)

    token = secrets.token_urlsafe(24)
    expires_at = datetime.utcnow() + timedelta(days=3)  # ✅ naive UTC

    try:
        invite_role = WorkspaceRole(payload.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role. Use OWNER/ADMIN/MEMBER/GUEST")
    
    inv = Invite(
        workspace_id=workspace_id,
        email=str(payload.email),
        token=token,
        status=InviteStatus.PENDING,
        expires_at=expires_at,
        role=invite_role
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    write_audit(
    db=db,
    workspace_id=workspace_id,
    actor_id=user.id,
    action="INVITE_CREATE",
    entity_type="invite",
    entity_id=inv.id,
    meta={"email": inv.email, "role": inv.role.value},
)
    db.commit()

    return InviteOut(
        id=inv.id,
        workspace_id=inv.workspace_id,
        email=inv.email,
        token=inv.token,
        status=inv.status.value,
        expires_at=inv.expires_at,
        created_at=inv.created_at,
        role=inv.role.value,
    )


@router.post("/invites/accept")
def accept_invite(
    payload: InviteAcceptIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    接受邀请：
    1) token 查 invite
    2) 必须 PENDING 且未过期
    3) 当前用户邮箱必须等于 invite.email
    4) 写入 workspace_members（MEMBER）
    5) invite 状态改 ACCEPTED
    """
    inv = db.execute(select(Invite).where(Invite.token == payload.token)).scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invite not found")

    if inv.status != InviteStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Invite not pending: {inv.status.value}")

    now = datetime.utcnow()  # ✅ naive UTC
    if inv.expires_at <= now:
        inv.status = InviteStatus.EXPIRED
        db.commit()
        raise HTTPException(status_code=400, detail="Invite expired")

    if user.email.lower() != inv.email.lower():
        raise HTTPException(status_code=403, detail="Invite email mismatch")

    # 如果已经是成员：直接标记 ACCEPTED
    existing = db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == inv.workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    ).scalar_one_or_none()

    if not existing:
        m = WorkspaceMember(
            workspace_id=inv.workspace_id,
            user_id=user.id,
            role=inv.role,  # ✅ 按邀请指定的角色加入,
        )
        db.add(m)

    inv.status = InviteStatus.ACCEPTED
    db.commit()
    # accept_invite 里，inv.status = ACCEPTED 并 commit 后
    write_audit(
        db=db,
        workspace_id=inv.workspace_id,
        actor_id=user.id,
        action="INVITE_ACCEPT",
        entity_type="invite",
        entity_id=inv.id,
        meta={"email": inv.email},
    )
    db.commit()

    return {"status": "ok", "workspace_id": inv.workspace_id}
            
