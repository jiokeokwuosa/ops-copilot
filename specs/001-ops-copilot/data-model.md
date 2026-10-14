# Data Model: Internal Support Ops Copilot

**Feature**: `001-ops-copilot` | **Date**: 2026-09-22

Logical entities for Postgres app schema + LangGraph checkpoint state. Field types are logical (implementation may use UUID/JSONB).

---

## Entity Relationship (overview)

```text
Tenant 1──* User
Tenant 1──* Thread *──1 User (owner)
Thread 1──* Message
Message 1──* ProgressStep (embedded JSON on message OK)
Thread 0──1 PendingApproval (at most one)
Tenant 1──* Document / DocumentChunk (knowledge)
Tenant 1──* TicketStub / CrmContactStub (demo data)
EvalCase (static files or table) → EvalRun
```

LangGraph checkpointer tables (managed by LangGraph Postgres saver) store graph channel state keyed by `thread_id` (= Thread.id).

---

## Tenant

| Field | Type | Rules |
|-------|------|--------|
| id | UUID | PK |
| name | string | required, unique |
| created_at | datetime | required |

---

## User

| Field | Type | Rules |
|-------|------|--------|
| id | UUID | PK |
| tenant_id | UUID | FK Tenant, required |
| email | string | required, unique globally or per tenant |
| password_hash | string | required (demo auth) |
| display_name | string | required |
| created_at | datetime | required |

**Validation**: Login must resolve user + tenant; JWT claims include `sub` (user id) and `tenant_id`.

---

## Thread

| Field | Type | Rules |
|-------|------|--------|
| id | UUID | PK; also LangGraph `thread_id` |
| tenant_id | UUID | FK, required; MUST match owner’s tenant |
| user_id | UUID | FK User, required |
| title | string | optional; default from first user message |
| status | enum | `active` \| `pending_approval` \| `archived` |
| created_at | datetime | required |
| updated_at | datetime | required |

**Relationships**: Has many Messages; optional one PendingApproval when `status=pending_approval`.

**Isolation**: All queries filter `tenant_id` (+ ownership as required by API).

---

## Message

| Field | Type | Rules |
|-------|------|--------|
| id | UUID | PK |
| thread_id | UUID | FK Thread |
| role | enum | `user` \| `assistant` \| `system` |
| content | text | assistant may grow during stream; final stored at end |
| steps | JSON | array of ProgressStep snapshots (FR-022) |
| sources | JSON | optional cited sources |
| run_id | string | optional LangSmith / internal run id |
| created_at | datetime | required |

---

## ProgressStep (embedded)

| Field | Type | Rules |
|-------|------|--------|
| id | string | client-stable within turn |
| type | enum | `searching` \| `grading` \| `rewriting` \| `reading` \| `tool` \| `approval` \| `writing` \| `refused` \| `error` |
| label | string | human-readable (“Searching docs”) |
| status | enum | `running` \| `completed` \| `failed` |
| detail | object | optional: `{ query?: string, sources?: SourceRef[], tool_name?: string, error?: string }` |
| started_at | datetime | optional |
| ended_at | datetime | optional |

---

## SourceRef (embedded)

| Field | Type | Rules |
|-------|------|--------|
| id | string | chunk or doc id |
| title | string | display |
| uri | string | path or URL for chips |

---

## PendingApproval

| Field | Type | Rules |
|-------|------|--------|
| id | UUID | PK |
| thread_id | UUID | FK, unique while pending |
| tenant_id | UUID | denormalized for isolation |
| tool_name | string | e.g. `ticket_update` |
| payload | JSON | proposed write fields |
| rationale | string | shown to user |
| status | enum | `pending` \| `approved` \| `rejected` |
| created_at | datetime | required |
| resolved_at | datetime | null until decision |

**Transitions**: `pending` → `approved` | `rejected`. Only one `pending` per thread. Reject/approve resumes LangGraph; writes run only on approve.

---

## Document

| Field | Type | Rules |
|-------|------|--------|
| id | UUID | PK |
| tenant_id | UUID | FK (corpus may be shared global tenant for demo) |
| title | string | required |
| uri | string | file path or logical URI |
| created_at | datetime | required |

## DocumentChunk

| Field | Type | Rules |
|-------|------|--------|
| id | UUID | PK |
| document_id | UUID | FK |
| tenant_id | UUID | for filtered retrieval |
| content | text | required |
| embedding | vector | pgvector; dim per embedding model |
| metadata | JSON | page, section, etc. |

**Retrieval rule**: Always filter by caller `tenant_id` (or demo global corpus tenant explicitly allowed).

---

## TicketStub / CrmContactStub

Minimal stub tables (or JSON fixtures) for tools:

**TicketStub**: id, tenant_id, subject, status, body, updated_at  
**CrmContactStub**: id, tenant_id, name, email, notes[]

Write tools mutate stub rows only after approval.

---

## EvalCase / EvalRun

**EvalCase** (files or table): id, category (`grounding` \| `refusal` \| `tool`), input, expected (assertions), tags  
**EvalRun**: id, started_at, results[] { case_id, pass, score, notes, trace_url }

---

## State transitions

### Thread.status

```text
active → pending_approval  (write tool proposed)
pending_approval → active  (approve or reject)
active → archived          (user archives)
```

### Graph (conceptual)

```text
start → refuse? → end
     → retrieve → grade → rewrite? → retrieve (≤2)
                → read → tools?
                         → propose_write → interrupt → execute_write|skip
                → generate → end
```
