NEGATION_TERMS = {"not", "no", "never", "without", "cannot", "can't", "doesn't", "do not", "isn't", "aren't"}


class ContradictionDetector:
    async def detect(self, query: str, chunks: list[dict]) -> list[dict]:
        output = []
        for left_index, left in enumerate(chunks):
            left_text = left.get("text", "").lower()
            left_has_negation = any(term in left_text for term in NEGATION_TERMS)
            for right in chunks[left_index + 1:]:
                if left["document_id"] == right["document_id"]:
                    continue
                right_text = right.get("text", "").lower()
                right_has_negation = any(term in right_text for term in NEGATION_TERMS)
                shared_terms = set(query.lower().split()) & set(left_text.split()) & set(right_text.split())
                if shared_terms and left_has_negation != right_has_negation:
                    output.append(
                        {
                            "left_chunk_id": left["id"],
                            "right_chunk_id": right["id"],
                            "left_file": left["filename"],
                            "right_file": right["filename"],
                            "severity": "medium",
                            "reason": "Potential polarity conflict found across documents for query terms.",
                        }
                    )
                if len(output) >= 5:
                    return output
        return output
