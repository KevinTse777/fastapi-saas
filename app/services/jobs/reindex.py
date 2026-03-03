from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.rag.ingest import ingest_document_content


def reindex_document(db: Session, document: Document) -> Document:
    if not document.storage_path:
        raise ValueError("Document has no persisted storage path")
    content = Path(document.storage_path).read_text(encoding="utf-8")
    return ingest_document_content(db, document, content)
