# SSE Event Contract: Chat Timeline Stream

**Feature**: `001-ops-copilot`  
**Transport**: `POST /v1/threads/{thread_id}/chat` → `Content-Type: text/event-stream`  
**Auth**: Bearer JWT required; thread must belong to caller tenant.

Each SSE message uses `event:` + `data:` (JSON). Clients MUST ignore unknown event types.

---

## Client → Server (request body)

```json
{
  "message": "How do I reset a user’s MFA?"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| message | string | yes | Non-empty user text |

---

## Server → Client events

### `step`

Emitted when a timeline phase starts or changes status.

```json
{
  "step_id": "s1",
  "type": "searching",
  "label": "Searching docs",
  "status": "running"
}
```

`type`: `searching` | `grading` | `rewriting` | `reading` | `tool` | `approval` | `writing` | `refused` | `error`  
`status`: `running` | `completed` | `failed`

### `step_detail`

Enrichment for an existing step (query, sources, tool name).

```json
{
  "step_id": "s1",
  "detail": {
    "query": "reset MFA user support runbook",
    "sources": [
      { "id": "c1", "title": "MFA Reset", "uri": "docs/corpus/mfa-reset.md" }
    ],
    "tool_name": null,
    "error": null
  }
}
```

### `token`

Incremental assistant answer text.

```json
{
  "step_id": "s_write",
  "delta": "To reset MFA, open the admin "
}
```

### `approval_required`

Stream may pause; client shows approval UI. Further tokens wait until resume API.

```json
{
  "approval_id": "uuid",
  "tool_name": "ticket_update",
  "payload": { "ticket_id": "T-100", "status": "waiting_on_customer", "note": "..." },
  "rationale": "Update ticket status per your request"
}
```

### `message_completed`

Final assistant message snapshot after turn finishes (or refuses).

```json
{
  "message_id": "uuid",
  "content": "Full final text...",
  "steps": [],
  "sources": []
}
```

### `done`

```json
{ "thread_id": "uuid", "status": "active" }
```

`status` may be `pending_approval` if waiting.

### `error`

```json
{ "code": "tool_timeout", "message": "Ticket service timed out", "step_id": "s3" }
```

---

## Ordering guarantees

1. `step` (`running`) before related `step_detail` / `token` for that phase.
2. At least one non-writing `step` before `token` on multi-phase grounded Q&A when retrieval runs.
3. `approval_required` before any write side effect.
4. Terminal: `message_completed` then `done`, or `error` then `done`.

---

## Mapping to UI (screenshot-style)

| Event | UI |
|-------|-----|
| `step` type=searching | Timeline node “Searching…” |
| `step_detail.query` | Query box under search node |
| `step` type=reading + sources | “Reading” + source chips |
| `step` type=writing + `token` | “Writing answer” + streaming bubble |
| `approval_required` | Approval card + approval timeline node |
