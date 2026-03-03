from __future__ import annotations

from datetime import datetime
import enum

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class AgentMessageRole(str, enum.Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"
    TOOL = "tool"


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    triggered_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AgentRunStatus] = mapped_column(
        Enum(AgentRunStatus),
        nullable=False,
        default=AgentRunStatus.PENDING,
    )
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    final_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    audit_log_id: Mapped[int | None] = mapped_column(ForeignKey("audit_logs.id"), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("agent_runs.id"), nullable=False, index=True)
    role: Mapped[AgentMessageRole] = mapped_column(
        Enum(AgentMessageRole),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tool_input_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tool_output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
