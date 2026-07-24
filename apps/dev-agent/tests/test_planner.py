import json

import pytest

from knowledge_isle_dev_agent.planner import (
    PlannerTask,
    classify_task,
    issue_body,
    parse_planner_output,
    task_fingerprint,
)


def task(**changes: object) -> PlannerTask:
    values = {
        "title": "补充文档启动说明",
        "summary": "README 缺少本地 Planner 的启动说明。",
        "risk": "low",
        "category": "docs",
        "evidence": ["README.md:20"],
        "constraints": ["不修改程序行为"],
        "acceptance_criteria": ["README 能说明启动命令"],
        "auto_ready": True,
    }
    values.update(changes)
    return PlannerTask(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (task(), ("low", True)),
        (task(category="tests"), ("low", True)),
        (task(category="database", title="增加数据库迁移"), ("high", False)),
        (task(category="auth", title="修改登录权限"), ("high", False)),
        (task(category="deployment", title="更新生产部署"), ("high", False)),
        (task(category="dependency", title="升级 Vue"), ("medium", False)),
        (
            task(
                category="tests",
                constraints=["不修改数据库结构", "不读取 Token"],
            ),
            ("low", True),
        ),
    ],
)
def test_risk_is_recalculated_by_local_policy(
    candidate: PlannerTask, expected: tuple[str, bool]
) -> None:
    assert classify_task(candidate) == expected


def test_fingerprint_ignores_title_case_and_spacing() -> None:
    assert task_fingerprint(task(title="Add  Tests")) == task_fingerprint(
        task(title=" add tests ")
    )


def test_parser_limits_output_to_three_tasks() -> None:
    record = {
        "title": "补充一个有效测试任务",
        "summary": "现有测试缺少一个明确的成功路径。",
        "risk": "low",
        "category": "tests",
        "evidence": ["apps/api/tests/test_app.py:1"],
        "constraints": [],
        "acceptanceCriteria": ["测试通过"],
        "autoReady": True,
    }
    parsed = parse_planner_output(json.dumps({"tasks": [record] * 5}))
    assert len(parsed) == 3


def test_issue_body_contains_evidence_acceptance_and_decision() -> None:
    body = issue_body(task(), "low", True)
    assert "README.md:20" in body
    assert "- [ ] README 能说明启动命令" in body
    assert "自动进入 Dev Agent 队列" in body
