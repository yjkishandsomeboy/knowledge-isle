from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    question: str
    relevant_ids: frozenset[str]


class RankedResult(Protocol):
    identifier: str


@dataclass(frozen=True)
class EvaluationMetrics:
    total: int
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    precision_at_5: float
    mrr: float


def evaluate_cases(
    cases: list[EvaluationCase],
    results: dict[str, list[RankedResult]],
) -> EvaluationMetrics:
    if not cases:
        return EvaluationMetrics(0, 0.0, 0.0, 0.0, 0.0, 0.0)

    recalls: dict[int, list[float]] = {1: [], 3: [], 5: []}
    precisions: list[float] = []
    reciprocal_ranks: list[float] = []
    for case in cases:
        ranked_ids = [item.identifier for item in results.get(case.case_id, [])]
        for cutoff in recalls:
            recalls[cutoff].append(
                float(bool(set(ranked_ids[:cutoff]) & case.relevant_ids))
            )
        hits_at_5 = sum(identifier in case.relevant_ids for identifier in ranked_ids[:5])
        precisions.append(hits_at_5 / 5)
        reciprocal_ranks.append(
            next(
                (1 / index for index, identifier in enumerate(ranked_ids, 1)
                 if identifier in case.relevant_ids),
                0.0,
            )
        )
    return EvaluationMetrics(
        total=len(cases),
        recall_at_1=sum(recalls[1]) / len(cases),
        recall_at_3=sum(recalls[3]) / len(cases),
        recall_at_5=sum(recalls[5]) / len(cases),
        precision_at_5=sum(precisions) / len(cases),
        mrr=sum(reciprocal_ranks) / len(cases),
    )
