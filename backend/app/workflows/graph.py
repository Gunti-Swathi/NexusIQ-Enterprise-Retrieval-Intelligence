import os

from app.evaluation.evaluation_node import EvaluationNode
from app.evaluation.citation_checker import CitationChecker
from app.generation.answer_generation_node import AnswerGenerationNode
from app.recommendations.service import RecommendationService
from app.recommendations.contradiction_detector import ContradictionDetector
from app.retrieval.hybrid_retrieval_node import HybridRetrievalNode
from app.workflows.multi_query_expansion_node import MultiQueryExpansionNode
from app.workflows.query_processing_node import QueryProcessingNode
from app.workflows.state import RagGraphState


class DocumentSearchGraph:
    def __init__(
        self,
        query_processor: QueryProcessingNode,
        query_expander: MultiQueryExpansionNode,
        retriever: HybridRetrievalNode,
        answer_generator: AnswerGenerationNode,
        evaluator: EvaluationNode,
        recommender: RecommendationService,
        citation_checker: CitationChecker | None = None,
        contradiction_detector: ContradictionDetector | None = None,
    ) -> None:
        self.query_processor = query_processor
        self.query_expander = query_expander
        self.retriever = retriever
        self.answer_generator = answer_generator
        self.evaluator = evaluator
        self.recommender = recommender
        self.citation_checker = citation_checker or CitationChecker()
        self.contradiction_detector = contradiction_detector or ContradictionDetector()
        self.graph = self._build_graph()

    def _build_graph(self):
        try:
            from langgraph.graph import END, StateGraph
        except Exception:
            return None

        graph = StateGraph(RagGraphState)

        async def query_processing_node(state: RagGraphState) -> RagGraphState:
            return await self.query_processor.run(state["user_query"])

        async def multi_query_expansion_node(state: RagGraphState) -> RagGraphState:
            return await self.query_expander.run(
                state["user_query"],
                state.get("use_multi_query", True),
                state.get("should_expand_query", True),
            )

        async def hybrid_retrieval_node(state: RagGraphState) -> RagGraphState:
            return await self.retriever.run(
                state["user_query"],
                state.get("expanded_queries", [state["user_query"]]),
                state.get("top_k", 8),
                state.get("query_type", "answer"),
            )

        async def answer_generation_node(state: RagGraphState) -> RagGraphState:
            return await self.answer_generator.run(state["user_query"], state.get("compressed_context", []))

        async def evaluation_node(state: RagGraphState) -> RagGraphState:
            return await self.evaluator.run(
                state["user_query"],
                state.get("generated_answer", ""),
                state.get("compressed_context", []),
            )

        async def citation_validation_node(state: RagGraphState) -> RagGraphState:
            return {
                "citation_validation": await self.citation_checker.validate(
                    state.get("generated_answer", ""),
                    state.get("citations", []),
                    state.get("compressed_context", []),
                )
            }

        async def contradiction_detection_node(state: RagGraphState) -> RagGraphState:
            if state.get("query_type") not in {"contradiction", "comparison"}:
                return {"contradictions": []}
            return {
                "contradictions": await self.contradiction_detector.detect(
                    state["user_query"],
                    state.get("compressed_context", []),
                )
            }

        async def recommendation_node(state: RagGraphState) -> RagGraphState:
            return {
                "recommendations": await self.recommender.recommend(
                    state["user_query"],
                    state.get("generated_answer", ""),
                    state.get("compressed_context", []),
                )
            }

        graph.add_node("query_processing_node", query_processing_node)
        graph.add_node("multi_query_expansion_node", multi_query_expansion_node)
        graph.add_node("hybrid_retrieval_node", hybrid_retrieval_node)
        graph.add_node("answer_generation_node", answer_generation_node)
        graph.add_node("citation_validation_node", citation_validation_node)
        graph.add_node("contradiction_detection_node", contradiction_detection_node)
        graph.add_node("evaluation_node", evaluation_node)
        graph.add_node("recommendation_node", recommendation_node)
        graph.set_entry_point("query_processing_node")
        graph.add_edge("query_processing_node", "multi_query_expansion_node")
        graph.add_edge("multi_query_expansion_node", "hybrid_retrieval_node")
        graph.add_edge("hybrid_retrieval_node", "answer_generation_node")
        graph.add_edge("answer_generation_node", "citation_validation_node")
        graph.add_edge("citation_validation_node", "contradiction_detection_node")
        graph.add_edge("contradiction_detection_node", "recommendation_node")
        graph.add_edge("recommendation_node", "evaluation_node")
        graph.add_edge("evaluation_node", END)
        return graph.compile()

    async def ask(self, question: str, top_k: int, use_multi_query: bool) -> RagGraphState:
        state: RagGraphState = {
            "user_query": question,
            "question": question,
            "top_k": top_k,
            "use_multi_query": use_multi_query,
        }
        if self.graph:
            result = await self.graph.ainvoke(state)
        else:
            processed = await self.query_processor.run(question)
            expanded = await self.query_expander.run(processed["user_query"], use_multi_query, processed["should_expand_query"])
            retrieved = await self.retriever.run(
                processed["user_query"],
                expanded["expanded_queries"],
                top_k,
                processed["query_type"],
            )
            answer = await self.answer_generator.run(processed["user_query"], retrieved["compressed_context"])
            citation_validation = {
                "citation_validation": await self.citation_checker.validate(
                    answer["generated_answer"],
                    answer["citations"],
                    retrieved["compressed_context"],
                )
            }
            contradiction_items = []
            if processed["query_type"] in {"contradiction", "comparison"}:
                contradiction_items = await self.contradiction_detector.detect(
                    processed["user_query"],
                    retrieved["compressed_context"],
                )
            contradictions = {"contradictions": contradiction_items}
            evaluation = await self.evaluator.run(
                processed["user_query"],
                answer["generated_answer"],
                retrieved["compressed_context"],
            )
            recommendations = await self.recommender.recommend(
                processed["user_query"],
                answer["generated_answer"],
                retrieved["compressed_context"],
            )
            result = {
                **state,
                **processed,
                **expanded,
                **retrieved,
                **answer,
                **citation_validation,
                **contradictions,
                **evaluation,
                "recommendations": recommendations,
            }
        result["trace_url"] = _langsmith_project_url()
        return result


def _langsmith_project_url() -> str | None:
    project = os.getenv("LANGSMITH_PROJECT")
    if not project:
        return None
    return f"https://smith.langchain.com/o/default/projects/p/{project}"
