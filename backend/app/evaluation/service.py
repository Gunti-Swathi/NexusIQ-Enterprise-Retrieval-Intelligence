from collections import Counter
from typing import Any


class EvaluationService:
    def __init__(self, llm: Any) -> None:
        self.llm = llm

    async def evaluate(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: str | None,
    ) -> list[dict]:
        if not answer:
            return self._fallback_metrics(question, answer, contexts, ground_truth)
        settings = _settings()
        if not settings.google_api_key:
            return self._fallback_metrics(
                question,
                answer,
                contexts,
                ground_truth,
                "Gemini API key is not configured for RAGAS judging.",
            )
        try:
            return await self._gemini_judge_metrics(question, answer, contexts, ground_truth)
        except Exception as exc:
            return self._fallback_metrics(question, answer, contexts, ground_truth, f"Gemini judge failed: {exc}")

    async def _gemini_judge_metrics(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: str | None,
    ) -> list[dict]:
        import json

        prompt = f"""
You are a strict RAG evaluation judge.
Score the answer from 0.0 to 1.0 for:
- faithfulness: answer is supported by retrieved context
- answer_relevancy: answer directly addresses the question
- context_precision: retrieved context is focused and useful
- context_recall: retrieved context contains enough information to answer

Return only valid JSON with numeric keys:
{{"faithfulness": 0.0, "answer_relevancy": 0.0, "context_precision": 0.0, "context_recall": 0.0}}

Question:
{question}

Answer:
{answer}

Retrieved context:
{chr(10).join(f"- {context}" for context in contexts)}

Ground truth, if provided:
{ground_truth or ""}
""".strip()
        raw = await self.llm.generate(prompt, temperature=0.0)
        scores = json.loads(raw.strip().strip("`").removeprefix("json").strip())
        return [
            {"name": "faithfulness", "score": _as_float(scores.get("faithfulness")), "reason": "Gemini judge: faithfulness score."},
            {"name": "answer_relevancy", "score": _as_float(scores.get("answer_relevancy")), "reason": "Gemini judge: answer relevancy score."},
            {"name": "context_precision", "score": _as_float(scores.get("context_precision")), "reason": "Gemini judge: context precision score."},
            {"name": "context_recall", "score": _as_float(scores.get("context_recall")), "reason": "Gemini judge: context recall score."},
        ]

    def _fallback_metrics(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: str | None,
        failure_reason: str = "RAGAS judge setup is unavailable.",
    ) -> list[dict]:
        context_text = " ".join(contexts)
        answer_overlap = _overlap(answer, context_text)
        question_overlap = _overlap(question, answer)
        truth_overlap = _overlap(ground_truth or answer, context_text)
        has_context = 1.0 if contexts else 0.0
        return [
            {"name": "faithfulness", "score": round(answer_overlap, 3), "reason": f"Local quality estimate: answer overlap with retrieved context. {failure_reason}"},
            {"name": "answer_relevancy", "score": round(question_overlap, 3), "reason": f"Local quality estimate: question overlap with answer. {failure_reason}"},
            {"name": "context_precision", "score": round((answer_overlap + has_context) / 2, 3), "reason": f"Local quality estimate: retrieved context support. {failure_reason}"},
            {"name": "context_recall", "score": round(truth_overlap, 3), "reason": f"Local quality estimate: context coverage. {failure_reason}"},
        ]


def _overlap(left: str, right: str) -> float:
    left_tokens = [token.lower() for token in left.split() if len(token) > 3]
    right_tokens = Counter(token.lower() for token in right.split() if len(token) > 3)
    if not left_tokens:
        return 0.0
    hits = sum(1 for token in left_tokens if right_tokens[token] > 0)
    return hits / len(left_tokens)


def _as_float(value) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _settings():
    from app.core.config import settings

    return settings
