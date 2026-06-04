from pydantic import BaseModel, Field

from app.schemas.documents import ChunkOut


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=8, ge=1, le=20)
    use_multi_query: bool = True


class Citation(BaseModel):
    source_number: int
    file_name: str
    document_id: str
    chunk_indices: list[int]
    chunk_ids: list[str]
    page_number: int | None = None


class Recommendation(BaseModel):
    kind: str
    title: str
    document_id: str | None = None
    chunk_id: str | None = None
    reason: str
    score: float | None = None


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved_chunks: list[ChunkOut]
    recommendations: list[Recommendation]
    contradictions: list[dict] = []
    citation_validation: dict | None = None
    retrieval_confidence: dict | None = None
    retrieval_debug: dict | None = None
    expanded_queries: list[str] = []
    selected_context: list[ChunkOut] = []
    query_type: str | None = None
    should_expand_query: bool | None = None
    should_compress_context: bool | None = None
    trace_url: str | None = None
