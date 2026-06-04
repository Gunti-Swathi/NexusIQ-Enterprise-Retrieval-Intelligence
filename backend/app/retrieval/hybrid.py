from app.core.config import settings
from app.core.llm import GeminiClient
from app.database.store import DocumentStore
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.vector_store import VectorStore


class HybridRetriever:
    def __init__(self, store: DocumentStore, llm: GeminiClient, vector_store: VectorStore) -> None:
        self.store = store
        self.llm = llm
        self.vector_store = vector_store

    async def retrieve(self, question: str, top_k: int | None = None, use_multi_query: bool = True) -> list[dict]:
        target_k = top_k or settings.hybrid_top_k
        queries = [question]
        if use_multi_query:
            expanded = await self.llm.expand_queries(question, count=3)
            queries = list(dict.fromkeys([question, *expanded]))
        return await self.retrieve_queries(queries, target_k)

    async def retrieve_queries(self, queries: list[str], top_k: int | None = None) -> list[dict]:
        target_k = top_k or settings.hybrid_top_k
        all_chunks = await self.store.list_chunks()
        bm25 = BM25Retriever(all_chunks)
        combined: dict[str, dict[str, float]] = {}
        rank_constant = 60

        for query in queries:
            query_embedding = await self.llm.embed_text(query, task_type="retrieval_query")
            semantic_hits = await self.vector_store.query(query_embedding, settings.semantic_top_k)
            semantic_hits = self._normalize_scores(semantic_hits)
            keyword_hits = bm25.search(query, settings.keyword_top_k)
            for rank, hit in enumerate(semantic_hits, start=1):
                scores = combined.setdefault(hit["id"], {"semantic_score": 0.0, "bm25_score": 0.0, "hybrid_score": 0.0})
                scores["semantic_score"] = max(scores["semantic_score"], max(0.0, hit["score"]))
                scores["hybrid_score"] += 0.70 / (rank_constant + rank)
            for rank, hit in enumerate(keyword_hits, start=1):
                scores = combined.setdefault(hit["id"], {"semantic_score": 0.0, "bm25_score": 0.0, "hybrid_score": 0.0})
                scores["bm25_score"] = max(scores["bm25_score"], hit["score"])
                scores["hybrid_score"] += 0.30 / (rank_constant + rank)

        ranked_ids = self._ranked_ids(combined, target_k)
        ranked_ids = self._ensure_semantic_coverage(ranked_ids, combined, target_k)
        max_hybrid_score = max([combined[chunk_id]["hybrid_score"] for chunk_id in ranked_ids], default=1.0) or 1.0
        rows = await self.store.get_chunks_by_ids(ranked_ids)
        row_by_id = {row["id"]: row for row in rows}
        return [
            {
                **row_by_id[chunk_id],
                "semantic_score": round(combined[chunk_id]["semantic_score"], 4),
                "bm25_score": round(combined[chunk_id]["bm25_score"], 4),
                "hybrid_score": round(combined[chunk_id]["hybrid_score"] / max_hybrid_score, 4),
                "score": round(combined[chunk_id]["hybrid_score"] / max_hybrid_score, 4),
            }
            for chunk_id in ranked_ids
            if chunk_id in row_by_id
        ]

    def _ranked_ids(self, combined: dict[str, dict[str, float]], top_k: int) -> list[str]:
        return [
            chunk_id
            for chunk_id, _ in sorted(combined.items(), key=lambda item: item[1]["hybrid_score"], reverse=True)[:top_k]
        ]

    def _normalize_scores(self, hits: list[dict]) -> list[dict]:
        max_score = max([max(0.0, float(hit.get("score", 0.0))) for hit in hits], default=0.0)
        if max_score <= 0:
            return hits
        return [
            {
                **hit,
                "score": max(0.0, float(hit.get("score", 0.0))) / max_score,
            }
            for hit in hits
        ]

    def _ensure_semantic_coverage(
        self,
        ranked_ids: list[str],
        combined: dict[str, dict[str, float]],
        top_k: int,
    ) -> list[str]:
        semantic_ranked = [
            chunk_id
            for chunk_id, scores in sorted(combined.items(), key=lambda item: item[1]["semantic_score"], reverse=True)
            if scores["semantic_score"] > 0
        ]
        if not semantic_ranked:
            return ranked_ids

        minimum_semantic = max(1, min(top_k, round(top_k * 0.35)))
        selected = list(ranked_ids)
        selected_semantic_count = sum(1 for chunk_id in selected if combined[chunk_id]["semantic_score"] > 0)
        for chunk_id in semantic_ranked:
            if selected_semantic_count >= minimum_semantic:
                break
            if chunk_id in selected:
                continue
            keyword_only_tail = next(
                (
                    index
                    for index in range(len(selected) - 1, -1, -1)
                    if combined[selected[index]]["semantic_score"] <= 0
                ),
                None,
            )
            if keyword_only_tail is None:
                break
            selected[keyword_only_tail] = chunk_id
            selected_semantic_count += 1
        return selected[:top_k]
