def score_retrieval_confidence(chunks: list[dict]) -> dict:
    if not chunks:
        return {"score": 0.0, "label": "none", "reason": "No chunks were retrieved."}

    scores = [float(chunk.get("rerank_score", chunk.get("hybrid_score", chunk.get("score", 0.0))) or 0.0) for chunk in chunks]
    best = max(scores)
    average_top = sum(scores[: min(3, len(scores))]) / min(3, len(scores))
    confidence = round(min(1.0, (0.65 * best) + (0.35 * average_top)), 4)
    if confidence >= 0.7:
        label = "high"
    elif confidence >= 0.4:
        label = "medium"
    else:
        label = "low"
    return {
        "score": confidence,
        "label": label,
        "reason": f"Best score {best:.2f}; average top evidence score {average_top:.2f}.",
    }
