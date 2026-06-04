import json
from datetime import datetime, timezone

import aiosqlite


def _decode_metadata(row: dict) -> dict:
    value = row.get("metadata")
    if isinstance(value, str):
        row["metadata"] = json.loads(value or "{}")
    return row


class DocumentStore:
    def __init__(self, path) -> None:
        self.path = path

    async def initialize(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
                """
            )
            await db.commit()

    async def document_count(self) -> int:
        async with aiosqlite.connect(self.path) as db:
            row = await (await db.execute("SELECT COUNT(*) FROM documents")).fetchone()
        return int(row[0])

    async def add_document(self, doc: dict, chunks: list[dict]) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?)",
                (
                    doc["id"],
                    doc["filename"],
                    doc["content_type"],
                    doc["size_bytes"],
                    json.dumps(doc.get("metadata", {})),
                    doc.get("created_at", datetime.now(timezone.utc).isoformat()),
                ),
            )
            await db.executemany(
                "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        chunk["id"],
                        chunk["document_id"],
                        chunk["filename"],
                        chunk["chunk_index"],
                        chunk["text"],
                        json.dumps(chunk.get("metadata", {})),
                    )
                    for chunk in chunks
                ],
            )
            await db.commit()

    async def list_documents(self) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            rows = await (await db.execute(
                """
                SELECT d.*, COUNT(c.id) AS chunk_count
                FROM documents d
                LEFT JOIN chunks c ON c.document_id = d.id
                GROUP BY d.id
                ORDER BY d.created_at DESC
                """
            )).fetchall()
        return [_decode_metadata(dict(row)) for row in rows]

    async def list_chunks(self) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            rows = await (await db.execute("SELECT * FROM chunks ORDER BY filename, chunk_index")).fetchall()
        return [_decode_metadata(dict(row)) for row in rows]

    async def get_chunks_by_ids(self, chunk_ids: list[str]) -> list[dict]:
        if not chunk_ids:
            return []
        placeholders = ",".join("?" for _ in chunk_ids)
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            rows = await (await db.execute(f"SELECT * FROM chunks WHERE id IN ({placeholders})", chunk_ids)).fetchall()
        by_id = {row["id"]: _decode_metadata(dict(row)) for row in rows}
        return [by_id[chunk_id] for chunk_id in chunk_ids if chunk_id in by_id]

    async def delete_document(self, document_id: str) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            await db.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            await db.commit()
            return cursor.rowcount > 0
