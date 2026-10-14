# Ops Copilot

Internal support/ops copilot — Next.js + FastAPI + LangGraph.

## Layout

- `apps/web` — Next.js (App Router), Tailwind, TanStack Query
- `apps/api` — FastAPI, LangChain/LangGraph, SQLAlchemy, Alembic
- `infra/` — Docker Compose (Postgres + pgvector, api, web)
- `docs/corpus/` — Seed knowledge for RAG
- `specs/001-ops-copilot/` — Spec, plan, tasks, contracts

## Quick start

See [specs/001-ops-copilot/quickstart.md](./specs/001-ops-copilot/quickstart.md).

```bash
cp .env.example .env
# fill OPENAI_API_KEY (and optional LangSmith keys)

npm start
```

`npm start` brings up Postgres, the API, and the web app. The API container applies migrations, seeds the demo users, and loads `docs/corpus` before it serves traffic. `npm stop` shuts the containers down.

Demo login: `alice@tenant-a.example` / `password123`
