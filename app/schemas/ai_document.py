from datetime import datetime

from pydantic import BaseModel


class DocumentCreateIn(BaseModel):
    filename: str | None = None
    content: str
    content_type: str = "text/plain"


class DocumentOut(BaseModel):
    id: int
    workspace_id: int
    uploaded_by: int
    filename: str
    content_type: str
    source_type: str
    status: str
    chunk_count: int
    error_message: str | None
    created_at: datetime


class RetrievedChunkOut(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    content: str
    score: float
    metadata: dict | None


class CitationOut(BaseModel):
    document_id: int
    filename: str
    chunk_id: int
    snippet: str

