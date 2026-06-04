def analyze_query(query: str) -> dict:
    lowered = query.lower()
    broad_terms = ["summarize", "summary", "overview", "compare", "difference", "recommend", "related"]
    exact_terms = ["page", "section", "chunk", "exact", "quote", ".pdf", ".docx", ".txt", ".csv"]
    is_broad = any(term in lowered for term in broad_terms) or len(query.split()) <= 5
    is_exact = any(term in lowered for term in exact_terms)
    should_expand = is_broad and not is_exact
    return {
        "is_broad": is_broad,
        "is_exact": is_exact,
        "should_expand": should_expand,
    }


def should_compress_context(query_type: str, chunks: list[dict], top_k: int) -> bool:
    if query_type in {"summary", "comparison"}:
        return True
    if len(chunks) > max(top_k, 8):
        return True
    total_chars = sum(len(chunk.get("text", "")) for chunk in chunks)
    return total_chars > 10000
