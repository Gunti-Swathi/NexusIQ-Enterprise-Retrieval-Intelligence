from typing import Any

from app.core.config import settings
from app.retrieval.vector_store import VectorStore


class RecommendationService:
    def __init__(self, llm: Any, vector_store: VectorStore) -> None:
        self.llm = llm
        self.vector_store = vector_store

    async def recommend(self, question: str, answer: str, chunks: list[dict]) -> list[dict]:
        seed = " ".join([question, answer, *[chunk["text"][:300] for chunk in chunks[:3]]])
        embedding = await self.llm.embed_text(seed, task_type="retrieval_query")
        hits = await self.vector_store.query(embedding, settings.recommendation_top_k + len(chunks))
        used = {chunk["id"] for chunk in chunks}
        output = []
        for hit in hits:
            if hit["id"] in used:
                continue
            metadata = hit.get("metadata") or {}
            output.append(
                {
                    "kind": "related_chunk",
                    "title": metadata.get("filename", "Related document"),
                    "document_id": metadata.get("document_id"),
                    "chunk_id": hit["id"],
                    "reason": "Semantically close to the retrieved evidence and answer.",
                    "score": round(hit["score"], 4),
                }
            )
            if len(output) >= settings.recommendation_top_k:
                break
        if chunks:
            output.insert(
                0,
                {
                    "kind": "supporting_document",
                    "title": chunks[0]["filename"],
                    "document_id": chunks[0]["document_id"],
                    "chunk_id": chunks[0]["id"],
                    "reason": "Highest-scoring source used for the grounded answer.",
                    "score": chunks[0].get("score"),
                },
            )
        return output
