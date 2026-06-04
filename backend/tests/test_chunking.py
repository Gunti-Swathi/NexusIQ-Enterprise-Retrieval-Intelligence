from app.ingestion.chunking import chunk_text


def test_chunk_text_preserves_content_order():
    text = "\n".join([f"Paragraph {index} has important searchable content." for index in range(20)])
    chunks = chunk_text(text, chunk_size=140, overlap=20)
    assert len(chunks) > 1
    assert chunks[0].index == 0
    assert "Paragraph 0" in chunks[0].text
    assert any("Paragraph 19" in chunk.text for chunk in chunks)
