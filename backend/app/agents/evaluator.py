from app.evaluation.evaluation_node import EvaluationNode


class EvaluatorAgent(EvaluationNode):
    async def run(self, question: str, answer: str, chunks: list[dict]) -> list[dict]:
        result = await super().run(question, answer, chunks)
        return result["evaluation_scores"]
