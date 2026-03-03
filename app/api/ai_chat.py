from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.logging import new_trace_id
from app.core.rbac import require_role
from app.core.telemetry import metrics
from app.db.session import get_db
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.schemas.ai_chat import ChatRequestIn, ChatResponseOut
from app.schemas.ai_document import RetrievedChunkOut
from app.services.llm.client import get_llm_provider
from app.services.rag.citations import build_citations
from app.services.rag.retriever import retrieve_workspace_chunks

router = APIRouter(tags=["ai-chat"])


@router.post("/workspaces/{workspace_id}/ai/chat", response_model=ChatResponseOut)
def workspace_ai_chat(
    workspace_id: int,
    payload: ChatRequestIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ = require_role(workspace_id, WorkspaceRole.GUEST, db, user)
    trace_id = new_trace_id()
    top_k = max(1, min(payload.top_k, 10))
    chunks = retrieve_workspace_chunks(db, workspace_id, payload.question, top_k=top_k)
    provider = get_llm_provider()
    answer = provider.generate_answer(payload.question, chunks)
    metrics.incr("ai_chat_requests")
    if chunks:
        metrics.incr("ai_chat_hits")

    return ChatResponseOut(
        answer=answer,
        citations=build_citations(chunks),
        retrieved_chunks=[
            RetrievedChunkOut(
                chunk_id=item["chunk_id"],
                document_id=item["document_id"],
                filename=item["filename"],
                content=item["content"],
                score=item["score"],
                metadata=item["metadata"],
            )
            for item in chunks
        ],
        trace_id=trace_id,
    )
