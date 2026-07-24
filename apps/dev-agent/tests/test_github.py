from pathlib import Path

import pytest

from knowledge_isle_dev_agent.github import GitHubClient


def test_create_pr_uses_url_returned_by_create_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = GitHubClient("gh", "owner/repo", tmp_path)
    calls: list[list[str]] = []

    def fake_run(args: list[str], *, cwd: Path | None = None) -> str:
        calls.append(args)
        return "https://github.com/owner/repo/pull/27"

    monkeypatch.setattr(client, "_run", fake_run)

    number, url = client.create_pr(
        tmp_path, title="Agent change", body="Closes #9", branch="agent/issue-9"
    )

    assert number == 27
    assert url == "https://github.com/owner/repo/pull/27"
    assert len(calls) == 1
