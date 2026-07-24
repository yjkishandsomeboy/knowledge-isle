import json
from dataclasses import dataclass
from pathlib import Path

from knowledge_isle_dev_agent.commands import run_command


@dataclass(frozen=True)
class GitHubIssue:
    number: int
    title: str
    body: str
    url: str


class GitHubClient:
    def __init__(self, gh_path: str, repo: str, cwd: Path) -> None:
        self.gh_path = gh_path
        self.repo = repo
        self.cwd = cwd

    def _run(self, args: list[str], *, cwd: Path | None = None) -> str:
        result = run_command(
            [self.gh_path, *args, "--repo", self.repo], cwd=cwd or self.cwd
        )
        return result.stdout.strip()

    def check_auth(self) -> None:
        run_command([self.gh_path, "auth", "status"], cwd=self.cwd)

    def ensure_labels(self) -> None:
        labels = {
            "agent-ready": "0E8A16",
            "agent-running": "FBCA04",
            "agent-review": "1D76DB",
            "agent-done": "5319E7",
            "agent-blocked": "D93F0B",
        }
        for name, color in labels.items():
            self._run(
                [
                    "label", "create", name, "--color", color, "--force",
                    "--description", "Knowledge Isle local Dev Agent workflow",
                ]
            )

    def ready_issues(self) -> list[GitHubIssue]:
        output = self._run(
            [
                "issue",
                "list",
                "--state",
                "open",
                "--label",
                "agent-ready",
                "--limit",
                "20",
                "--json",
                "number,title,body,url,labels",
            ]
        )
        records = json.loads(output or "[]")
        blocked_labels = {"agent-running", "agent-review", "agent-done", "agent-blocked"}
        return [
            GitHubIssue(record["number"], record["title"], record.get("body") or "", record["url"])
            for record in records
            if not ({label["name"] for label in record["labels"]} & blocked_labels)
        ]

    def set_state(self, issue_number: int, state_label: str) -> None:
        labels = ["agent-running", "agent-review", "agent-done", "agent-blocked"]
        output = self._run(
            ["issue", "view", str(issue_number), "--json", "labels"]
        )
        current = {label["name"] for label in json.loads(output)["labels"]}
        args = ["issue", "edit", str(issue_number)]
        for label in labels:
            if label in current and label != state_label:
                args.extend(["--remove-label", label])
        args.extend(["--add-label", state_label])
        self._run(args)

    def comment(self, issue_number: int, body: str) -> None:
        self._run(["issue", "comment", str(issue_number), "--body", body])

    def create_pr(self, cwd: Path, *, title: str, body: str, branch: str) -> tuple[int, str]:
        self._run(
            ["pr", "create", "--base", "main", "--head", branch, "--title", title, "--body", body],
            cwd=cwd,
        )
        output = self._run(["pr", "view", branch, "--json", "number,url"], cwd=cwd)
        record = json.loads(output)
        return int(record["number"]), str(record["url"])

    def merge_pr(self, pr_number: int) -> None:
        self._run(["pr", "merge", str(pr_number), "--merge", "--delete-branch"])
