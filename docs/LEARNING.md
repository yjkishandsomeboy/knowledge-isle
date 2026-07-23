# Knowledge Isle 学习笔记

这份笔记记录当前已经实现的内容和推荐学习顺序。它是项目导航，不重复粘贴完整源码。

## 1. 当前版本做了什么

- 初始化唯一管理员、登录、退出登录。
- 使用 Session + HttpOnly Cookie 保护 API。
- 创建、查询、修改、删除知识库。
- 上传 PDF、Markdown、TXT 文件。
- 将原文件保存到 MinIO 私有 Bucket。
- 提取文本并保存文档状态：`processing`、`processed`、`failed`。
- 提供文档列表接口。
- 使用 Alembic 管理数据库结构变更。

上传接口现在只负责保存原文件并投递任务；Celery Worker 从 MinIO 取回文件、提取文本并更新 PostgreSQL 状态。

## 2. 技术栈与作用

### 前端

- Vue 3：组件化页面和响应式状态。
- TypeScript：为 API 数据和组件逻辑提供类型检查。
- Vite：开发服务器和生产构建。
- Pinia：管理登录状态、知识库列表等客户端状态。
- Vue Router：登录、初始化和应用页面路由。
- Vue I18n：中文/英文切换。

### 后端

- FastAPI：HTTP API、参数校验和 OpenAPI 文档。
- Pydantic：请求与响应 Schema，自动生成 camelCase API 字段。
- SQLAlchemy 2 Async：异步数据库访问和 ORM 模型。
- Alembic：用版本化迁移创建和修改表结构。
- Argon2：密码哈希。
- MinIO SDK：把文件保存到私有对象存储。
- pypdf：提取 PDF 文本。

### 基础设施

- PostgreSQL + pgvector：业务数据和后续向量检索。
- Redis：后续 Celery 队列和缓存。
- Celery：后续异步解析、切片和向量化任务。
- Docker Compose：本地和服务器上的基础服务编排。

## 3. 一次上传的请求链路

```text
浏览器选择文件
  -> FastAPI 校验登录、知识库归属、MIME 类型
  -> MinIO 保存原文件
  -> Redis 队列保存文档 ID
  -> Celery Worker 从 MinIO 读取文件
  -> pypdf 或 UTF-8 解码提取文本
  -> PostgreSQL 保存文档元数据、文本和处理状态
  -> 前端刷新列表看到 processed / failed
```

重点：数据库只保存对象键和文本元数据，原文件本身保存在 MinIO；Bucket 不对公网开放。

## 4. 建议阅读顺序

1. `apps/api/src/knowledge_isle_api/api/routes/documents.py`：理解 FastAPI 路由、认证依赖和上传校验。
2. `apps/api/src/knowledge_isle_api/services/documents.py`：理解业务流程、文本提取和状态处理。
3. `apps/api/src/knowledge_isle_api/services/storage.py`：理解 MinIO 客户端和私有 Bucket。
4. `apps/api/src/knowledge_isle_api/models/document.py`：理解 ORM 模型和数据库字段。
5. `apps/api/migrations/versions/20260723_0003_create_documents.py`：理解数据库迁移。
6. `apps/api/tests/test_documents.py`：理解上传成功、列表和非法类型测试。
7. `apps/web/src/views/DashboardView.vue` 与 `apps/web/src/stores/knowledgeBases.ts`：理解 Vue 页面和 Pinia。

## 5. 学习时要掌握的概念

- 路由层只负责 HTTP 输入输出，业务规则放在 service 层。
- Schema 负责 API 契约，Model 负责数据库结构，两者不要混用。
- `owner_id` 和知识库归属检查是权限边界，不能只依赖前端隐藏按钮。
- 对象存储适合保存文件，PostgreSQL 适合保存可查询的元数据。
- Alembic 迁移必须可重复执行，并且要有 downgrade 思路。
- 测试通过 monkeypatch 替代真实 MinIO，避免单元测试依赖外部服务。

## 6. 常用验证命令

```powershell
uv run --package knowledge-isle-api pytest apps/api/tests
uv run --package knowledge-isle-api ruff check apps/api
uv run --package knowledge-isle-api mypy apps/api/src
uv run --package knowledge-isle-api alembic -c apps/api/alembic.ini upgrade head
```

## 7. 后续学习路线

下一阶段增加文档切片、Embedding、pgvector 相似度检索，最后接入 Responses API 并返回可追溯引用。每一步都会先补测试，再扩展前端页面。
