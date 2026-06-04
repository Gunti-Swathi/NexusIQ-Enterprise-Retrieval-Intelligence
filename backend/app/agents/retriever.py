from app.core.config import settings
from app.reranking.cross_encoder import CrossEncoderReranker
from app.retrieval.compression import ContextCompressor
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.hybrid_retrieval_node import HybridRetrievalNode


class RetrieverAgent(HybridRetrievalNode):
    def __init__(self, retriever: HybridRetriever, compressor: ContextCompressor) -> None:
        super().__init__(retriever, CrossEncoderReranker(), compressor)

    async def run(self, question: str, top_k: int, use_multi_query: bool) -> list[dict]:
        chunks = await self.retriever.retrieve(question, top_k=top_k, use_multi_query=use_multi_query)
        return await self.compressor.compress(question, chunks, max_chunks=min(top_k, settings.hybrid_top_k))
