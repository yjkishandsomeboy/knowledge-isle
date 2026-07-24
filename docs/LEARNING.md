# Knowledge Isle 学习笔记

这份文档记录项目已经实现的技术和推荐阅读顺序，不粘贴完整源码。

## 当前已实现

- Vue 3、TypeScript、Vite、Pinia、Vue Router、Vue I18n：前端页面、状态管理、路由和中英文切换。
- FastAPI、Pydantic、SQLAlchemy 2 Async、Alembic：异步 API、数据校验、ORM 和数据库迁移。
- Argon2、Session、HttpOnly Cookie：管理员认证和会话保护。
- MinIO：保存私有原文件；PostgreSQL 只保存可查询的元数据和提取文本。
- Redis + Celery：异步文档处理，失败任务自动重试。
- 文档切片：Worker 提取文本后按自然边界和固定窗口生成 `document_chunks`，支持重复处理而不产生重复序号。
- 问答 MVP：正文关键词检索和文件名检索并发执行，回答保存会话、消息、切片级引用及字符位置。
- 向量检索基础：可选调用 Embeddings API，为切片保存向量并进行余弦相似度召回；默认关闭，不影响关键词检索。
- SSE 流式问答：Responses API 的增量文本通过 `event: delta` 返回，结束事件携带会话和引用元数据。
- 离线评估：`evals/retrieval.jsonl` 保存脱敏样例，脚本计算 Recall@K、Precision@5 和 MRR，不调用外部 AI。
- 可观测性：API 统一记录 `X-Request-ID`、HTTP 总耗时、检索耗时和 AI 调用耗时，便于定位慢请求。
- 本地自动开发：Planner Agent 用 Codex 只读审计仓库并生成结构化候选任务，Python 再进行风险分级、去重和每日限额；Dev Agent 在独立 Git worktree 中开发、测试并创建 PR，最终合并仍由人工确认。

## 一次上传的链路

```text
Vue 上传 -> FastAPI 鉴权与校验 -> MinIO 保存原文件
         -> Redis/Celery -> Worker 提取文本 -> 生成 document_chunks
         -> PostgreSQL 保存状态 -> 问答时并发检索切片并记录引用
```

## 推荐阅读顺序

1. `apps/api/src/knowledge_isle_api/api/routes/documents.py`：理解 HTTP 路由和权限依赖。
2. `apps/api/src/knowledge_isle_api/services/documents.py`：理解上传业务和任务投递。
3. `apps/worker/src/knowledge_isle_worker/tasks.py`：理解异步任务、重试和切片入库。
4. `apps/api/src/knowledge_isle_api/services/chunking.py`：理解可重复的切片边界算法。
5. `apps/api/src/knowledge_isle_api/services/retrieval.py`：理解并发召回、评分和引用位置。
6. `apps/api/src/knowledge_isle_api/services/chat.py`：理解检索结果如何进入 AI 和数据库。
7. `apps/api/migrations/versions/`：理解数据库结构如何版本化演进。
8. `apps/api/src/knowledge_isle_api/services/evaluation.py` 和 `scripts/evaluate_retrieval.py`：理解检索质量如何量化。
9. `apps/dev-agent/src/knowledge_isle_dev_agent/planner.py`：理解模型输出为什么必须经过本地安全策略重新裁决。
10. `apps/dev-agent/src/knowledge_isle_dev_agent/runner.py`：理解 Issue、Codex、质量门禁、Git 分支和 PR 如何组成状态机。

## 后续高级化路线

当前还没有把以下内容当作已完成：离线评估集、Tracing/指标监控。
语义召回已经使用 PostgreSQL pgvector `<=>` 查询和 HNSW 索引；Embedding 仍需在 `.env` 中显式开启。

## 验证命令

```powershell
uv run --package knowledge-isle-api pytest apps/api/tests
uv run --package knowledge-isle-api ruff check apps/api/src apps/api/tests
uv run --package knowledge-isle-worker ruff check apps/worker/src
uv run --package knowledge-isle-api mypy apps/api/src
uv run --package knowledge-isle-api alembic -c apps/api/alembic.ini upgrade head
uv run --package knowledge-isle-api python scripts/evaluate_retrieval.py
pnpm --filter @knowledge-isle/web typecheck
pnpm --filter @knowledge-isle/web test
pnpm --filter @knowledge-isle/web build
```
