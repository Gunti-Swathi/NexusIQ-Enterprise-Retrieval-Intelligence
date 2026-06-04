import pytest

from app.retrieval.vector_scoring import distance_to_score


def test_vector_distance_scores_stay_positive_for_l2_collections():
    assert distance_to_score(0.0, "l2") == 1.0
    assert distance_to_score(4.0, "l2") == 0.2


def test_vector_distance_scores_use_cosine_similarity_direction():
    assert distance_to_score(0.18, "cosine") == pytest.approx(0.82)
    assert distance_to_score(1.4, "cosine") == 0.0
