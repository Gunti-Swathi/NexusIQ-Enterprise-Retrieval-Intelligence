import re

from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


class BM25Retriever:
    def __init__(self, chunks: list[dict]) -> None:
        self.chunks = chunks
        self.tokens = [tokenize(chunk["text"]) for chunk in chunks]
        self.index = BM25Okapi(self.tokens) if self.tokens else None

    def search(self, query: str, top_k: int) -> list[dict]:
        if not self.index:
            return []
        scores = self.index.get_scores(tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:top_k]
        max_score = max([score for _, score in ranked], default=1.0) or 1.0
        return [
            {"id": self.chunks[index]["id"], "score": float(score / max_score)}
            for index, score in ranked
            if score > 0
        ]
