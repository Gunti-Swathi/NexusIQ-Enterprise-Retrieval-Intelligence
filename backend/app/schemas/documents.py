from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    chunk_count: int
    created_at: datetime


class ChunkOut(BaseModel):
    id: str
    document_id: str
    filename: str
    chunk_index: int
    text: str
    score: float | None = None
    semantic_score: float | None = None
    bm25_score: float | None = None
    hybrid_score: float | None = None
    rerank_score: float | None = None
    query_relevance: float | None = None
    page_number: int | None = None
    section: str | None = None
    source_number: int | None = None


class DocumentsResponse(BaseModel):
    documents: list[DocumentOut]
