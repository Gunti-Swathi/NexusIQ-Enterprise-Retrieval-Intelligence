from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.core.config import settings
from app.core.llm import GeminiClient
from app.evaluation.evaluation_node import EvaluationNode
from app.evaluation.service import EvaluationService
from app.generation.answer_generation_node import AnswerGenerationNode
from app.ingestion.pipeline import IngestionPipeline
from app.recommendations.service import RecommendationService
from app.reranking.cross_encoder import CrossEncoderReranker
from app.retrieval.compression import ContextCompressor
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.hybrid_retrieval_node import HybridRetrievalNode
from app.retrieval.vector_store import VectorStore
from app.schemas.chat import AskRequest, AskResponse
from app.schemas.documents import ChunkOut, DocumentsResponse
from app.schemas.evaluation import EvaluationRequest, EvaluationResponse
from app.workflows.graph import DocumentSearchGraph
from app.workflows.multi_query_expansion_node import MultiQueryExpansionNode
from app.workflows.query_processing_node import QueryProcessingNode

router = APIRouter()


def services(request: Request):
    llm = GeminiClient()
    vector_store = VectorStore()
    store = request.app.state.store
    return llm, vector_store, store


def chunk_out(chunk: dict) -> ChunkOut:
    metadata = chunk.get("metadata") if isinstance(chunk.get("metadata"), dict) else {}
    return ChunkOut(
        id=chunk["id"],
        document_id=chunk["document_id"],
        filename=chunk["filename"],
        chunk_index=chunk["chunk_index"],
        text=chunk["text"],
        score=chunk.get("score"),
        semantic_score=chunk.get("semantic_score"),
        bm25_score=chunk.get("bm25_score"),
        hybrid_score=chunk.get("hybrid_score"),
        rerank_score=chunk.get("rerank_score"),
        query_relevance=chunk.get("query_relevance"),
        page_number=metadata.get("page_number"),
        section=metadata.get("section"),
        source_number=chunk.get("source_number"),
    )


def retrieval_debug_out(result: dict) -> dict:
    debug = result.get("retrieval_debug") or {}
    return {
        "original_query": debug.get("original_query"),
        "expanded_queries": debug.get("expanded_queries", result.get("expanded_queries", [])),
        "retrieved_chunks": [chunk_out(chunk).model_dump() for chunk in debug.get("retrieved_chunks", [])],
        "reranked_chunks": [chunk_out(chunk).model_dump() for chunk in debug.get("reranked_chunks", [])],
        "selected_context": [chunk_out(chunk).model_dump() for chunk in debug.get("selected_context", [])],
        "retrieval_confidence": debug.get("retrieval_confidence", result.get("retrieval_confidence")),
    }


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "generation_model": settings.gemini_generation_model,
        "embedding_model": settings.gemini_embedding_model,
    }


@router.post("/upload")
async def upload(request: Request, files: list[UploadFile] = File(...)) -> dict:
    if len(files) > settings.max_upload_files:
        raise HTTPException(status_code=400, detail=f"Upload at most {settings.max_upload_files} files.")
    llm, vector_store, store = services(request)
    pipeline = IngestionPipeline(store, llm, vector_store)
    try:
        documents = await pipeline.ingest(files)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"documents": documents}


@router.post("/ask", response_model=AskResponse)
async def ask(request: Request, payload: AskRequest) -> AskResponse:
    llm, vector_store, store = services(request)
    hybrid = HybridRetriever(store, llm, vector_store)
    graph = DocumentSearchGraph(
        query_processor=QueryProcessingNode(),
        query_expander=MultiQueryExpansionNode(llm),
        retriever=HybridRetrievalNode(hybrid, CrossEncoderReranker(), ContextCompressor(llm)),
        answer_generator=AnswerGenerationNode(llm),
        evaluator=EvaluationNode(EvaluationService(llm)),
        recommender=RecommendationService(llm, vector_store),
    )
    try:
        result = await graph.ask(payload.question, payload.top_k, payload.use_multi_query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ask workflow failed: {exc}") from exc
    chunks = [chunk_out(chunk) for chunk in result.get("chunks", [])]
    selected_context = [chunk_out(chunk) for chunk in result.get("selected_context", result.get("chunks", []))]
    return AskResponse(
        answer=result.get("answer", ""),
        citations=result.get("citations", []),
        retrieved_chunks=chunks,
        recommendations=result.get("recommendations", []),
        contradictions=result.get("contradictions", []),
        citation_validation=result.get("citation_validation"),
        retrieval_confidence=result.get("retrieval_confidence"),
        retrieval_debug=retrieval_debug_out(result),
        expanded_queries=result.get("expanded_queries", []),
        selected_context=selected_context,
        query_type=result.get("query_type"),
        should_expand_query=result.get("should_expand_query"),
        should_compress_context=result.get("should_compress_context"),
        trace_url=result.get("trace_url"),
    )


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: Request, payload: EvaluationRequest) -> EvaluationResponse:
    llm, _, _ = services(request)
    result = await EvaluationService(llm).evaluate(
        payload.question,
        payload.answer,
        payload.contexts,
        payload.ground_truth,
    )
    return EvaluationResponse(metrics=result)


@router.get("/documents", response_model=DocumentsResponse)
async def documents(request: Request) -> DocumentsResponse:
    rows = await request.app.state.store.list_documents()
    return DocumentsResponse(documents=rows)


@router.get("/recommendations/{document_id}")
async def recommendations(request: Request, document_id: str) -> dict:
    llm, vector_store, store = services(request)
    chunks = [chunk for chunk in await store.list_chunks() if chunk["document_id"] == document_id]
    if not chunks:
        raise HTTPException(status_code=404, detail="Document not found")
    items = await RecommendationService(llm, vector_store).recommend(
        f"Recommend documents and chunks related to {chunks[0]['filename']}.",
        "",
        chunks[:3],
    )
    return {"recommendations": items}


@router.delete("/documents/{document_id}")
async def delete_document(request: Request, document_id: str) -> dict:
    _, vector_store, store = services(request)
    deleted = await store.delete_document(document_id)
    await vector_store.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": True}
