from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import require_role
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.schemas.ai_document import DocumentOut
from app.services.audit import write_audit
from app.services.rag.ingest import create_manual_document, create_uploaded_document

router = APIRouter(tags=["ai-documents"])


def _serialize_document(document: Document) -> DocumentOut:
    return DocumentOut(
        id=document.id,
        workspace_id=document.workspace_id,
        uploaded_by=document.uploaded_by,
        filename=document.filename,
        content_type=document.content_type,
        source_type=document.source_type.value,
        status=document.status.value,
        chunk_count=document.chunk_count,
        error_message=document.error_message,
        created_at=document.created_at,
    )


@router.post("/workspaces/{workspace_id}/documents", response_model=DocumentOut, status_code=201)
async def upload_document(
    workspace_id: int,
    file: UploadFile | None = File(default=None),
    content: str | None = Form(default=None),
    filename: str | None = Form(default=None),
    content_type: str | None = Form(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ = require_role(workspace_id, WorkspaceRole.MEMBER, db, user)

    if file is None and not content:
        raise HTTPException(status_code=400, detail="Provide either a file upload or manual content")

    if file is not None:
        raw = await file.read()
        document = create_uploaded_document(
            db,
            workspace_id=workspace_id,
            user_id=user.id,
            filename=file.filename or "uploaded.txt",
            content=raw,
            content_type=file.content_type or "application/octet-stream",
        )
    else:
        document = create_manual_document(
            db,
            workspace_id=workspace_id,
            user_id=user.id,
            filename=filename or "manual-note.txt",
            content=content or "",
            content_type=content_type or "text/plain",
        )

    write_audit(
        db=db,
        workspace_id=workspace_id,
        actor_id=user.id,
        action="DOCUMENT_UPLOAD",
        entity_type="document",
        entity_id=document.id,
        meta={"filename": document.filename, "status": document.status.value},
    )
    db.commit()
    return _serialize_document(document)


@router.get("/workspaces/{workspace_id}/documents", response_model=list[DocumentOut])
def list_documents(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ = require_role(workspace_id, WorkspaceRole.GUEST, db, user)
    rows = db.execute(
        select(Document)
        .where(Document.workspace_id == workspace_id)
        .order_by(Document.id.desc())
    ).scalars().all()
    return [_serialize_document(document) for document in rows]
