from app.evaluation.service import EvaluationService


def test_evaluation_fallback_returns_four_metrics():
    service = EvaluationService(llm=None)
    metrics = service._fallback_metrics(
        "What does the policy cover?",
        "The policy covers data retention.",
        ["The policy covers data retention and access review."],
        None,
    )
    assert [metric["name"] for metric in metrics] == [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
    ]
    assert all(metric["score"] is not None for metric in metrics)
