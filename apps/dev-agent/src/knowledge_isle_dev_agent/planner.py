import asyncio
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from knowledge_isle_dev_agent.commands import run_command
from knowledge_isle_dev_agent.config import AgentSettings
from knowledge_isle_dev_agent.database import AgentDatabase
from knowledge_isle_dev_agent.github import GitHubClient

SAFE_CATEGORIES = {"docs", "tests", "bug", "ui", "quality"}
MEDIUM_CATEGORIES = {"dependency"}
HIGH_CATEGORIES = {"database", "auth", "deployment", "architecture"}
DANGEROUS_TERMS = {
    "alembic",
    "architecture",
    "auth",
    "authorization",
    "database",
    "delete",
    "deploy",
    "docker",
    "drop",
    "migration",
    "nginx",
    "permission",
    "production",
    "refactor",
    "secret",
    "security",
    "token",
    "upgrade",
    "认证",
    "授权",
    "删除",
    "数据库",
    "部署",
    "迁移",
    "重构",
}


@dataclass(frozen=True)
class PlannerTask:
    title: str
    summary: str
    risk: str
    category: str
    evidence: list[str]
    constraints: list[str]
    acceptance_criteria: list[str]
    auto_ready: bool

    @classmethod
    def from_dict(cls, record: dict[str, Any]) -> "PlannerTask":
        return cls(
            title=str(record["title"]).strip(),
            summary=str(record["summary"]).strip(),
            risk=str(record["risk"]),
            category=str(record["category"]),
            evidence=[str(item).strip() for item in record["evidence"] if str(item).strip()],
            constraints=[
                str(item).strip() for item in record["constraints"] if str(item).strip()
            ],
            acceptance_criteria=[
                str(item).strip()
                for item in record["acceptanceCriteria"]
                if str(item).strip()
            ],
            auto_ready=bool(record["autoReady"]),
        )


def parse_planner_output(raw: str) -> list[PlannerTask]:
    payload = json.loads(raw)
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("Planner output does not contain a tasks list")
    return [PlannerTask.from_dict(record) for record in tasks[:3]]


def task_fingerprint(task: PlannerTask) -> str:
    normalized = re.sub(r"\s+", " ", task.title.strip().casefold())
    return hashlib.sha256(f"{task.category}:{normalized}".encode()).hexdigest()


def classify_task(task: PlannerTask) -> tuple[str, bool]:
    searchable = " ".join(
        [task.title, task.summary, *task.constraints, *task.acceptance_criteria]
    ).casefold()
    if task.category in HIGH_CATEGORIES or any(term in searchable for term in DANGEROUS_TERMS):
        return "high", False
    if task.category in MEDIUM_CATEGORIES or task.risk in {"medium", "high"}:
        return "medium", False
    auto_ready = (
        task.category in SAFE_CATEGORIES
        and task.risk == "low"
        and task.auto_ready
        and bool(task.evidence)
        and bool(task.acceptance_criteria)
    )
    return "low", auto_ready


def issue_body(task: PlannerTask, risk: str, auto_ready: bool) -> str:
    evidence = "\n".join(f"- {item}" for item in task.evidence)
    constraints = "\n".join(f"- {item}" for item in task.constraints) or "- 遵循 AGENTS.md"
    acceptance = "\n".join(f"- [ ] {item}" for item in task.acceptance_criteria)
    decision = "自动进入 Dev Agent 队列" if auto_ready else "等待人工审核后添加 agent-ready"
    return f"""## 目标

{task.summary}

## 发现证据

{evidence}

## 约束

{constraints}

## 验收标准

{acceptance}

## Planner 决策

- 风险等级：`{risk}`
- 分类：`{task.category}`
- 后续动作：{decision}

> 此 Issue 由 Knowledge Isle 本地 Planner Agent 只读审计后创建。
"""


