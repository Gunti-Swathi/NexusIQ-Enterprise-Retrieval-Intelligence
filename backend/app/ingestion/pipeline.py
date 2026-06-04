import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.llm import GeminiClient
from app.database.store import DocumentStore
from app.ingestion.chunking import chunk_text
from app.ingestion.extractors import SUPPORTED_EXTENSIONS, clean_text, extract_text
from app.retrieval.vector_store import VectorStore


class IngestionPipeline:
    def __init__(self, store: DocumentStore, llm: GeminiClient, vector_store: VectorStore) -> None:
        self.store = store
        self.llm = llm
        self.vector_store = vector_store

    async def ingest(self, files: list[UploadFile]) -> list[dict]:
        existing = await self.store.document_count()
        if existing + len(files) > settings.max_upload_files:
            raise ValueError(f"Upload limit is {settings.max_upload_files} files.")

        documents = []
        for file in files:
            suffix = Path(file.filename or "").suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS:
                raise ValueError(f"Unsupported file type: {file.filename}")

            document_id = str(uuid.uuid4())
            safe_name = Path(file.filename or f"{document_id}{suffix}").name
            upload_path = settings.upload_dir / f"{document_id}_{safe_name}"
            with upload_path.open("wb") as handle:
                shutil.copyfileobj(file.file, handle)

            text = clean_text(extract_text(upload_path))
            chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
            created_at = datetime.now(timezone.utc).isoformat()
            chunk_rows = [
                {
                    "id": f"{document_id}:{chunk.index}",
                    "document_id": document_id,
                    "filename": safe_name,
                    "chunk_index": chunk.index,
                    "text": chunk.text,
                    "metadata": {
                        "source_path": str(upload_path),
                        "page_number": None,
                        "section": None,
                        "upload_time": created_at,
                    },
                }
                for chunk in chunks
            ]
            doc = {
                "id": document_id,
                "filename": safe_name,
                "content_type": file.content_type or "application/octet-stream",
                "size_bytes": upload_path.stat().st_size,
                "metadata": {"source_path": str(upload_path), "extension": suffix, "upload_time": created_at},
                "created_at": created_at,
            }
            embeddings = await self.llm.embed_many([chunk["text"] for chunk in chunk_rows])
            await self.vector_store.add_chunks(chunk_rows, embeddings)
            await self.store.add_document(doc, chunk_rows)
            documents.append({**doc, "chunk_count": len(chunk_rows)})
        return documents
