from __future__ import annotations

from pathlib import Path
import uuid

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentChunk, DocumentStatus, DocumentSourceType
from app.services.rag.chunking import split_text
from app.services.rag.embeddings import estimate_token_count


def ensure_storage_dir() -> Path:
    storage = Path(settings.ai_storage_dir)
    storage.mkdir(parents=True, exist_ok=True)
    return storage


def save_uploaded_bytes(filename: str, content: bytes) -> str:
    storage = ensure_storage_dir()
    safe_name = f"{uuid.uuid4().hex}_{Path(filename).name}"
    path = storage / safe_name
    path.write_bytes(content)
    return str(path)


def ingest_document_content(
    db: Session,
    document: Document,
    content: str,
) -> Document:
    document.status = DocumentStatus.PARSING
    document.error_message = None
    db.commit()

    chunks = split_text(content)
    db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
    db.flush()

    for index, chunk_text in enumerate(chunks):
        db.add(
            DocumentChunk(
                document_id=document.id,
                workspace_id=document.workspace_id,
                chunk_index=index,
                content=chunk_text,
                token_count=estimate_token_count(chunk_text),
                metadata_json={
                    "workspace_id": document.workspace_id,
                    "document_id": document.id,
                    "source": document.source_type.value,
                    "filename": document.filename,
                },
            )
        )

    document.chunk_count = len(chunks)
    document.status = DocumentStatus.INDEXED if chunks else DocumentStatus.FAILED
    document.error_message = None if chunks else "No parsable content found"
    db.commit()
    db.refresh(document)
    return document


def create_manual_document(
    db: Session,
    workspace_id: int,
    user_id: int,
    filename: str,
    content: str,
    content_type: str,
) -> Document:
    document = Document(
        workspace_id=workspace_id,
        uploaded_by=user_id,
        filename=filename,
        storage_path=None,
        content_type=content_type,
        source_type=DocumentSourceType.MANUAL,
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return ingest_document_content(db, document, content)


def create_uploaded_document(
    db: Session,
    workspace_id: int,
    user_id: int,
    filename: str,
    content: bytes,
    content_type: str,
) -> Document:
    storage_path = save_uploaded_bytes(filename, content)
    document = Document(
        workspace_id=workspace_id,
        uploaded_by=user_id,
        filename=filename,
        storage_path=storage_path,
        content_type=content_type,
        source_type=DocumentSourceType.UPLOAD,
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError:
        document.status = DocumentStatus.FAILED
        document.error_message = "Only UTF-8 text-like files are supported in this MVP"
        db.commit()
        db.refresh(document)
        return document

    return ingest_document_content(db, document, decoded)
