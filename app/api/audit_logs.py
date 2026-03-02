"""
Audit Logs API
- GET /workspaces/{workspace_id}/audit-logs
只允许 ADMIN+ 查询
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.rbac import require_role
from app.models.user import User
from app.models.audit import AuditLog
from app.models.workspace import WorkspaceRole

router = APIRouter(tags=["audit"])


@router.get("/workspaces/{workspace_id}/audit-logs")
def list_audit_logs(
    workspace_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    查询审计日志：
    - 权限：ADMIN+
    - 分页：limit/offset
    """
    _ = require_role(workspace_id, WorkspaceRole.ADMIN, db, user)

    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    rows = db.execute(
        select(AuditLog)
        .where(AuditLog.workspace_id == workspace_id)
        .order_by(AuditLog.id.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()

    return [
        {
            "id": r.id,
            "workspace_id": r.workspace_id,
            "actor_id": r.actor_id,
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "meta": r.meta,
            "created_at": r.created_at,
        }
        for r in rows
    ]
