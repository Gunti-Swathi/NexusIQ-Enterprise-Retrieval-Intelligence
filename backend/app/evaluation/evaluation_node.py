from app.evaluation.service import EvaluationService


class EvaluationNode:
    def __init__(self, service: EvaluationService) -> None:
        self.service = service

    async def run(self, user_query: str, answer: str, chunks: list[dict]) -> dict:
        scores = await self.service.evaluate(
            question=user_query,
            answer=answer,
            contexts=[chunk["text"] for chunk in chunks],
            ground_truth=None,
        )
        return {"evaluation_scores": scores, "evaluation": scores}
