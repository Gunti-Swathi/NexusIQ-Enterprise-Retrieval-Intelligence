from app.retrieval.bm25 import tokenize


STOPWORDS = {
    "a",
    "about",
    "applied",
    "ask",
    "for",
    "have",
    "in",
    "is",
    "model",
    "models",
    "of",
    "on",
    "paper",
    "papers",
    "predict",
    "the",
    "to",
    "used",
    "we",
    "what",
    "which",
    "they",
    "does",
    "did",
    "how",
}

NORMALIZED_TERMS = {
    "throid": "thyroid",
    "thyroids": "thyroid",
    "nodules": "nodule",
    "cancerous": "cancer",
    "cancers": "cancer",
    "defects": "defect",
    "boards": "board",
    "methods": "method",
    "identified": "identify",
    "identifies": "identify",
    "identifying": "identify",
    "identification": "identify",
    "detected": "detect",
    "detecting": "detect",
    "detection": "detect",
    "classify": "classification",
    "classified": "classification",
    "classifying": "classification",
}


def normalize_term(token: str) -> str:
    normalized = NORMALIZED_TERMS.get(token, token)
    if normalized in NORMALIZED_TERMS:
        return NORMALIZED_TERMS[normalized]
    if len(normalized) > 5 and normalized.endswith("ies"):
        return f"{normalized[:-3]}y"
    if len(normalized) > 4 and normalized.endswith("es"):
        return normalized[:-2]
    if len(normalized) > 4 and normalized.endswith("s"):
        return normalized[:-1]
    return normalized


def important_query_terms(query: str) -> set[str]:
    terms = set()
    for token in tokenize(query):
        normalized = normalize_term(token)
        if normalized not in STOPWORDS and len(normalized) > 2:
            terms.add(normalized)
    return terms


def relevance_score(query: str, chunk: dict) -> float:
    terms = important_query_terms(query)
    if not terms:
        return 0.0
    haystack = " ".join(
        [
            chunk.get("filename", ""),
            chunk.get("text", ""),
        ]
    ).lower()
    haystack_terms = {normalize_term(token) for token in tokenize(haystack)}
    return len(terms & haystack_terms) / len(terms)


def keep_relevant_chunks(query: str, chunks: list[dict]) -> list[dict]:
    terms = important_query_terms(query)
    if not terms:
        return chunks
    scored = [(chunk, relevance_score(query, chunk)) for chunk in chunks]
    relevant = [
        chunk
        for chunk, score in scored
        if score > 0 or float(chunk.get("semantic_score", 0.0)) > 0
    ]
    return relevant or chunks[:1]
