import asyncio
import hashlib
import json
import sqlite3
from pathlib import Path

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


class GeminiClient:
    def __init__(self) -> None:
        if settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)
        self.generation_model = settings.gemini_generation_model
        self.embedding_model = settings.gemini_embedding_model
        self.cache = EmbeddingCache(settings.embedding_cache_path)

    async def generate(self, prompt: str, temperature: float = 0.1) -> str:
        if not settings.google_api_key:
            return "Gemini API key is not configured. Set GOOGLE_API_KEY to enable answer generation."

        def _call() -> str:
            model = genai.GenerativeModel(self.generation_model)
            response = model.generate_content(
                prompt,
                generation_config={"temperature": temperature},
            )
            return response.text or ""

        try:
            return await asyncio.to_thread(_call)
        except Exception as exc:
            return f"Gemini generation failed: {exc}"

    async def expand_queries(self, question: str, count: int = 3) -> list[str]:
        prompt = (
            "Generate concise alternative search queries for enterprise document retrieval. "
            "Return only a JSON list of strings.\n"
            f"Question: {question}\nCount: {count}"
        )
        raw = await self.generate(prompt, temperature=0.2)
        try:
            parsed = json.loads(raw.strip().strip("`"))
            if isinstance(parsed, list):
                return [str(item) for item in parsed[:count]]
        except json.JSONDecodeError:
            pass
        return [question]

    async def embed_text(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        cached = self.cache.get(text, task_type)
        if cached:
            return cached
        if not settings.google_api_key:
            # Deterministic local fallback keeps tests and development usable without spending API calls.
            vector = self._fallback_embedding(text)
            self.cache.set(text, task_type, vector)
            return vector

        @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
        def _call() -> list[float]:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type=task_type,
            )
            return list(result["embedding"])

        try:
            vector = await asyncio.to_thread(_call)
        except Exception:
            vector = self._fallback_embedding(text)
        self.cache.set(text, task_type, vector)
        return vector

    async def embed_many(self, texts: list[str], task_type: str = "retrieval_document") -> list[list[float]]:
        return [await self.embed_text(text, task_type=task_type) for text in texts]

    def _fallback_embedding(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [((digest[i % len(digest)] / 255.0) - 0.5) for i in range(768)]


class EmbeddingCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS embeddings (key TEXT PRIMARY KEY, vector TEXT NOT NULL)"
            )

    def _key(self, text: str, task_type: str) -> str:
        payload = f"{settings.gemini_embedding_model}:{task_type}:{text}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def get(self, text: str, task_type: str) -> list[float] | None:
        with sqlite3.connect(self.path) as conn:
            row = conn.execute("SELECT vector FROM embeddings WHERE key = ?", (self._key(text, task_type),)).fetchone()
        return json.loads(row[0]) if row else None

    def set(self, text: str, task_type: str, vector: list[float]) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO embeddings (key, vector) VALUES (?, ?)",
                (self._key(text, task_type), json.dumps(vector)),
            )
