from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk, DocumentStatus
from app.services.rag.reranker import rerank_chunks


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9_\-\u4e00-\u9fff]+", text.lower()) if len(token) > 1}


def retrieve_workspace_chunks(
    db: Session,
    workspace_id: int,
    query: str,
    top_k: int,
    document_ids: list[int] | None = None,
) -> list[dict]:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    stmt = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.workspace_id == workspace_id,
            Document.status == DocumentStatus.INDEXED,
        )
    )
    if document_ids:
        stmt = stmt.where(Document.id.in_(document_ids))

    rows = db.execute(stmt).all()
    scored: list[dict] = []
    for chunk, document in rows:
        chunk_tokens = _tokenize(chunk.content)
        overlap = query_tokens & chunk_tokens
        if not overlap:
            continue
        score = len(overlap) / max(len(query_tokens), 1)
        scored.append(
            {
                "chunk_id": chunk.id,
                "document_id": document.id,
                "filename": document.filename,
                "content": chunk.content,
                "score": round(score, 4),
                "metadata": chunk.metadata_json or {},
            }
        )
    return rerank_chunks(scored)[:top_k]
