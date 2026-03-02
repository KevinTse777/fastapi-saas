"""
Audit Log（审计日志）：
记录关键写操作：谁做了什么、作用于哪个实体、发生在什么 workspace。
"""

from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 多租户：日志属于哪个 workspace
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)

    # 操作者 user_id
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # 动作名：比如 PROJECT_CREATE / TASK_UPDATE_STATUS 等
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

    # 被作用的实体类型/ID（方便追踪）
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(nullable=True)

    # 附加信息：JSON（如 old/new status、邀请 email、title 等）
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
