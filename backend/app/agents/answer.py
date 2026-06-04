from app.generation.answer_generation_node import AnswerGenerationNode


class AnswerAgent(AnswerGenerationNode):
    async def run(self, question: str, chunks: list[dict]) -> tuple[str, list[dict]]:
        result = await super().run(question, chunks)
        return result["generated_answer"], result["citations"]
