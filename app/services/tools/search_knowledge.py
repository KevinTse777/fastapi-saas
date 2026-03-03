from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.rag.retriever import retrieve_workspace_chunks


def search_knowledge(
    db: Session,
    workspace_id: int,
    query: str,
    top_k: int = 3,
    document_ids: list[int] | None = None,
) -> dict:
    chunks = retrieve_workspace_chunks(db, workspace_id, query, top_k=top_k, document_ids=document_ids)
    return {
        "tool_name": "search_knowledge",
        "summary": f"Retrieved {len(chunks)} knowledge chunks for the workspace query.",
        "chunks": chunks,
    }
