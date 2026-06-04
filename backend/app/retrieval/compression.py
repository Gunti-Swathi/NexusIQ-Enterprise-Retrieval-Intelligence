from typing import Any


class ContextCompressor:
    def __init__(self, llm: Any) -> None:
        self.llm = llm

    async def compress(self, question: str, chunks: list[dict], max_chunks: int) -> list[dict]:
        # Cheap default: keep the highest scoring chunks after retrieval and reranking.
        return sorted(chunks, key=lambda chunk: chunk.get("score", 0), reverse=True)[:max_chunks]
