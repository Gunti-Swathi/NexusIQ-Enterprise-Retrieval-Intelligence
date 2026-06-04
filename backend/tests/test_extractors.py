from app.ingestion.extractors import clean_text


def test_clean_text_removes_empty_lines_and_extra_spaces():
    assert clean_text(" A   line\n\n another\tline ") == "A line\nanother line"