class PlannerAgent:
    def __init__(
        self,
        settings: AgentSettings,
        database: AgentDatabase,
        github: GitHubClient,
        execution_lock: asyncio.Lock,
    ) -> None:
        self.settings = settings
        self.database = database
        self.github = github
        self.execution_lock = execution_lock
        self.lock = asyncio.Lock()
        self._scheduled = False

    @property
    def busy(self) -> bool:
        return self._scheduled or self.lock.locked()

    def is_due(self) -> bool:
        latest = self.database.latest_planner_run()
        if latest is None:
            return True
        timestamp = latest.get("completed_at") or latest["started_at"]
        completed_at = datetime.fromisoformat(str(timestamp))
        return datetime.now(UTC) - completed_at >= timedelta(
            hours=self.settings.planner_interval_hours
        )

    async def start(self, *, force: bool = False) -> int | None:
        if self.busy or self.execution_lock.locked():
            return None
        if not force and not self.is_due():
            return None
        run_id = self.database.create_planner_run()
        self._scheduled = True
        asyncio.create_task(self._execute(run_id))
        return run_id

    async def _execute(self, run_id: int) -> None:
        async with self.lock, self.execution_lock:
            created = 0
            candidate_count = 0
            try:
                used = self.database.planner_issues_created_in_last_day()
                available = max(0, self.settings.planner_max_tasks - used)
                if available == 0:
                    self.database.complete_planner_run(run_id, status="rate_limited")
                    return
                tasks = await asyncio.to_thread(self._run_codex)
                candidate_count = len(tasks)
                open_titles = await asyncio.to_thread(self.github.open_issue_titles)
                for task in tasks:
                    if created >= available:
                        break
                    fingerprint = task_fingerprint(task)
                    if (
                        self.database.planner_fingerprint_seen(fingerprint)
                        or task.title.casefold() in open_titles
                    ):
                        continue
                    risk, auto_ready = classify_task(task)
                    labels = ["agent-planned", f"risk-{risk}"]
                    labels.append("agent-ready" if auto_ready else "agent-needs-approval")
                    number, url = await asyncio.to_thread(
                        self.github.create_issue,
                        title=task.title,
                        body=issue_body(task, risk, auto_ready),
                        labels=labels,
                    )
                    self.database.add_planner_candidate(
                        run_id,
                        fingerprint=fingerprint,
                        title=task.title,
                        summary=task.summary,
                        category=task.category,
                        risk_level=risk,
                        auto_ready=auto_ready,
                        issue_number=number,
                        issue_url=url,
                        evidence=task.evidence,
                    )
                    open_titles.add(task.title.casefold())
                    created += 1
                self.database.complete_planner_run(
                    run_id,
                    status="succeeded",
                    candidates_count=candidate_count,
                    issues_created=created,
                )
            except Exception as error:
                self.database.complete_planner_run(
                    run_id,
                    status="failed",
                    candidates_count=candidate_count,
                    issues_created=created,
                    error=str(error)[-4000:],
                )
            finally:
                self._scheduled = False

    def _run_codex(self) -> list[PlannerTask]:
        run_command(["git", "fetch", "origin", "main"], cwd=self.settings.repo_root)
        audit_worktree = self.settings.worktree_dir / "planner-audit"
        if audit_worktree.exists():
            run_command(
                ["git", "worktree", "remove", "--force", str(audit_worktree)],
                cwd=self.settings.repo_root,
            )
        run_command(
            ["git", "worktree", "add", "--detach", str(audit_worktree), "origin/main"],
            cwd=self.settings.repo_root,
        )
        output_file = self.settings.data_dir / "planner-codex-final.json"
        schema_file = Path(__file__).with_name("planner_schema.json")
        prompt = (
            "你是 Knowledge Isle 的只读 Planner Agent。审计当前仓库，最多提出 "
            f"{self.settings.planner_max_tasks} 个高价值、范围明确、可验证且当前确实需要的"
            "开发任务。\n\n"
            "只检查 README、docs、apps 下的源码与测试、CI 配置、TODO/FIXME 和可见的"
            "测试/构建配置。严禁读取或输出 .env、密钥、Token、data/dev-agent、用户文档"
            "内容和仓库外文件。不要修改任何文件，不要创建提交、分支、Issue 或 PR。\n\n"
            "优先：缺失测试、明确 Bug、文档偏差、小型 UI 可用性和小范围代码质量问题。"
            "不得为了凑数创建任务；没有可靠证据时返回空 tasks。证据必须包含具体文件"
            "路径和行号或明确的测试信号。数据库迁移、认证授权、安全、删除、部署、依赖"
            "大版本和架构重构必须标为 medium/high 且 autoReady=false。只有 docs/tests/"
            "bug/ui/quality 中边界清晰的低风险任务才可 autoReady=true。\n"
        )
        try:
            run_command(
                [
                    str(self.settings.codex_path),
                    "exec",
                    "--cd",
                    str(audit_worktree),
                    "--sandbox",
                    "read-only",
                    "--ephemeral",
                    "--color",
                    "never",
                    "--output-schema",
                    str(schema_file),
                    "--output-last-message",
                    str(output_file),
                    "-",
                ],
                cwd=audit_worktree,
                timeout=1800,
                input_text=prompt,
            )
            return parse_planner_output(output_file.read_text(encoding="utf-8"))
        finally:
            run_command(
                ["git", "worktree", "remove", "--force", str(audit_worktree)],
                cwd=self.settings.repo_root,
                check=False,
            )
