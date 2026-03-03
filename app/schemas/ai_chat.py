from pydantic import BaseModel, Field

from app.schemas.ai_document import CitationOut, RetrievedChunkOut


class ChatRequestIn(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    top_k: int = 5


class ChatResponseOut(BaseModel):
    answer: str
    citations: list[CitationOut]
    retrieved_chunks: list[RetrievedChunkOut]
    trace_id: str

