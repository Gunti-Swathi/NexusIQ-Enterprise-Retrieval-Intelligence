from app.retrieval.bm25 import tokenize
from app.retrieval.relevance import relevance_score


class CrossEncoderReranker:
    async def rerank(self, query: str, chunks: list[dict], top_k: int) -> list[dict]:
        query_terms = set(tokenize(query))
        if not query_terms:
            return chunks[:top_k]

        reranked = []
        for chunk in chunks:
            chunk_terms = set(tokenize(chunk.get("text", "")))
            lexical_overlap = len(query_terms & chunk_terms) / len(query_terms)
            query_relevance = relevance_score(query, chunk)
            semantic_score = float(chunk.get("semantic_score", 0.0))
            fused_score = (
                0.55 * float(chunk.get("hybrid_score", chunk.get("score", 0.0)))
                + 0.20 * semantic_score
                + 0.10 * lexical_overlap
                + 0.15 * query_relevance
            )
            reranked.append(
                {
                    **chunk,
                    "query_relevance": round(query_relevance, 4),
                    "score": round(fused_score, 4),
                    "rerank_score": round(fused_score, 4),
                }
            )
        return sorted(reranked, key=lambda chunk: chunk.get("rerank_score", 0.0), reverse=True)[:top_k]
