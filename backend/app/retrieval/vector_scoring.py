def distance_to_score(distance: float, metric: str) -> float:
    distance = max(0.0, distance)
    if metric.lower() in {"cosine", "ip"}:
        return max(0.0, min(1.0, 1.0 - distance))
    return 1.0 / (1.0 + distance)
