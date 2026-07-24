import json
from pathlib import Path
from types import SimpleNamespace

from knowledge_isle_api.services.evaluation import EvaluationCase, evaluate_cases
from knowledge_isle_api.services.retrieval import _lexical_search


def main() -> None:
    dataset_path = Path(__file__).parents[1] / "evals" / "retrieval.jsonl"
    cases: list[EvaluationCase] = []
    ranked: dict[str, list[SimpleNamespace]] = {}
    for line in dataset_path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        documents = [
            SimpleNamespace(
                id=document["id"],
                original_filename=document["filename"],
                extracted_text=document["text"],
            )
            for document in record["documents"]
        ]
        results = _lexical_search([(document, None) for document in documents], record["question"])
        ranked[record["id"]] = [SimpleNamespace(identifier=item.document_id) for item in results]
        cases.append(
            EvaluationCase(
                case_id=record["id"],
                question=record["question"],
                relevant_ids=frozenset(record["relevant_ids"]),
            )
        )
    metrics = evaluate_cases(cases, ranked)
    print(json.dumps(metrics.__dict__, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
