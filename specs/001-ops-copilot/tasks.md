# Tasks: Internal Support Ops Copilot

**Input**: Design documents from `/specs/001-ops-copilot/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included (constitution Principle II — Test-First is NON-NEGOTIABLE; plan requires contract/integration tests)

**Organization**: Tasks grouped by user story for independent implementation and testing

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1–US6)
- Paths follow `apps/web`, `apps/api`, `infra/`, `docs/` from plan.md

## Path Conventions

- API: `apps/api/app/`, tests in `apps/api/tests/`
- Web: `apps/web/src/`, tests in `apps/web/tests/`
- Infra: `infra/`
- Corpus: `docs/corpus/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Monorepo initialization and tooling

- [x] T001 Create monorepo directories `apps/api/`, `apps/web/`, `infra/`, `docs/corpus/` per plan.md structure
- [x] T002 Initialize FastAPI project with `apps/api/pyproject.toml` (FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2, Alembic, LangChain, LangGraph, httpx, pytest, ruff)
- [x] T003 [P] Initialize Next.js App Router + TypeScript app in `apps/web/` with Tailwind CSS and TanStack Query v5
- [x] T004 [P] Add `infra/docker-compose.yml` with Postgres 16 + pgvector, api, and web services
- [x] T005 [P] Add root `.env.example` with DATABASE_URL, JWT_SECRET, OPENAI_API_KEY, LANGCHAIN_* placeholders (no secrets)
- [x] T006 [P] Configure API lint/format in `apps/api/pyproject.toml` (ruff) and `apps/api/tests/conftest.py` skeleton
- [x] T007 [P] Configure web eslint, prettier, and Vitest in `apps/web/package.json` and `apps/web/vitest.config.ts`
- [x] T008 [P] Add root README with monorepo overview linking to `specs/001-ops-copilot/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared DB, auth, API/web shells, and thread CRUD that all stories need

**⚠️ CRITICAL**: No user story work begins until this phase is complete

- [x] T009 Implement settings and structured logging in `apps/api/app/core/settings.py` and `apps/api/app/core/logging.py`
- [x] T010 [P] Implement SQLAlchemy base + session in `apps/api/app/db/base.py` and `apps/api/app/db/session.py`
- [x] T011 [P] Create Tenant and User models in `apps/api/app/db/models/tenant.py` and `apps/api/app/db/models/user.py`
- [x] T012 Create Thread and Message models in `apps/api/app/db/models/thread.py` and `apps/api/app/db/models/message.py`
- [x] T013 Configure Alembic in `apps/api/alembic/` and initial migration for tenants, users, threads, messages
- [x] T014 Implement JWT auth helpers and dependencies in `apps/api/app/auth/jwt.py` and `apps/api/app/auth/deps.py`
- [x] T015 Implement `POST /v1/auth/login` and `GET /v1/auth/me` in `apps/api/app/routes/auth.py` wired in `apps/api/app/main.py`
- [x] T016 Implement thread list/create/get in `apps/api/app/routes/threads.py` with tenant-scoped queries
- [x] T017 Add seed script for two tenants and users in `apps/api/app/db/seed.py`
- [x] T018 [P] Add Zod API schemas and fetch client in `apps/web/src/lib/schemas.ts` and `apps/web/src/lib/api.ts`
- [x] T019 [P] Add login page and httpOnly cookie/session bridge in `apps/web/src/app/login/page.tsx` and `apps/web/src/app/api/auth/[...]/route.ts`
- [x] T020 Add chat shell routes `apps/web/src/app/page.tsx` and `apps/web/src/app/chat/[threadId]/page.tsx` with TanStack Query thread list
- [x] T021 Write failing contract tests for auth + threads OpenAPI paths in `apps/api/tests/contract/test_auth_threads.py`

**Checkpoint**: Foundation ready — login, JWT, tenant-scoped threads, Compose DB up

---

## Phase 3: User Story 1 — Grounded Answers From Internal Knowledge (Priority: P1) 🎯 MVP

**Goal**: Authenticated users get grounded answers from internal docs via retrieve → grade → rewrite → refuse

**Independent Test**: Seeded corpus; on-topic questions return grounded answers; off-topic/ungrounded refuse; no ticket/CRM tools required

### Tests for User Story 1

> Write these tests FIRST; ensure they FAIL before implementation

- [x] T022 [P] [US1] Contract/unit tests for retrieve-grade-rewrite-refuse behavior in `apps/api/tests/unit/test_rag_loop.py`
- [x] T023 [P] [US1] Integration test for on-topic grounded chat turn in `apps/api/tests/integration/test_grounded_chat.py`
- [x] T024 [P] [US1] Integration test for off-topic refusal in `apps/api/tests/integration/test_refuse_offtopic.py`

### Implementation for User Story 1

- [x] T025 [P] [US1] Add Document and DocumentChunk models + migration in `apps/api/app/db/models/document.py` and `apps/api/alembic/versions/`
- [x] T026 [P] [US1] Add sample internal markdown corpus under `docs/corpus/` (policies/runbooks)
- [x] T027 [US1] Implement embedding ingest CLI in `apps/api/app/rag/ingest.py` (pgvector)
- [x] T028 [P] [US1] Implement retrieve in `apps/api/app/rag/retrieve.py`
- [x] T029 [P] [US1] Implement grade and rewrite in `apps/api/app/rag/grade.py` and `apps/api/app/rag/rewrite.py`
- [x] T030 [US1] Define LangGraph state and nodes (route/refuse, retrieve, grade, rewrite, generate) in `apps/api/app/graph/state.py` and `apps/api/app/graph/nodes/`
- [x] T031 [US1] Wire StateGraph compile in `apps/api/app/graph/build.py` (MemorySaver OK for MVP; Postgres checkpointer in US3)
- [x] T032 [US1] Implement chat endpoint that runs graph and returns assistant message in `apps/api/app/routes/chat.py` (token streaming can be minimal JSON until US4)
- [x] T033 [US1] Persist user/assistant Messages on each turn in `apps/api/app/routes/chat.py` / message repository helpers
- [x] T034 [US1] Add basic chat UI send/receive in `apps/web/src/components/ChatPanel.tsx` and wire to API
- [x] T035 [US1] Ensure T022–T024 pass; fix grounding/refusal gaps

**Checkpoint**: US1 MVP — grounded Q&A + refusals work independently

---

## Phase 4: User Story 2 — Look Up And Act Via Connected Systems (Priority: P1)

**Goal**: Docs/ticket/CRM tools; reads without approval; writes interrupt for human approve/reject

**Independent Test**: Stub tools; read flows complete; writes pause; reject applies nothing; approve applies once

### Tests for User Story 2

- [x] T036 [P] [US2] Contract test for approval resolve API in `apps/api/tests/contract/test_approvals.py`
- [x] T037 [P] [US2] Integration test write interrupt approve/reject in `apps/api/tests/integration/test_write_approval.py`
- [x] T038 [P] [US2] Integration test that writes never apply without approve in `apps/api/tests/integration/test_no_silent_write.py`

### Implementation for User Story 2

- [x] T039 [P] [US2] Add TicketStub and CrmContactStub models + seed data in `apps/api/app/db/models/stubs.py` and `apps/api/app/db/seed.py`
- [x] T040 [P] [US2] Implement PendingApproval model + migration in `apps/api/app/db/models/approval.py`
- [x] T041 [P] [US2] Implement `docs_search` tool in `apps/api/app/tools/docs_search.py`
- [x] T042 [P] [US2] Implement ticket stub tools in `apps/api/app/tools/tickets.py`
- [x] T043 [P] [US2] Implement CRM stub tools in `apps/api/app/tools/crm.py`
- [x] T044 [US2] Add tool + `execute_write` nodes with `interrupt_before` in `apps/api/app/graph/nodes/tools.py` and `apps/api/app/graph/build.py`
- [x] T045 [US2] Implement `POST /v1/threads/{thread_id}/approvals/{approval_id}` in `apps/api/app/routes/approvals.py` (resume graph on decide)
- [x] T046 [US2] Add ApprovalCard UI and `useApprove` hook in `apps/web/src/components/ApprovalCard.tsx` and `apps/web/src/hooks/useApprove.ts`
- [x] T047 [US2] Ensure T036–T038 pass

**Checkpoint**: US2 — tools + approval gate independently verifiable

---

## Phase 5: User Story 4 — Live Step Timeline While The Copilot Works (Priority: P1)

**Goal**: Perplexity-style live vertical timeline (search query, source chips, writing tokens) via graph streaming + SSE

**Independent Test**: Multi-step question shows ordered live steps with query/sources and streamed answer text

### Tests for User Story 4

- [ ] T048 [P] [US4] Contract tests for SSE event shapes per `contracts/sse-events.md` in `apps/api/tests/contract/test_sse_events.py`
- [ ] T049 [P] [US4] Vitest for ChatTimeline/StepNode/SourceChips rendering in `apps/web/tests/ChatTimeline.test.tsx`
- [ ] T050 [P] [US4] Integration test that multi-phase chat emits searching→reading→writing before completion in `apps/api/tests/integration/test_timeline_stream.py`

### Implementation for User Story 4

- [ ] T051 [US4] Map LangGraph `updates`/`messages`/`custom` streams to SSE events in `apps/api/app/graph/streaming.py`
- [ ] T052 [US4] Convert `POST /v1/threads/{thread_id}/chat` to `text/event-stream` in `apps/api/app/routes/chat.py`
- [ ] T053 [US4] Persist completed ProgressStep array on assistant Message (FR-022) in `apps/api/app/db/models/message.py` helpers
- [ ] T054 [P] [US4] Implement `ChatTimeline`, `StepNode`, `SourceChips` in `apps/web/src/components/ChatTimeline.tsx`, `StepNode.tsx`, `SourceChips.tsx`
- [ ] T055 [US4] Implement `useChatStream` SSE consumer in `apps/web/src/hooks/useChatStream.ts`
- [ ] T056 [US4] Wire timeline + streaming bubble into chat page `apps/web/src/app/chat/[threadId]/page.tsx`
- [ ] T057 [US4] Ensure T048–T050 pass; verify first step appears under normal load (SC-006)

**Checkpoint**: US4 — live timeline UX independently demonstrable

---

## Phase 6: User Story 3 — Resume Conversations With Durable Memory (Priority: P2)

**Goal**: Durable thread state across restart, including pending approval

**Independent Test**: Restart API mid-thread / mid-approval; reopen thread_id; history and pending approval restored

### Tests for User Story 3

- [ ] T058 [P] [US3] Integration test resume after process restart with Postgres checkpointer in `apps/api/tests/integration/test_durable_resume.py`
- [ ] T059 [P] [US3] Integration test pending approval survives restart in `apps/api/tests/integration/test_approval_resume.py`

### Implementation for User Story 3

- [ ] T060 [US3] Configure LangGraph AsyncPostgresSaver in `apps/api/app/graph/checkpointer.py` and use in `apps/api/app/graph/build.py`
- [ ] T061 [US3] Ensure chat/approve pass `thread_id` config consistently in `apps/api/app/routes/chat.py` and `apps/api/app/routes/approvals.py`
- [ ] T062 [US3] Reload messages + pending_approval on `GET /v1/threads/{id}` and hydrate UI in `apps/web/src/hooks/useThread.ts`
- [ ] T063 [US3] Ensure T058–T059 pass (SC-004)

**Checkpoint**: US3 — durable memory independently verified

---

## Phase 7: User Story 5 — Authenticated Multi-Tenant Access (Priority: P2)

**Goal**: Enforce auth on all chat routes; harden tenant isolation (no cross-tenant thread access)

**Independent Test**: Unauthenticated denied; Tenant A cannot open Tenant B thread ids

### Tests for User Story 5

- [ ] T064 [P] [US5] Integration test unauthenticated chat/threads return 401 in `apps/api/tests/integration/test_auth_required.py`
- [ ] T065 [P] [US5] Integration test cross-tenant thread access denied in `apps/api/tests/integration/test_tenant_isolation.py`
- [ ] T066 [P] [US5] Vitest/guard test that web redirects unauthenticated users in `apps/web/tests/auth-guard.test.tsx`

### Implementation for User Story 5

- [ ] T067 [US5] Audit all API routes for auth dependency + tenant filters in `apps/api/app/routes/` and `apps/api/app/auth/deps.py`
- [ ] T068 [US5] Ensure RAG retrieval and stub tools filter by `tenant_id` in `apps/api/app/rag/retrieve.py` and `apps/api/app/tools/`
- [ ] T069 [US5] Add web auth guard/middleware for chat routes in `apps/web/src/middleware.ts` (or layout guard)
- [ ] T070 [US5] Ensure T064–T066 pass (SC-005)

**Checkpoint**: US5 — auth + tenancy independently verified

---

## Phase 8: User Story 6 — Evaluate And Trace Copilot Quality (Priority: P3)

**Goal**: Golden eval suite + LangSmith-style inspectable traces

**Independent Test**: Run eval suite; open a trace for a turn; identify retrieval/grade/tool/approval/outcome

### Tests for User Story 6

- [ ] T071 [P] [US6] Eval runner smoke test in `apps/api/tests/integration/test_eval_runner.py`
- [ ] T072 [P] [US6] Contract test for `POST /v1/evals/run` in `apps/api/tests/contract/test_evals_api.py`

### Implementation for User Story 6

- [ ] T073 [P] [US6] Add golden cases JSON under `apps/api/app/evals/cases/` (grounding, refusal, tool)
- [ ] T074 [US6] Implement eval runner in `apps/api/app/evals/run.py`
- [ ] T075 [US6] Implement `POST /v1/evals/run` in `apps/api/app/routes/evals.py`
- [ ] T076 [US6] Configure LangSmith tracing in `apps/api/app/core/langsmith.py` and enable on graph invokes
- [ ] T077 [US6] Document how to view traces and run evals in `specs/001-ops-copilot/quickstart.md` (V7 section verify)
- [ ] T078 [US6] Ensure T071–T072 pass (SC-009/SC-010)

**Checkpoint**: US6 — evals + tracing independently usable

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates and full quickstart validation

- [ ] T079 [P] Add CI workflow lint/type/test for api + web in `.github/workflows/ci.yml` (or equivalent)
- [ ] T080 [P] Harden error SSE/`error` events and failed step UI in `apps/api/app/graph/streaming.py` and `apps/web/src/components/StepNode.tsx`
- [ ] T081 Verify thread status transitions `active` ↔ `pending_approval` across chat/approve paths
- [ ] T082 Run full `specs/001-ops-copilot/quickstart.md` scenarios V1–V7 and fix gaps
- [ ] T083 [P] Code cleanup: remove dead stubs, ensure no secrets committed, align OpenAPI with `contracts/openapi.yaml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS** all user stories
- **US1 (Phase 3)**: After Foundational — MVP
- **US2 (Phase 4)**: After Foundational; naturally builds on US1 graph but independently testable with stubs
- **US4 (Phase 5)**: After US1 chat path exists (needs graph turns to stream); can parallelize UI with US2 backend if SSE contract mocked
- **US3 (Phase 6)**: After US2 preferred (approval resume); can start after US1 if only message durability tested first
- **US5 (Phase 7)**: After Foundational auth; harden after threads/RAG/tools exist (after US1–US2 ideal)
- **US6 (Phase 8)**: After US1–US2 behaviors exist to score
- **Polish (Phase 9)**: After desired stories complete

