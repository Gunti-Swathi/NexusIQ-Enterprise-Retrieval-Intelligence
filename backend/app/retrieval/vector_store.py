import chromadb

from app.core.config import settings
from app.retrieval.vector_scoring import distance_to_score


class VectorStore:
    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(path=str(settings.chroma_path))
        self.collection = self.client.get_or_create_collection(
            "document_chunks",
            metadata={"hnsw:space": "cosine"},
        )
        self.distance_metric = _distance_metric(self.collection)

    async def add_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        self.collection.upsert(
            ids=[chunk["id"] for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk["text"] for chunk in chunks],
            metadatas=[
                _chroma_metadata(chunk)
                for chunk in chunks
            ],
        )

    async def query(self, embedding: list[float], top_k: int) -> list[dict]:
        count = self.collection.count()
        if count == 0:
            return []
        result = self.collection.query(query_embeddings=[embedding], n_results=min(top_k, count))
        ids = result.get("ids", [[]])[0]
        distances = result.get("distances", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        return [
            {
                "id": chunk_id,
                "score": distance_to_score(float(distance), self.distance_metric),
                "metadata": metadata,
            }
            for chunk_id, distance, metadata in zip(ids, distances, metadatas)
        ]

    async def delete_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})


def _chroma_metadata(chunk: dict) -> dict:
    metadata = chunk.get("metadata") if isinstance(chunk.get("metadata"), dict) else {}
    output = {
        "document_id": chunk["document_id"],
        "filename": chunk["filename"],
        "chunk_index": chunk["chunk_index"],
    }
    page_number = metadata.get("page_number")
    section = metadata.get("section")
    if page_number is not None:
        output["page_number"] = page_number
    if section:
        output["section"] = section
    return output


def _distance_metric(collection) -> str:
    metadata = getattr(collection, "metadata", None) or {}
    return str(metadata.get("hnsw:space", "l2")).lower()

