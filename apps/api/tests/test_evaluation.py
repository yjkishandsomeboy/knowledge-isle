from types import SimpleNamespace

from knowledge_isle_api.services.evaluation import EvaluationCase, evaluate_cases


def test_evaluation_metrics_are_reproducible() -> None:
    cases = [EvaluationCase("case-1", "question", frozenset({"b"}))]
    metrics = evaluate_cases(
        cases,
        {"case-1": [SimpleNamespace(identifier="a"), SimpleNamespace(identifier="b")]},
    )

    assert metrics.recall_at_1 == 0.0
    assert metrics.recall_at_3 == 1.0
    assert metrics.precision_at_5 == 0.2
    assert metrics.mrr == 0.5