### User Story Dependencies

| Story | Priority | Depends on | Notes |
|-------|----------|------------|--------|
| US1 Grounded RAG | P1 | Foundational | MVP; no tools required |
| US2 Tools + Approval | P1 | Foundational (+ US1 graph shell ideal) | Independently testable with stubs |
| US4 Live Timeline | P1 | US1 chat/graph | SSE + UI; highest UX impact with US1 |
| US3 Durable Memory | P2 | US1; US2 for approval resume | Postgres checkpointer |
| US5 Auth / Tenancy | P2 | Foundational | Hardening pass over all routes/tools |
| US6 Evals / Traces | P3 | US1 + US2 | Builder-facing |

### Within Each User Story

1. Tests first (fail) → models → services/graph → API → UI → tests pass  
2. Story checkpoint before next priority when sequencing solo

### Parallel Opportunities

- Phase 1: T003, T004, T005, T006, T007, T008 in parallel after T001–T002
- Phase 2: T010–T011 parallel; T018–T019 parallel with API auth work
- US1: T022–T024 parallel; T025–T026, T028–T029 parallel
- US2: T036–T038 parallel; T039–T043 parallel after models
- US4: T048–T050 parallel; T054 parallel with T051–T052
- After Foundational, US1 then branch: one person US2 tools, another US4 UI against SSE mocks

