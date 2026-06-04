import importlib.util

import pytest

if importlib.util.find_spec("pydantic_settings") is None or importlib.util.find_spec("chromadb") is None:
    pytest.skip("Full backend dependencies are not installed in this Python environment.", allow_module_level=True)

from app.retrieval.hybrid import HybridRetriever
from app.retrieval.relevance import keep_relevant_chunks


class DummyStore:
    def __init__(self, chunks):
        self.chunks = chunks

    async def list_chunks(self):
        return self.chunks

    async def get_chunks_by_ids(self, chunk_ids):
        by_id = {chunk["id"]: chunk for chunk in self.chunks}
        return [by_id[chunk_id] for chunk_id in chunk_ids if chunk_id in by_id]


class DummyLlm:
    async def embed_text(self, query, task_type):
        return [1.0]


class DummyVectorStore:
    async def query(self, embedding, top_k):
        return [{"id": "semantic-only", "score": 0.82}]


@pytest.mark.asyncio
async def test_hybrid_retrieval_keeps_semantic_only_hits():
    chunks = [
        {
            "id": "keyword-one",
            "document_id": "doc-1",
            "filename": "policy.pdf",
            "chunk_index": 0,
            "text": "travel expense reimbursement travel expense",
            "metadata": {},
        },
        {
            "id": "keyword-two",
            "document_id": "doc-1",
            "filename": "policy.pdf",
            "chunk_index": 1,
            "text": "expense reimbursement receipt approval",
            "metadata": {},
        },
        {
            "id": "semantic-only",
            "document_id": "doc-2",
            "filename": "handbook.pdf",
            "chunk_index": 0,
            "text": "employees may claim approved business costs after manager review",
            "metadata": {},
        },
    ]
    retriever = HybridRetriever(DummyStore(chunks), DummyLlm(), DummyVectorStore())

    results = await retriever.retrieve_queries(["travel expense reimbursement"], top_k=2)

    semantic = next(chunk for chunk in results if chunk["id"] == "semantic-only")
    assert semantic["semantic_score"] == 1
    assert semantic["bm25_score"] == 0


def test_relevance_filter_preserves_semantic_signal_without_keyword_overlap():
    chunks = [
        {"id": "semantic-only", "text": "approved business costs", "semantic_score": 0.73},
        {"id": "unrelated", "text": "general information", "semantic_score": 0.0},
    ]

    relevant = keep_relevant_chunks("travel expense reimbursement", chunks)

    assert [chunk["id"] for chunk in relevant] == ["semantic-only"]

