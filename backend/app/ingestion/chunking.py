from dataclasses import dataclass


@dataclass
class TextChunk:
    index: int
    text: str


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[TextChunk]:
    if not text:
        return []
    paragraphs = [part.strip() for part in text.split("\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 1 <= chunk_size:
            current = f"{current}\n{paragraph}".strip()
            continue
        if current:
            chunks.append(current)
        current = paragraph
        while len(current) > chunk_size:
            chunks.append(current[:chunk_size])
            current = current[max(0, chunk_size - overlap):]
    if current:
        chunks.append(current)

    normalized: list[str] = []
    for chunk in chunks:
        if normalized and overlap > 0:
            prefix = normalized[-1][-overlap:]
            chunk = f"{prefix} {chunk}"
        normalized.append(chunk[: chunk_size + overlap].strip())
    return [TextChunk(index=i, text=value) for i, value in enumerate(normalized)]
