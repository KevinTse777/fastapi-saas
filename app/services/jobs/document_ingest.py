from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.rag.ingest import ingest_document_content


def run_document_ingest(db: Session, document: Document, content: str) -> Document:
    return ingest_document_content(db, document, content)
