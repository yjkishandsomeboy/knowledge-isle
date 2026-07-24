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

## 后续高级化路线

当前还没有把以下内容当作已完成：数据库级 pgvector ANN 索引、SSE 流式回答、离线评估集、Tracing/指标监控。
当前向量召回使用应用层余弦计算，适合学习和小规模 MVP；下一步应改为 PostgreSQL pgvector `<=>` 查询并增加 ANN 索引。

## 验证命令

```powershell
uv run --package knowledge-isle-api pytest apps/api/tests
uv run --package knowledge-isle-api ruff check apps/api/src apps/api/tests
uv run --package knowledge-isle-worker ruff check apps/worker/src
uv run --package knowledge-isle-api mypy apps/api/src
uv run --package knowledge-isle-api alembic -c apps/api/alembic.ini upgrade head
pnpm --filter @knowledge-isle/web typecheck
pnpm --filter @knowledge-isle/web test
pnpm --filter @knowledge-isle/web build
```
