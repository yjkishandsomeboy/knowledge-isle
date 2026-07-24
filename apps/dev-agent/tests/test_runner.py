from pathlib import Path

import pytest

from knowledge_isle_dev_agent.config import AgentSettings
from knowledge_isle_dev_agent.database import AgentDatabase
from knowledge_isle_dev_agent.runner import DevelopmentAgent


class FakeGitHub:
    merged: int | None = None

    def merge_pr(self, pr_number: int) -> None:
        self.merged = pr_number

    def set_state(self, _issue_number: int, _label: str) -> None:
        return None


@pytest.mark.asyncio
async def test_merge_requires_quality_approval_and_matching_issue(tmp_path: Path) -> None:
    database = AgentDatabase(tmp_path / "agent.db")
    github = FakeGitHub()
    settings = AgentSettings(tmp_path, tmp_path, tmp_path / "codex.exe", "gh", "owner/repo", 600)
    agent = DevelopmentAgent(settings, database, github)  # type: ignore[arg-type]
    run_id = database.create_run(21, "Safe merge")
    database.update_run(
        run_id, status="awaiting_review", quality_passed=1, pr_number=8
    )

    with pytest.raises(ValueError):
        await agent.confirm_merge(run_id, 21)
    await agent.approve_merge(run_id)
    with pytest.raises(ValueError):
        await agent.confirm_merge(run_id, 20)
    await agent.confirm_merge(run_id, 21)

    assert github.merged == 8
    assert database.get_run(run_id)["status"] == "succeeded"  # type: ignore[index]
