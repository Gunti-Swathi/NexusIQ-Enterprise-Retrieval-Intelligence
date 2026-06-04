import importlib.util

import pytest

if importlib.util.find_spec("pydantic_settings") is None:
    pytest.skip("Full backend dependencies are not installed in this Python environment.", allow_module_level=True)

from app.evaluation.evaluation_node import EvaluationNode
from app.generation.answer_generation_node import AnswerGenerationNode
from app.reranking.cross_encoder import CrossEncoderReranker
from app.retrieval.hybrid_retrieval_node import HybridRetrievalNode
from app.workflows.graph import DocumentSearchGraph
from app.workflows.multi_query_expansion_node import MultiQueryExpansionNode
from app.workflows.query_processing_node import QueryProcessingNode


class DummyRetriever:
    async def retrieve_queries(self, queries, top_k):
        return []


class DummyCompressor:
    async def compress(self, question, chunks, max_chunks):
        return chunks[:max_chunks]


class DummyEvaluation:
    async def evaluate(self, question, answer, contexts, ground_truth):
        return []


class DummyRecommendations:
    async def recommend(self, question, answer, chunks):
        return []


class DummyLlm:
    async def expand_queries(self, question, count):
        return []


def test_langgraph_builds_without_state_key_collisions():
    graph = DocumentSearchGraph(
        query_processor=QueryProcessingNode(),
        query_expander=MultiQueryExpansionNode(DummyLlm()),
        retriever=HybridRetrievalNode(DummyRetriever(), CrossEncoderReranker(), DummyCompressor()),
        answer_generator=AnswerGenerationNode(llm=None),
        evaluator=EvaluationNode(DummyEvaluation()),
        recommender=DummyRecommendations(),
    )
    assert graph.graph is not None
