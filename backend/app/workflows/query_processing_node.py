from app.workflows.conditions import analyze_query


class QueryProcessingNode:
    async def run(self, user_query: str) -> dict:
        normalized_query = " ".join(user_query.split())
        analysis = analyze_query(normalized_query)
        return {
            "user_query": normalized_query,
            "question": normalized_query,
            "query_type": self._classify(normalized_query),
            "route": "answer",
            "should_expand_query": analysis["should_expand"],
            "query_analysis": analysis,
        }

    def _classify(self, query: str) -> str:
        lowered = query.lower()
        if any(term in lowered for term in ["compare", "difference", "versus", " vs "]):
            return "comparison"
        if any(term in lowered for term in ["recommend", "related", "similar"]):
            return "recommendation"
        if any(term in lowered for term in ["contradict", "conflict", "inconsistent"]):
            return "contradiction"
        if any(term in lowered for term in ["summarize", "summary", "overview"]):
            return "summary"
        if any(term in lowered for term in ["evaluate", "faithfulness", "ragas"]):
            return "evaluation"
        return "answer"
