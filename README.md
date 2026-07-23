# Knowledge Isle

Knowledge Isle 是一个私有、支持中英文界面的 AI 知识库平台。你可以上传文档，在自己的知识范围内提问，并追溯回答对应的原文引用。

项目当前处于基础功能开发阶段，冻结版 MVP 范围见 [`docs/MVP.md`](docs/MVP.md)。
已实现功能、技术栈、请求链路和推荐学习顺序见 [`docs/LEARNING.md`](docs/LEARNING.md)。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Pinia、Vue Router、Vue I18n
- 后端：FastAPI、Pydantic、SQLAlchemy 2、Alembic
- 异步任务：Celery、Redis
- 数据库：PostgreSQL、pgvector
- 文件存储：MinIO
- 部署与基础设施：Docker Compose

## 本地开发

### 环境要求

- Node.js 24 或更高版本
- pnpm 11 或更高版本
- uv
- Docker Desktop

### 推荐启动方式

以下命令都在项目根目录执行。Docker Compose 只会使用 Knowledge Isle 自己的服务和数据卷。

第一次启动时，先复制环境变量文件并填写密钥：

```powershell
cd D:\front_study\knowledge-isle
Copy-Item .env.example .env       # 仅第一次执行，然后编辑 .env 中的密钥
pnpm install
uv sync --all-packages
```

启动 PostgreSQL、Redis、MinIO 和 Celery Worker：

```powershell
docker compose up -d postgres redis minio worker
```

执行数据库迁移：

```powershell
uv run --package knowledge-isle-api alembic -c apps/api/alembic.ini upgrade head
```

在一个终端启动 API：

```powershell
$env:PYTHONPATH="apps/api/src"
uv run --package knowledge-isle-api uvicorn knowledge_isle_api.main:app --reload
```

在另一个终端启动 Vue 前端：

```powershell
cd D:\front_study\knowledge-isle
pnpm dev:web
```

浏览器打开 `http://127.0.0.1:5173`。首次访问会进入 `/setup`，使用 `.env` 中的 `ADMIN_SETUP_TOKEN` 创建唯一管理员。

查看服务状态和 Worker 日志：

```powershell
docker compose ps
docker compose logs -f worker
```

停止服务但保留数据：

```powershell
docker compose down
```

除非你明确要删除 Knowledge Isle 的 PostgreSQL 和 MinIO 数据卷，否则不要使用 `docker compose down -v`。

### 分步启动命令

如果你希望分别执行每一步，可以使用以下命令：

```powershell
Copy-Item .env.example .env
pnpm install
uv sync --all-packages
docker compose up -d postgres redis minio worker
```

创建数据库结构：

```powershell
uv run --package knowledge-isle-api alembic -c apps/api/alembic.ini upgrade head
```

启动 API：

```powershell
$env:PYTHONPATH="apps/api/src"
uv run --package knowledge-isle-api uvicorn knowledge_isle_api.main:app --reload
```

在另一个终端启动前端：

```powershell
pnpm dev:web
```

初始化成功后，初始化接口会因数据库的单例约束永久关闭，之后直接使用管理员账号登录。

## 运行检查

前端检查：

```powershell
pnpm lint:web
pnpm typecheck:web
pnpm test:web
```

后端检查：

```powershell
uv run --package knowledge-isle-api pytest apps/api/tests
uv run --package knowledge-isle-api ruff check apps/api
uv run --package knowledge-isle-api mypy apps/api/src
uv run --package knowledge-isle-worker ruff check apps/worker/src
```

## 独立 PostgreSQL 集成测试

以下命令会使用独立的 Compose 项目、网络、数据卷、数据库和端口，不会连接其他 Compose 项目：

```powershell
$env:POSTGRES_HOST_PORT = "55432"
$env:POSTGRES_DB = "knowledge_isle_integration"
$env:POSTGRES_USER = "knowledge_isle_integration"
$env:POSTGRES_PASSWORD = "knowledge_isle_integration_only"
docker compose -p knowledge-isle-integration up -d postgres
$env:DATABASE_URL = "postgresql+asyncpg://knowledge_isle_integration:knowledge_isle_integration_only@127.0.0.1:55432/knowledge_isle_integration"
uv run --package knowledge-isle-api alembic -c apps/api/alembic.ini upgrade head
$env:INTEGRATION_DATABASE_URL = $env:DATABASE_URL
uv run --package knowledge-isle-api pytest -o addopts="" apps/api/integration_tests/test_postgres_auth.py
docker compose -p knowledge-isle-integration down -v --remove-orphans
```

不要把 `knowledge-isle-integration` 替换成公司已有基础设施使用的 Compose 项目名。

## 安全注意事项

不要将以下内容提交到 GitHub：

- `.env` 文件
- 上传的私密文档
- PostgreSQL 或 MinIO 数据
- 日志文件
- API Key、Token 和密码
- 包含真实隐私数据的测试文件
