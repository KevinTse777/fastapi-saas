"""
Workspace 多租户核心模型：
- Workspace：一个团队/空间
- WorkspaceMember：用户在某个 workspace 中的角色
- Invite：邀请记录（token + 过期 + 状态）
"""

from __future__ import annotations

from datetime import datetime
import enum

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Enum,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkspaceRole(str, enum.Enum):
    """
    角色枚举（Day3 先做最小集合）
    Day5 会扩展 RBAC 校验逻辑
    """
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    GUEST = "GUEST"


class InviteStatus(str, enum.Enum):
    """
    邀请状态
    """
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # workspace 名称
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    # workspace 的拥有者（用于展示/归属；权限仍以 member.role 为准）
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # 关系字段（可选，方便查询；不写也不影响）
    members: Mapped[list["WorkspaceMember"]] = relationship(back_populates="workspace")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        # 同一 workspace 中一个 user 只能出现一次
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # 角色：OWNER / ADMIN / MEMBER / GUEST
    role: Mapped[WorkspaceRole] = mapped_column(
        Enum(WorkspaceRole),
        nullable=False,
        default=WorkspaceRole.MEMBER,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="members")


class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)

    # 被邀请人的邮箱（我们 Day3 采用：只有邮箱匹配的登录用户才能接受）
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # 邀请 token（随机字符串）
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    status: Mapped[InviteStatus] = mapped_column(
        Enum(InviteStatus),
        nullable=False,
        default=InviteStatus.PENDING,
    )

    # 过期时间
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
