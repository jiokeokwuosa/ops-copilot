# Quickstart: Internal Support Ops Copilot

**Feature**: `001-ops-copilot`  
**Purpose**: Validate the feature end-to-end after implementation (not an implementation guide).

See also: [plan.md](./plan.md), [data-model.md](./data-model.md), [contracts/openapi.yaml](./contracts/openapi.yaml), [contracts/sse-events.md](./contracts/sse-events.md).

---

## Prerequisites

- Docker + Docker Compose
- Node.js 22+ and pnpm or npm
- Python 3.12 + uv or pip
- OpenAI-compatible API key (or local Ollama configured in `.env`)
- Optional: LangSmith API key for traces

---

## Setup

1. Copy the root env template and fill secrets:
   - `cp .env.example .env`
2. Start Postgres, API, and web. The API container runs migrations, seed, and corpus ingest on startup:
   - `npm start`
3. That command is `docker compose -f infra/docker-compose.yml up --build` from the repo root.
4. Open web: `http://localhost:3000`  
   API docs: `http://localhost:8000/docs`

Seeded demo users (exact values in seed script): one user in **Tenant A**, one in **Tenant B**.

---

## Validation scenarios

### V1 — Auth gate

1. Open chat without logging in → redirected or 401.
2. Log in as Tenant A user → land on chat / thread list.

**Expect**: FR-016 satisfied.

### V2 — Grounded answer + live timeline

1. Create a thread; ask an on-topic question covered by corpus (e.g. MFA reset if seeded).
2. Watch the timeline while waiting.

**Expect**:
- Searching step with query detail
- Reading step with source chips
- Writing answer with streaming tokens
- Final answer grounded in corpus (SC-001 sample; SC-006/SC-007)

### V3 — Off-topic refuse

1. Ask something outside support/ops domain (e.g. write a poem about unrelated news).

**Expect**: Explicit refusal step/message; no fabricated policy (SC-002 sample).

### V4 — Tool read + write approval

1. Ask to look up a stub ticket.
2. Ask to update that ticket’s status.

**Expect**:
- Tool step for read
- `approval_required` + approval UI before write
- Reject → no DB change; Approve → stub updated once (SC-003)

### V5 — Durable resume

1. Mid-approval or after a few messages, restart API container.
2. Reopen same thread id.

**Expect**: History + pending approval restored (SC-004).

### V6 — Tenant isolation

1. Copy a Tenant A thread id; log in as Tenant B; open that id.

**Expect**: 404/denied; no content leak (SC-005).

### V7 — Evals + trace

1. Run the golden suite from the API container/host:
   - `cd apps/api && ENVIRONMENT=test CHECKPOINT_BACKEND=memory pytest -m eval`
   - or authenticated `POST /v1/evals/run` with body `{"suite":"golden"}`
2. Cases live under `apps/api/app/evals/cases/` (grounding, refusal, tool).
3. Optional traces: set `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY`, and
   `LANGCHAIN_PROJECT` in `.env`, restart API, run a chat turn, then open the
   LangSmith project UI to inspect retrieve → grade → tool → approval → outcome.

**Expect**: Report with grounding/refusal/tool cases; trace shows steps (SC-009/SC-010).

---

## Contract checks

- SSE event shapes match [sse-events.md](./contracts/sse-events.md) (`apps/api/tests/contract/`).
- OpenAPI routes match [openapi.yaml](./contracts/openapi.yaml).

---

## Definition of done (quickstart)

All V1–V7 pass locally against Compose stack with seeded corpus and stubs.
