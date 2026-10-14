# Implementation Plan: Internal Support Ops Copilot

**Branch**: `001-ops-copilot` | **Date**: 2026-09-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-ops-copilot/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Build an authenticated, multi-tenant internal support/ops copilot that answers from internal knowledge with advanced RAG (retrieve → grade → rewrite → refuse), calls docs/ticket/CRM tools with human approval before writes, persists durable threads, and streams a Perplexity-style live step timeline plus answer tokens to the UI.

**Technical approach**: Next.js (App Router) + Tailwind + TypeScript + TanStack Query chat frontend; FastAPI backend hosting a LangGraph agent (LangChain tools/retrievers) with Postgres (`pgvector` + LangGraph Postgres checkpointer) for knowledge, app data, and durable graph state; SSE for live timeline/token streaming; LangSmith for traces; pytest + Vitest for contract/behavior tests.

## Technical Context

**Language/Version**: TypeScript 5.x (frontend), Python 3.12 (backend)

**Primary Dependencies**:
- Frontend: Next.js 15 (App Router), React 19, Tailwind CSS 4, TanStack Query v5, Zod
- Backend: FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2 + Alembic, LangChain, LangGraph
- AI/ops: OpenAI-compatible chat + embeddings (configurable), LangSmith tracing
- Auth: JWT issued by FastAPI; Next.js session cookie bridge (httpOnly)

**Storage**: PostgreSQL 16 with `pgvector` (documents/embeddings + app tables); LangGraph AsyncPostgresSaver checkpointer for thread/run state

**Testing**: pytest + httpx (API/graph/contract), Vitest + Testing Library (UI), Playwright smoke for chat timeline (optional P3)

**Target Platform**: Local Docker Compose (web + API + Postgres); Linux-friendly deploy later

**Project Type**: Web application (frontend + backend monorepo)

**Performance Goals**: First timeline step visible &lt; 2s under normal local load; resume thread history &lt; 5s for &lt;100 messages; streaming tokens without multi-second gaps under normal load

**Constraints**: Write tools blocked until explicit approve; tenant isolation on all thread/tool access; no secrets in repo; typed TS + typed Python; test-first for behavior changes

**Scale/Scope**: Learning/reference internal demo — single region, tens of concurrent users, seeded docs corpus, stub ticket/CRM systems; not multi-region production

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | How plan satisfies |
|------|--------|--------------------|
| I. Code Clarity | PASS | Monorepo with clear `apps/web`, `apps/api` boundaries; graph nodes named by phase; no premature shared libs until second use |
| II. Test-First | PASS | Contract tests for SSE event shapes and approval gates written before graph/UI polish; pytest for RAG/refuse/tools; Vitest for timeline rendering |
| III. Meaningful Coverage | PASS | Golden evals for grounding/refusal; integration tests for interrupt/resume and tenant isolation; timeline streaming contract tests |
| IV. Maintainable Design | PASS | LangGraph nodes = phases; tools as thin adapters; stubs isolated; YAGNI on RBAC beyond tenant |
| V. Safe Change | PASS | Focused PRs; CI lint/type/test; structured logs + LangSmith traces |
| Quality Constraints | PASS | ruff/mypy or pyright, eslint/tsc, prettier; `.env.example` only; no committed secrets |

**Post-design re-check**: PASS — contracts and data model keep approval, tenancy, and streaming observable and testable without unjustified complexity. Complexity Tracking left empty (no constitution violations).

## Project Structure

### Documentation (this feature)

```text
specs/001-ops-copilot/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
apps/
├── web/                          # Next.js App Router + Tailwind + TanStack Query
│   ├── src/
│   │   ├── app/                  # routes: login, chat/[threadId], settings
│   │   ├── components/           # ChatTimeline, StepNode, SourceChips, ApprovalCard, MessageBubble
│   │   ├── hooks/                # useThread, useChatStream, useApprove
│   │   ├── lib/                  # api client, auth session helpers, zod schemas
│   │   └── types/
│   ├── tests/
│   ├── package.json
│   └── tailwind.config.ts
│
└── api/                          # FastAPI + LangGraph
    ├── app/
    │   ├── main.py
    │   ├── api/                  # auth, threads, chat stream, approvals, evals
    │   ├── auth/                 # JWT, tenant context
    │   ├── db/                   # SQLAlchemy models, session, alembic
    │   ├── graph/                # LangGraph definition, nodes, state, streaming
    │   ├── rag/                  # ingest, retrieve, grade, rewrite
    │   ├── tools/                # docs_search, tickets_stub, crm_stub
    │   ├── evals/                # golden cases + runner
    │   └── core/                 # settings, logging, langsmith
    ├── tests/
    │   ├── contract/
    │   ├── integration/
    │   └── unit/
    ├── alembic/
    ├── pyproject.toml
    └── Dockerfile

packages/
└── shared-schemas/               # Optional OpenAPI-generated TS types (later)

.env.example                     # committed template; real secrets live in root .env

infra/
└── docker-compose.yml            # postgres (pgvector), api, web

docs/
└── corpus/                       # Seed internal markdown docs for RAG
```

**Structure Decision**: Web + API monorepo under `apps/` with Docker Compose for Postgres. Shared OpenAPI types may be generated later; start with hand-synced Zod/Pydantic mirrors of `contracts/`.

## Complexity Tracking

> No constitution violations requiring justification.
