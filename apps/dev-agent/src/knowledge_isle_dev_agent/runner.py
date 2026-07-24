import asyncio
import re
from pathlib import Path

from knowledge_isle_dev_agent.commands import run_command
from knowledge_isle_dev_agent.config import AgentSettings
from knowledge_isle_dev_agent.database import AgentDatabase
from knowledge_isle_dev_agent.github import GitHubClient, GitHubIssue

QUALITY_COMMANDS = [
    [
        "uv", "run", "--package", "knowledge-isle-api", "ruff", "check",
        "apps/api/src", "apps/api/tests",
    ],
    ["uv", "run", "--package", "knowledge-isle-api", "mypy", "apps/api/src"],
    ["uv", "run", "--package", "knowledge-isle-api", "pytest", "apps/api/tests"],
    ["uv", "run", "--package", "knowledge-isle-worker", "ruff", "check", "apps/worker/src"],
    ["pnpm", "--filter", "@knowledge-isle/web", "typecheck"],
    ["pnpm", "--filter", "@knowledge-isle/web", "test"],
    ["pnpm", "--filter", "@knowledge-isle/web", "build"],
    ["git", "diff", "--check"],
]


class DevelopmentAgent:
    def __init__(
        self, settings: AgentSettings, database: AgentDatabase, github: GitHubClient
    ) -> None:
        self.settings = settings
        self.database = database
        self.github = github
        self.lock = asyncio.Lock()

    async def poll_once(self) -> int | None:
        if self.lock.locked():
            return None
        issues = await asyncio.to_thread(self.github.ready_issues)
        issue = next((item for item in issues if not self.database.issue_seen(item.number)), None)
        if issue is None:
            return None
        run_id = self.database.create_run(issue.number, issue.title)
        asyncio.create_task(self._execute(run_id, issue))
        return run_id

    async def _execute(self, run_id: int, issue: GitHubIssue) -> None:
        async with self.lock:
            worktree = self.settings.worktree_dir / f"issue-{issue.number}"
            branch = f"agent/issue-{issue.number}"
            try:
                self.database.update_run(run_id, status="running", branch=branch)
                self.database.add_event(run_id, "开始处理 GitHub Issue", details={"url": issue.url})
                await asyncio.to_thread(self.github.set_state, issue.number, "agent-running")
                await asyncio.to_thread(self._prepare_worktree, worktree, branch)
                self.database.add_event(
                    run_id, "独立 worktree 已创建", details={"path": str(worktree)}
                )
                await asyncio.to_thread(self._run_codex, run_id, issue, worktree)
                self.database.update_run(run_id, status="testing")
                await asyncio.to_thread(self._run_quality_gate, run_id, worktree)
                await asyncio.to_thread(self._commit_and_push, run_id, issue, worktree, branch)
                pr_number, pr_url = await asyncio.to_thread(
                    self._create_pr, run_id, issue, worktree, branch
                )
                self.database.update_run(
                    run_id,
                    status="awaiting_review",
                    quality_passed=1,
                    pr_number=pr_number,
                    pr_url=pr_url,
                )
                await asyncio.to_thread(self.github.set_state, issue.number, "agent-review")
                await asyncio.to_thread(
                    self.github.comment,
                    issue.number,
                    f"Dev Agent 已完成实现与质量门禁，等待人工审核：{pr_url}",
                )
                self.database.add_event(run_id, "PR 已创建，等待人工审核", details={"url": pr_url})
            except Exception as error:
                self.database.update_run(run_id, status="blocked", error=str(error)[-4000:])
                self.database.add_event(
                    run_id, "执行失败", level="error", details={"error": str(error)}
                )
                try:
                    await asyncio.to_thread(self.github.set_state, issue.number, "agent-blocked")
                    await asyncio.to_thread(
                        self.github.comment,
                        issue.number,
                        "Dev Agent 执行失败，详情请查看本地管理页面。",
                    )
                except Exception:
                    pass

    def _prepare_worktree(self, path: Path, branch: str) -> None:
        run_command(["git", "fetch", "origin", "main"], cwd=self.settings.repo_root)
        if path.exists():
            run_command(
                ["git", "worktree", "remove", "--force", str(path)],
                cwd=self.settings.repo_root,
            )
        run_command(
            ["git", "worktree", "add", "-b", branch, str(path), "origin/main"],
            cwd=self.settings.repo_root,
        )
        run_command(["uv", "sync", "--all-packages"], cwd=path, timeout=600)
        run_command(["pnpm", "install", "--frozen-lockfile"], cwd=path, timeout=600)

    def _run_codex(self, run_id: int, issue: GitHubIssue, worktree: Path) -> None:
        prompt = f"""完成 GitHub Issue #{issue.number}。

标题：{issue.title}
正文：
{issue.body}

严格遵循仓库 AGENTS.md。先检查现有实现，再完成最小必要改动并补测试。
不要 commit、push、创建 PR、合并分支、修改 .env 或操作生产环境；这些由外部编排器负责。
完成后运行与改动相关的验证，并简洁报告改动和验证结果。
"""
        output_file = self.settings.data_dir / f"run-{run_id}-codex-final.txt"
        result = run_command(
            [
                str(self.settings.codex_path),
                "exec",
                "--cd",
                str(worktree),
                "--sandbox",
                "workspace-write",
                "--ephemeral",
                "--color",
                "never",
                "--output-last-message",
                str(output_file),
                "-",
            ],
            cwd=worktree,
            timeout=1800,
            input_text=prompt,
        )
        self.database.add_event(run_id, "Codex 开发完成", details={"output": result.stdout[-4000:]})

    def _run_quality_gate(self, run_id: int, worktree: Path) -> None:
        for command in QUALITY_COMMANDS:
            result = run_command(command, cwd=worktree, timeout=600)
            self.database.add_event(
                run_id,
                f"验证通过：{' '.join(command)}",
                details={"output": result.stdout[-2000:]},
            )

    def _commit_and_push(
        self, run_id: int, issue: GitHubIssue, worktree: Path, branch: str
    ) -> None:
        status = run_command(["git", "status", "--porcelain"], cwd=worktree).stdout
        if not status.strip():
            raise RuntimeError("Codex did not produce any file changes")
        run_command(["git", "add", "--all"], cwd=worktree)
        safe_title = re.sub(r"[\r\n]+", " ", issue.title).strip()[:60]
        message = f"[ ! ] Issue #{issue.number}，{safe_title}"
        run_command(["git", "commit", "-m", message], cwd=worktree)
        run_command(["git", "push", "-u", "origin", branch], cwd=worktree)
        self.database.add_event(run_id, "分支已提交并推送", details={"branch": branch})

    def _create_pr(
        self, run_id: int, issue: GitHubIssue, worktree: Path, branch: str
    ) -> tuple[int, str]:
        body = (
            f"Closes #{issue.number}\n\n"
            "## Agent 交付\n\n"
            "- 已按仓库 AGENTS.md 完成实现\n"
            "- 已通过后端测试、静态检查、前端测试与生产构建\n"
            "- 本 PR 不会自动合并，必须在本地管理页面完成三重确认\n"
        )
        return self.github.create_pr(
            worktree, title=f"[Agent] {issue.title}", body=body, branch=branch
        )

    async def approve_merge(self, run_id: int) -> None:
        run = self.database.get_run(run_id)
        if run is None or run["status"] != "awaiting_review" or not run["quality_passed"]:
            raise ValueError("该任务尚未通过质量门禁或不在待审核状态")
        self.database.update_run(run_id, merge_approved=1)
        self.database.add_event(run_id, "人工初次批准合并")

    async def confirm_merge(self, run_id: int, issue_number: int) -> None:
        run = self.database.get_run(run_id)
        if run is None or not run["merge_approved"] or not run["quality_passed"]:
            raise ValueError("必须先通过质量门禁并进行初次人工批准")
        if issue_number != run["issue_number"]:
            raise ValueError("Issue 编号不匹配")
        await asyncio.to_thread(self.github.merge_pr, int(run["pr_number"]))
        await asyncio.to_thread(self.github.set_state, issue_number, "agent-done")
        self.database.update_run(run_id, status="succeeded")
        self.database.add_event(run_id, "PR 已通过最终确认并合并")
