"""
审计日志写入工具：
在关键写操作成功后调用，用于落库。
"""

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def write_audit(
    db: Session,
    workspace_id: int,
    actor_id: int,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    meta: dict | None = None,
) -> None:
    """
    写入一条审计日志（不返回值）
    - 建议在 db.commit() 成功后调用（或同一事务内一起 commit）
    """
    log = AuditLog(
        workspace_id=workspace_id,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        meta=meta,
    )
    db.add(log)
