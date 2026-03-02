"""
Task（任务）模型：
- 归属 project（从而间接归属 workspace）
- status 用枚举：TODO / DOING / DONE / BLOCKED
- assignee_id 可为空（未指派）
"""

from __future__ import annotations

from datetime import datetime, date
import enum

from sqlalchemy import (
    String,
    Text,
    DateTime,
    Date,
    ForeignKey,
    Enum,
    Integer,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskStatus(str, enum.Enum):
    TODO = "TODO"
    DOING = "DOING"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 任务属于某个 project
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    # 描述可选
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.TODO,
    )

    # 简单优先级（数字越大优先级越高），可选
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 指派人（用户 id），可为空
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # 截止日期（可为空）
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
