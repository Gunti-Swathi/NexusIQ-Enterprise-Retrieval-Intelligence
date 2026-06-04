class CitationChecker:
    async def validate(self, answer: str, citations: list[dict], chunks: list[dict]) -> dict:
        chunk_ids = {chunk["id"] for chunk in chunks}
        citation_ids = {
            chunk_id
            for citation in citations
            for chunk_id in citation.get("chunk_ids", [])
        }
        missing = sorted(citation_id for citation_id in citation_ids if citation_id not in chunk_ids)
        has_answer = bool(answer.strip()) and "do not have enough grounded context" not in answer.lower()
        valid = not missing and (not has_answer or bool(citations))
        return {
            "valid": valid,
            "missing_chunk_ids": missing,
            "citation_count": len(citations),
            "reason": "All citations map to selected context." if valid else "One or more answer citations are missing from selected context.",
        }
