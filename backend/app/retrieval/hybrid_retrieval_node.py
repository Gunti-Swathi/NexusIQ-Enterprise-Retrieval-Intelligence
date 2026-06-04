from app.core.config import settings
from app.reranking.cross_encoder import CrossEncoderReranker
from app.retrieval.compression import ContextCompressor
from app.retrieval.confidence import score_retrieval_confidence
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.relevance import keep_relevant_chunks
from app.workflows.conditions import should_compress_context


class HybridRetrievalNode:
    def __init__(
        self,
        retriever: HybridRetriever,
        reranker: CrossEncoderReranker,
        compressor: ContextCompressor,
    ) -> None:
        self.retriever = retriever
        self.reranker = reranker
        self.compressor = compressor

    async def run(self, user_query: str, queries: list[str], top_k: int, query_type: str = "answer") -> dict:
        retrieval_k = max(top_k, settings.hybrid_top_k, 20)
        retrieved = await self.retriever.retrieve_queries(queries, top_k=retrieval_k)
        reranked_all = await self.reranker.rerank(user_query, retrieved, top_k=min(retrieval_k, len(retrieved)))
        reranked = self._ensure_semantic_coverage(keep_relevant_chunks(user_query, reranked_all), top_k)
        confidence = score_retrieval_confidence(reranked)
        compress_context = should_compress_context(query_type, retrieved, top_k)
        selected = reranked
        if compress_context:
            selected = await self.compressor.compress(user_query, reranked, max_chunks=min(top_k, settings.hybrid_top_k))
        return {
            "retrieved_chunks": retrieved,
            "reranked_chunks": reranked,
            "compressed_context": selected,
            "selected_context": selected,
            "retrieval_confidence": confidence,
            "should_compress_context": compress_context,
            "retrieval_debug": {
                "original_query": user_query,
                "expanded_queries": queries,
                "retrieved_chunks": retrieved,
                "reranked_chunks": reranked,
                "selected_context": selected,
                "retrieval_confidence": confidence,
            },
            "chunks": selected,
        }

    def _ensure_semantic_coverage(self, chunks: list[dict], top_k: int) -> list[dict]:
        selected = list(chunks[:top_k])
        if any(float(chunk.get("semantic_score", 0.0)) > 0 for chunk in selected):
            return selected

        semantic_candidate = next(
            (chunk for chunk in chunks[top_k:] if float(chunk.get("semantic_score", 0.0)) > 0),
            None,
        )
        if not semantic_candidate:
            return selected
        if not selected:
            return [semantic_candidate]
        return [*selected[:-1], semantic_candidate]
