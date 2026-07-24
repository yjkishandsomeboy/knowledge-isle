from pathlib import Path

from knowledge_isle_dev_agent.database import AgentDatabase


def test_run_lifecycle_is_persisted(tmp_path: Path) -> None:
    database = AgentDatabase(tmp_path / "agent.db")
    run_id = database.create_run(12, "Add feature")
    database.update_run(run_id, status="awaiting_review", quality_passed=1)
    database.add_event(run_id, "Quality gate passed")

    run = database.get_run(run_id)
    assert run is not None
    assert run["issue_number"] == 12
    assert run["quality_passed"] == 1
    assert run["events"][0]["message"] == "Quality gate passed"
