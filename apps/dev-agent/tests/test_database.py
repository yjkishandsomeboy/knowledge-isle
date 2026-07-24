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


def test_planner_run_and_candidate_are_persisted(tmp_path: Path) -> None:
    database = AgentDatabase(tmp_path / "agent.db")
    run_id = database.create_planner_run()
    database.add_planner_candidate(
        run_id,
        fingerprint="unique-task",
        title="补充健康检查测试",
        summary="覆盖健康检查接口的成功路径。",
        category="tests",
        risk_level="low",
        auto_ready=True,
        issue_number=31,
        issue_url="https://github.com/example/repo/issues/31",
        evidence=["apps/api/tests/test_health.py:1"],
    )
    database.complete_planner_run(
        run_id, status="succeeded", candidates_count=1, issues_created=1
    )

    assert database.planner_fingerprint_seen("unique-task")
    assert database.planner_issues_created_in_last_day() == 1
    assert database.latest_planner_run()["issues_created"] == 1  # type: ignore[index]
    assert database.list_planner_candidates()[0]["auto_ready"] == 1


def test_blocked_issue_can_reuse_its_run_after_manual_requeue(tmp_path: Path) -> None:
    database = AgentDatabase(tmp_path / "agent.db")
    run_id = database.create_run(44, "Retry command")
    database.update_run(run_id, status="blocked", error="Command not found: pnpm")

    assert not database.issue_seen(44)
    assert database.create_run(44, "Retry command") == run_id
    assert database.get_run(run_id)["status"] == "queued"  # type: ignore[index]
    assert database.get_run(run_id)["error"] is None  # type: ignore[index]
