# Knowledge Isle

Knowledge Isle is a private, bilingual AI knowledge base for uploading documents and asking questions with traceable source citations.

The project is currently in its foundation phase. The frozen MVP scope is documented in [`docs/MVP.md`](docs/MVP.md).
For a concise explanation of the implemented features, technologies, request flow, and study order, see [`docs/LEARNING.md`](docs/LEARNING.md).

## Stack

- Vue 3, TypeScript, Vite
- FastAPI, Pydantic, SQLAlchemy
- Celery, Redis
- PostgreSQL, pgvector
- MinIO
- Docker Compose

## Local development

Requirements: Node.js 24+, pnpm 11+, uv, and Docker.

### Recommended startup

Run these commands from the repository root. The Compose project only uses the Knowledge Isle services and volumes.

```powershell
cd D:\front_study\knowledge-isle
Copy-Item .env.example .env       # first run only; then edit secrets in .env
pnpm install
uv sync --all-packages
docker compose up -d postgres redis minio worker
uv run --package knowledge-isle-api alembic -c apps/api/alembic.ini upgrade head
```

Start the API in one terminal:

```powershell
$env:PYTHONPATH="apps/api/src"
uv run --package knowledge-isle-api uvicorn knowledge_isle_api.main:app --reload
```

Start the Vue web app in another terminal:

```powershell
pnpm dev:web
```

Open `http://127.0.0.1:5173`. The first visit opens `/setup`; create the sole administrator with the `ADMIN_SETUP_TOKEN` from `.env`.

Check service status and Worker logs with:

```powershell
docker compose ps
docker compose logs -f worker
```

Stop services without deleting data:

```powershell
docker compose down
```

Do not use `docker compose down -v` unless you intentionally want to delete the Knowledge Isle PostgreSQL and MinIO volumes.

### Individual startup commands

```bash
cp .env.example .env
pnpm install
uv sync --all-packages
docker compose up -d
```

Create the database schema:

```bash
uv run --package knowledge-isle-api alembic -c apps/api/alembic.ini upgrade head
```

Start the API:

```bash
uv run --package knowledge-isle-api uvicorn knowledge_isle_api.main:app --reload
```

Start the web app in another terminal:

```bash
pnpm dev:web
```

On the first visit, the app redirects to `/setup`. Create the sole administrator with the value configured in `ADMIN_SETUP_TOKEN`. After setup succeeds, the initialization endpoint is permanently closed by the database singleton constraint.

Run checks:

```bash
pnpm lint:web
pnpm typecheck:web
pnpm test:web
uv run --package knowledge-isle-api pytest apps/api/tests
uv run --package knowledge-isle-api ruff check apps/api
```

Run the isolated PostgreSQL integration check without touching another Compose project:

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

The integration project uses its own Compose project name, network, volume, database, and host port. Never replace the `knowledge-isle-integration` project name with an existing infrastructure project.

Do not commit `.env`, uploaded documents, database data, logs, API keys, or real private test documents.
