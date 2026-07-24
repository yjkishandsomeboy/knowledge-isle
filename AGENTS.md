# Knowledge Isle Agent 开发约定

## 项目范围

- `apps/web`：Vue 3 + TypeScript 前端。
- `apps/api`：FastAPI + SQLAlchemy 后端。
- `apps/worker`：Celery 文档处理任务。
- `apps/dev-agent`：Windows 本地自动开发 Agent。

## 开发规则

- 只实现当前 GitHub Issue 明确要求的内容，不顺手重构无关代码。
- 不读取、修改或提交 `.env`、密钥、Token 和私人文档内容。
- 不删除数据库数据，不操作生产环境，不自动合并 Pull Request。
- 数据库结构变化必须使用 Alembic 迁移。
- 所有代码使用 UTF-8。
- 提交信息使用中文，并遵循 `[ + ]`、`[ ! ]`、`[ ! ] fix`、`[ - ]` 前缀规范。

## 完成标准

根据改动范围运行相关检查；跨前后端改动运行全部检查：

```powershell
uv run --package knowledge-isle-api ruff check apps/api/src apps/api/tests
uv run --package knowledge-isle-api mypy apps/api/src
uv run --package knowledge-isle-api pytest apps/api/tests
uv run --package knowledge-isle-worker ruff check apps/worker/src
pnpm --filter @knowledge-isle/web typecheck
pnpm --filter @knowledge-isle/web test
pnpm --filter @knowledge-isle/web build
```

完成前检查 `git diff --check`，并在 PR 中说明改动、验证结果和风险。