---

## Parallel Example: User Story 1

```bash
# Tests first (parallel):
Task: "T022 unit RAG loop tests in apps/api/tests/unit/test_rag_loop.py"
Task: "T023 integration grounded chat in apps/api/tests/integration/test_grounded_chat.py"
Task: "T024 integration refusal in apps/api/tests/integration/test_refuse_offtopic.py"

# Parallel prep:
Task: "T025 Document models"
Task: "T026 Seed docs/corpus"
Task: "T028 retrieve.py"
Task: "T029 grade.py + rewrite.py"
```

## Parallel Example: User Story 4

```bash
Task: "T048 SSE contract tests"
Task: "T049 ChatTimeline Vitest"
Task: "T050 timeline stream integration test"
# Then implement streaming.py + UI components in parallel once events agreed
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup  
2. Phase 2 Foundational  
3. Phase 3 US1 (grounded RAG + refuse)  
4. **STOP** — validate US1 independent test  
5. Demo MVP

### Suggested Incremental Demos

1. MVP = US1  
2. Add US4 (timeline) for “wow” UX on same grounded path  
3. Add US2 (tools + approval)  
4. Add US3 (durable) + US5 (tenancy harden)  
5. Add US6 (evals/traces)  
6. Polish + quickstart V1–V7

### Parallel Team Strategy

1. Team completes Setup + Foundational together  
2. Dev A: US1 → US3  
3. Dev B: US2 → US5  
4. Dev C: US4 UI/SSE (after US1 stream hooks) → US6  

---

## Notes

- [P] = different files, no incomplete-task dependencies  
- Constitution: do not merge story behavior without automated verification  
- SQLite MemorySaver allowed only in US1 unit tests; Postgres checkpointer required for US3+ demo path  
- Commit after each task or logical group; stop at checkpoints  
- Next command: `/speckit-implement`
