"""add ai workspace copilot tables

Revision ID: 71e9f5f8c2a1
Revises: 3b1e67e48d54
Create Date: 2026-03-03 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "71e9f5f8c2a1"
down_revision: Union[str, None] = "3b1e67e48d54"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=True),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("source_type", sa.Enum("UPLOAD", "URL", "MANUAL", name="documentsourcetype"), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "PARSING", "INDEXED", "FAILED", name="documentstatus"), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_workspace_id"), "documents", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_documents_uploaded_by"), "documents", ["uploaded_by"], unique=False)

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_chunks_document_id"), "document_chunks", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_chunks_workspace_id"), "document_chunks", ["workspace_id"], unique=False)

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("triggered_by", sa.Integer(), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "RUNNING", "SUCCESS", "FAILED", name="agentrunstatus"), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("final_output", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("audit_log_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["audit_log_id"], ["audit_logs.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["triggered_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_runs_workspace_id"), "agent_runs", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_agent_runs_project_id"), "agent_runs", ["project_id"], unique=False)
    op.create_index(op.f("ix_agent_runs_triggered_by"), "agent_runs", ["triggered_by"], unique=False)
    op.create_index(op.f("ix_agent_runs_trace_id"), "agent_runs", ["trace_id"], unique=False)
    op.create_index(op.f("ix_agent_runs_audit_log_id"), "agent_runs", ["audit_log_id"], unique=False)

    op.create_table(
        "agent_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.Enum("USER", "SYSTEM", "ASSISTANT", "TOOL", name="agentmessagerole"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_name", sa.String(length=120), nullable=True),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("tool_input_json", sa.JSON(), nullable=True),
        sa.Column("tool_output_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["agent_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_messages_run_id"), "agent_messages", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_messages_run_id"), table_name="agent_messages")
    op.drop_table("agent_messages")
    op.drop_index(op.f("ix_agent_runs_audit_log_id"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_trace_id"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_triggered_by"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_project_id"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_workspace_id"), table_name="agent_runs")
    op.drop_table("agent_runs")
    op.drop_index(op.f("ix_document_chunks_workspace_id"), table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_document_id"), table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_index(op.f("ix_documents_uploaded_by"), table_name="documents")
    op.drop_index(op.f("ix_documents_workspace_id"), table_name="documents")
    op.drop_table("documents")
