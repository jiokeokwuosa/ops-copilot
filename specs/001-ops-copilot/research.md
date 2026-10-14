# Research: Internal Support Ops Copilot

**Feature**: `001-ops-copilot` | **Date**: 2026-09-22

All Technical Context unknowns resolved. Decisions below drive `plan.md`, `data-model.md`, and `contracts/`.

---

## 1. Monorepo layout

- **Decision**: `apps/web` (Next.js) + `apps/api` (FastAPI) + `infra/docker-compose.yml`
- **Rationale**: Matches frontend/backend split; clear ownership; constitution clarity (cohesive modules).
- **Alternatives considered**: Single Next.js with Route Handlers only (weak for LangGraph/Python ecosystem); separate repos (overhead for a learning project).

---

## 2. Agent orchestration & streaming

- **Decision**: LangGraph StateGraph with nodes: `route_or_refuse` → `retrieve` → `grade` → (`rewrite` loop, bounded) → `read_sources` → `tools` (optional) → `interrupt` on writes → `generate`. Stream via `graph.astream(..., stream_mode=["updates", "messages", "custom"])` mapped to SSE events (`step`, `step_detail`, `token`, `approval_required`, `done`, `error`).
- **Rationale**: Spec requires live phase timeline + token streaming; LangGraph streaming + `interrupt_before` (or interrupt inside write tool node) is the intended learning stack.
- **Alternatives considered**: Pure LangChain AgentExecutor (weaker durable interrupts); custom FSM without LangGraph (more code, less ecosystem); WebSockets instead of SSE (heavier; SSE sufficient for server→client stream + separate POST for approve).

---

## 3. Durable memory / checkpointer

- **Decision**: LangGraph **AsyncPostgresSaver** (Postgres) as primary checkpointer; same Postgres instance as app data. `thread_id` = app thread UUID string. Local fallback: SQLite checkpointer only for unit tests without Docker.
- **Rationale**: Spec calls for durable threads + pending approval across restart; Postgres is user-selected; one DB simplifies ops.
- **Alternatives considered**: MemorySaver (not durable); separate Redis checkpointer (extra infra); SQLite for all envs (weak concurrent multi-tenant demo).

---

## 4. RAG store

- **Decision**: PostgreSQL + **pgvector**; LangChain PGVector (or direct SQLAlchemy) for chunk embeddings; seed from `docs/corpus/**/*.md`. Embeddings via configured OpenAI-compatible API.
- **Rationale**: Keeps one database; good enough for internal corpus scale; aligns with “Postgres” choice.
- **Alternatives considered**: Chroma/Qdrant (extra service); OpenAI file search (less portable learning); BM25-only (weaker for semantic ops questions).

---

## 5. Advanced RAG loop

- **Decision**: Explicit graph edges: retrieve → grade (binary/score + rationale) → if fail and retries &lt; N rewrite query → retrieve again → else refuse or proceed to read/generate. Max retries = 2.
- **Rationale**: Matches FR-003/FR-004 and learning goals; testable nodes.
- **Alternatives considered**: Single-shot RAG (fails “advanced RAG”); unbounded rewrite (risk of loops).

---

## 6. Tools & write approval

- **Decision**: LangChain tools: `docs_search` (real vector/keyword), `ticket_get` / `ticket_update` (in-memory or DB stub), `crm_get` / `crm_add_note` (stub). Mark write tools; compile graph with `interrupt_before=["execute_write"]` or interrupt after proposing write. Resume with `Command(resume=True/False)` (or equivalent) via `POST /threads/{id}/approvals`.
- **Rationale**: Spec FR-006–FR-007, FR-020–FR-021; stubs keep scope demable.
- **Alternatives considered**: Auto-approve writes (unsafe); always-on human-in-the-loop for reads (noise).

---

## 7. Frontend stack

- **Decision**: Next.js App Router, Tailwind, TypeScript, **TanStack Query** for REST (threads list, history, auth profile); **fetch + ReadableStream** (or `eventsource-parser`) for SSE chat stream; local React state for in-flight timeline steps.
- **Rationale**: User-requested stack; Query shines for cacheable REST; streaming is a poor fit for Query mutations alone.
- **Alternatives considered**: SWR (fine, but user asked React Query); tRPC (Python backend friction); Socket.io (unnecessary).

---

## 8. Auth & multi-tenancy

- **Decision**: FastAPI issues JWT (access token) after email/password demo login (seeded users with `tenant_id`). Next.js stores token in httpOnly cookie via Route Handler BFF or Authorization header from secure cookie. Every thread row has `tenant_id` + `user_id`; list/get/stream/approve enforce match.
- **Rationale**: Spec FR-016–FR-017; simple for learning without full IdP.
- **Alternatives considered**: Auth.js + external IdP (heavier); API keys only (weak UX); row-level Postgres policies later (YAGNI for v1; app-layer checks first).

---

## 9. API transport for timeline

- **Decision**: `POST /v1/threads/{thread_id}/chat` returns `text/event-stream` with typed events (see `contracts/openapi.yaml` + `sse-events.md`). Client renders vertical timeline from `step` / `step_detail` events; appends tokens from `token` events.
- **Rationale**: Matches screenshot UX; works through Next proxy; simpler than WebSockets for this pattern.
- **Alternatives considered**: NDJSON over fetch; polling (fails live feel); gRPC streaming (browser friction).

---

## 10. Observability & evals

- **Decision**: **LangSmith** tracing enabled via env (`LANGCHAIN_TRACING_V2`, API key, project). Evals: pytest + LangSmith datasets optional; local golden JSON cases under `apps/api/app/evals/cases/` run with `pytest -m eval` or `python -m app.evals.run`.
- **Rationale**: Spec FR-018–FR-019 / SC-009–SC-010; LangSmith matches “LangSmith-style tracing” learning goal.
- **Alternatives considered**: Only OpenTelemetry (less LLM-native); Phoenix (good alternative; LangSmith preferred for curriculum fit).

---

## 11. LLM provider

- **Decision**: Pluggable via env: default OpenAI (`gpt-4o-mini` or similar for cost) + `text-embedding-3-small`; allow Azure/OpenAI-compatible base URL.
- **Rationale**: Fastest path for LangChain/LangGraph demos; swappable.
- **Alternatives considered**: Local Ollama only (good offline alt; document as optional in quickstart).

---

## 12. Validation & quality tooling

- **Decision**: Backend: ruff, pytest, httpx ASGITransport. Frontend: eslint, prettier, tsc, Vitest. Pre-commit or CI scripts at repo root. Docker Compose healthchecks for Postgres.
- **Rationale**: Constitution quality constraints + test-first.
- **Alternatives considered**: Black-only (ruff covers more); Jest (Vitest faster in Vite/Next ecosystem).

---

## 13. UI timeline mapping

- **Decision**: Map graph events to labels: Searching (query detail) → Checking sources (grade) → Reading (source chips) → Tool steps → Waiting for approval → Writing answer (tokens). Persist completed step timeline on Message metadata for FR-022.
- **Rationale**: Spec User Story 4 + screenshot reference.
- **Alternatives considered**: Collapsed “thinking” accordion only (fails SC-008).
