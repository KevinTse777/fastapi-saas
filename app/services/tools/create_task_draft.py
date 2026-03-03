from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.llm.client import get_llm_provider
from app.services.rag.retriever import retrieve_workspace_chunks


def create_task_draft(
    db: Session,
    workspace_id: int,
    project_id: int,
    requirement: str,
    document_ids: list[int] | None = None,
) -> dict:
    contexts = retrieve_workspace_chunks(
        db,
        workspace_id=workspace_id,
        query=requirement,
        top_k=3,
        document_ids=document_ids,
    )
    provider = get_llm_provider()
    drafts = provider.draft_tasks(requirement, contexts)
    return {
        "tool_name": "create_task_draft",
        "summary": f"Generated {len(drafts)} task drafts for project {project_id}.",
        "drafts": drafts,
        "contexts": contexts,
    }
