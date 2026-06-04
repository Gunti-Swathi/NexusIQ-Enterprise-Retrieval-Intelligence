from typing import TypedDict


class RagGraphState(TypedDict, total=False):
    user_query: str
    query_type: str
    expanded_queries: list[str]
    retrieved_chunks: list[dict]
    reranked_chunks: list[dict]
    compressed_context: list[dict]
    generated_answer: str
    citations: list[dict]
    citation_validation: dict
    evaluation_scores: list[dict]
    recommendations: list[dict]
    contradictions: list[dict]
    retrieval_confidence: dict
    retrieval_debug: dict
    query_analysis: dict
    should_expand_query: bool
    should_compress_context: bool
    selected_context: list[dict]
    trace_url: str | None
    top_k: int
    use_multi_query: bool

    # Backward-compatible aliases used by existing API serializers and tests.
    question: str
    route: str
    chunks: list[dict]
    answer: str
    evaluation: list[dict]
