# Knowledge Isle

Knowledge Isle is a private, bilingual AI knowledge base for uploading documents and asking questions with traceable source citations.

The project is currently in its foundation phase. The frozen MVP scope is documented in [`docs/MVP.md`](docs/MVP.md).

## Stack

- Vue 3, TypeScript, Vite
- FastAPI, Pydantic, SQLAlchemy
- Celery, Redis
- PostgreSQL, pgvector
- MinIO
- Docker Compose

## Local development

Requirements: Node.js 24+, pnpm 11+, uv, and Docker.

```bash
cp .env.example .env
pnpm install
uv sync --all-packages
docker compose up -d
```

Start the API:

```bash
uv run --package knowledge-isle-api uvicorn knowledge_isle_api.main:app --reload
```

Start the web app in another terminal:

```bash
pnpm dev:web
```

Run checks:

```bash
pnpm lint:web
pnpm typecheck:web
pnpm test:web
uv run --package knowledge-isle-api pytest apps/api/tests
uv run --package knowledge-isle-api ruff check apps/api
```

Do not commit `.env`, uploaded documents, database data, logs, API keys, or real private test documents.
