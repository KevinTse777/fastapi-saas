from __future__ import annotations

from app.schemas.ai_document import CitationOut


def build_citations(retrieved_chunks: list[dict]) -> list[CitationOut]:
    citations: list[CitationOut] = []
    for chunk in retrieved_chunks:
        snippet = chunk["content"][:180]
        citations.append(
            CitationOut(
                document_id=chunk["document_id"],
                filename=chunk["filename"],
                chunk_id=chunk["chunk_id"],
                snippet=snippet,
            )
        )
    return citations
