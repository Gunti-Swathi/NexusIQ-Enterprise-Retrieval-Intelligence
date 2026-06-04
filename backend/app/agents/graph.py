from app.workflows.graph import DocumentSearchGraph as WorkflowDocumentSearchGraph


class DocumentSearchGraph(WorkflowDocumentSearchGraph):
    def __init__(self, *args, **kwargs) -> None:
        if "router" not in kwargs:
            super().__init__(*args, **kwargs)
            return

        super().__init__(
            query_processor=kwargs["router"],
            query_expander=_LegacyQueryExpansionNode(),
            retriever=_LegacyRetrievalNode(kwargs["retriever"]),
            answer_generator=_LegacyAnswerGenerationNode(kwargs["answerer"]),
            evaluator=_LegacyEvaluationNode(kwargs["evaluator"]),
            recommender=kwargs["recommender"],
        )


class _LegacyQueryExpansionNode:
    async def run(self, user_query: str, use_multi_query: bool) -> dict:
        return {"expanded_queries": [user_query]}


class _LegacyRetrievalNode:
    def __init__(self, retriever) -> None:
        self.retriever = retriever

    async def run(self, user_query: str, queries: list[str], top_k: int) -> dict:
        chunks = await self.retriever.run(user_query, top_k, use_multi_query=True)
        return {
            "retrieved_chunks": chunks,
            "reranked_chunks": chunks,
            "compressed_context": chunks,
            "chunks": chunks,
        }


class _LegacyAnswerGenerationNode:
    def __init__(self, answerer) -> None:
        self.answerer = answerer

    async def run(self, user_query: str, chunks: list[dict]) -> dict:
        answer, citations = await self.answerer.run(user_query, chunks)
        return {"generated_answer": answer, "answer": answer, "citations": citations}


class _LegacyEvaluationNode:
    def __init__(self, evaluator) -> None:
        self.evaluator = evaluator

    async def run(self, user_query: str, answer: str, chunks: list[dict]) -> dict:
        scores = await self.evaluator.run(user_query, answer, chunks)
        return {"evaluation_scores": scores, "evaluation": scores}


__all__ = ["DocumentSearchGraph"]
