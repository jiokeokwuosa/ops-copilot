# Feature Specification: Internal Support Ops Copilot

**Feature Branch**: `001-ops-copilot`

**Created**: 2026-09-22

**Status**: Draft

**Input**: User description: "Internal support / ops copilot — best overall. What you learn: Advanced RAG (retrieve, grade, rewrite, refuse off-topic); Tool calling into real systems (docs search, tickets, CRM stubs); interrupt_before / approval for write actions; Durable memory (thread_id + Postgres/SQLite checkpointer); Streaming (steps + tokens); Evals + LangSmith-style tracing; Auth / multi-tenant threads. Amendment: use graph streaming so the UI shows live progress updates (reference: Perplexity-style timeline—Searching, Reading with source chips, Writing answer with streamed text)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Grounded Answers From Internal Knowledge (Priority: P1)

An authenticated support or ops teammate asks a question about internal policies, runbooks, or product behavior. The copilot retrieves relevant knowledge, checks that sources are good enough to answer, rewrites the search if needed, and replies with a grounded answer—or clearly refuses if the question is off-topic or unsupported by available knowledge.

**Why this priority**: Accurate, refuse-when-unsure answers are the core value of an internal support copilot. Without this, tool actions and memory add little trust.

**Independent Test**: Can be fully tested with a seeded knowledge corpus and a set of on-topic / off-topic questions; delivers correct grounded answers and explicit refusals without any ticket or CRM tools enabled.

**Acceptance Scenarios**:

1. **Given** an authenticated user and a knowledge base with relevant documents, **When** they ask an on-topic question covered by those documents, **Then** the copilot returns an answer that cites or clearly reflects retrieved sources and does not invent unsupported facts.
2. **Given** retrieved sources that are weak or irrelevant, **When** the copilot grades them as insufficient, **Then** it rewrites the retrieval query and tries again before answering.
3. **Given** a question outside the supported support/ops domain or with no usable sources after retries, **When** the user asks it, **Then** the copilot refuses to answer with a clear explanation rather than guessing.
4. **Given** a partial or ambiguous on-topic question, **When** the user asks it, **Then** the copilot asks a clarifying question or states what it can and cannot confirm from knowledge.

---

### User Story 2 - Look Up And Act Via Connected Systems (Priority: P1)

The same teammate asks the copilot to find documentation, inspect or draft ticket updates, or look up CRM-style customer context. The copilot calls the appropriate connected tools, uses results in its reply, and never performs a write (create/update) without explicit human approval first.

**Why this priority**: Real ops work needs system access; write-approval is the safety boundary that makes automation acceptable for support teams.

**Independent Test**: Can be tested with stubbed docs, ticket, and CRM tools; read flows complete without approval; write flows pause for approval and only proceed when confirmed.

**Acceptance Scenarios**:

1. **Given** connected docs search is available, **When** the user asks for a procedure or article, **Then** the copilot searches docs and answers using those results.
2. **Given** ticket and CRM stubs are available, **When** the user asks for ticket status or customer context, **Then** the copilot retrieves that information via tools and summarizes it for the user.
3. **Given** the user requests a write action (e.g., update a ticket or add a CRM note), **When** the copilot is about to execute it, **Then** the flow interrupts and presents the proposed write for approval before any change is applied.
4. **Given** a proposed write is shown, **When** the user rejects or cancels approval, **Then** no write occurs and the conversation continues with a clear “not applied” outcome.
5. **Given** a proposed write is shown, **When** the user approves, **Then** the write executes exactly once as described and the copilot confirms the result.

---

### User Story 3 - Resume Conversations With Durable Memory (Priority: P2)

A teammate starts a conversation, leaves, and later returns to the same thread. Prior messages, tool outcomes, and pending approval state (if any) are restored so they can continue without re-explaining context.

**Why this priority**: Support work is interrupt-driven; durable threads make the copilot usable across shifts and browser sessions.

**Independent Test**: Start a thread, send messages (and optionally pause on a write approval), restart the session, resume the same thread id, and verify history and pending state are restored.

**Acceptance Scenarios**:

1. **Given** an existing thread with prior messages, **When** the user reopens that thread, **Then** they see the full conversation history and can continue in context.
2. **Given** a thread interrupted waiting for write approval, **When** the user resumes that thread, **Then** the pending approval is still present and can be approved or rejected.
3. **Given** two different users or tenants, **When** each uses their own threads, **Then** neither can read or resume the other’s threads.

---

### User Story 4 - Live Step Timeline While The Copilot Works (Priority: P1)

While the copilot works, the chat shows a live vertical progress timeline between the user’s question and the final answer—similar to a “search → read → write” assistant UX. Each phase appears as it happens (not only at the end), with useful detail under the step (e.g., the search query being used, sources currently being read as compact chips/pills, then the answer text streaming into a reply bubble). Phases for this product include at least: searching knowledge/docs, grading or rewriting retrieval when needed, reading selected sources, calling tools (tickets/CRM when used), waiting for write approval when needed, and writing the answer.

**Why this priority**: Users need to trust multi-step work; opaque spinners feel broken. A visible timeline of what is happening is a core product requirement for this copilot, not a polish item.

**Independent Test**: Ask a multi-step on-topic question and verify (1) ordered timeline steps appear in real time, (2) search/read steps show query and source details when applicable, (3) answer text streams under a “writing answer” (or equivalent) step, without enabling eval tooling.

**Acceptance Scenarios**:

1. **Given** a user sends a question that requires knowledge retrieval, **When** processing starts, **Then** a “Searching…” (or equivalent) step appears in a vertical timeline before any final answer, including the query or search terms being used when available.
2. **Given** sources have been retrieved, **When** the copilot is consuming them, **Then** a “Reading…” (or equivalent) step appears with visible source identifiers (titles, paths, or URLs) as compact chips/pills under that step.
3. **Given** the copilot is composing the final reply, **When** answer text is produced, **Then** a “Writing answer” (or equivalent) step is visible and the reply text appears progressively in the conversation (not only as a single dump at completion).
4. **Given** grading/rewrite or a tool call occurs, **When** that phase runs, **Then** a distinct timeline step appears for that phase (e.g., “Checking sources”, “Looking up ticket”) so the user can follow the path.
5. **Given** a write approval is required, **When** the flow pauses, **Then** the timeline shows a waiting/approval step and the approval UI is presented without hiding prior steps.
6. **Given** a refusal or error, **When** the flow ends, **Then** the timeline stops in a terminal state with a clear message (not an endless “working” indicator).

---

### User Story 5 - Authenticated Multi-Tenant Access (Priority: P2)

Only signed-in users can use the copilot. Conversations are scoped to a tenant (e.g., team or organization) so threads and data stay isolated.

**Why this priority**: Internal tools that touch tickets and customer data require identity and isolation before broader rollout.

**Independent Test**: Attempt access without auth (denied); create threads under two tenants and verify isolation.

**Acceptance Scenarios**:

1. **Given** an unauthenticated visitor, **When** they try to start or resume a conversation, **Then** access is denied until they authenticate.
2. **Given** an authenticated user in tenant A, **When** they list or open threads, **Then** they only see threads belonging to tenant A (and permitted to them).
3. **Given** a valid session, **When** the user starts a new conversation, **Then** the new thread is associated with their identity and tenant.

---

### User Story 6 - Evaluate And Trace Copilot Quality (Priority: P3)

Operators and builders can run evaluation cases (e.g., groundedness, refusal correctness, tool-choice accuracy) and inspect traces of individual runs (steps, retrievals, tool calls, approvals) to debug and improve behavior.

**Why this priority**: Teaching and operating an advanced copilot requires measurable quality and inspectable runs; ships after core user flows.

**Independent Test**: Run a fixed eval suite against the copilot and open a trace for a single conversation turn; verify scores and step-level visibility without changing product UX for end users.

**Acceptance Scenarios**:

1. **Given** a defined eval set of questions and expected behaviors, **When** the suite is run, **Then** results report pass/fail (or scores) per case for grounding, refusal, and tool behavior.
2. **Given** a completed conversation turn, **When** a builder inspects its trace, **Then** they can see ordered steps including retrieval, grading/rewrite, tool calls, approval gates, and the final outcome.
3. **Given** a failing eval case, **When** its trace is reviewed, **Then** enough detail exists to identify whether failure was retrieval, grading, tool selection, or generation.

---

### Edge Cases

- Knowledge base empty or temporarily unavailable: refuse with a clear “cannot retrieve knowledge” message; do not invent answers.
- Tool timeout or stub error: surface a user-visible failure for that tool and continue with remaining useful context when safe.
- User sends a new message while a write approval is pending: either complete/cancel the pending approval first or clearly supersede it—never apply a stale write silently.
- Extremely long threads: system remains usable; older context may be summarized but durable history remains available to resume.
- Off-topic request that looks like a write (“email the CEO…”): refuse domain-inappropriate actions; never escalate to write approval for disallowed actions.
- Concurrent approvals on the same thread: only one pending write approval at a time; additional writes wait or are rejected until resolved.
- Cross-tenant thread id guessing: access denied; no leakage of existence details beyond authorization failure.
- Client disconnect mid-stream: on reconnect/resume, completed steps and any finalized answer remain visible; in-progress steps do not appear stuck forever without a terminal state.
- Very fast runs: steps still appear in order (even briefly); the UI MUST NOT skip straight to a final answer with no timeline when multi-phase work occurred.
- Step failure (search or tool error): failed step is marked as failed in the timeline with a short reason; later recovery or refusal is still shown.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow authenticated support/ops users to start and continue conversational threads with the copilot.
- **FR-002**: System MUST ground answers in retrieved internal knowledge when answering on-topic factual questions.
- **FR-003**: System MUST grade retrieved material for relevance/sufficiency before answering and MUST rewrite the retrieval attempt when grades are insufficient (within a bounded retry limit).
- **FR-004**: System MUST refuse off-topic or ungroundable questions with an explicit refusal rather than fabricating an answer.
- **FR-005**: System MUST support tool-backed actions for at least: documentation search, ticket operations (stub acceptable), and CRM-style customer lookup/notes (stub acceptable).
- **FR-006**: System MUST distinguish read tools from write tools; read tools MAY run without approval; write tools MUST NOT execute until a human explicitly approves the proposed action.
- **FR-007**: System MUST present the proposed write (target, fields/changes, and rationale) at the approval interrupt so the user can approve or reject.
- **FR-008**: System MUST persist conversation state per thread so users can resume after disconnect or process restart, including messages and any pending approval state.
- **FR-009**: System MUST associate each thread with a stable thread identifier, the owning user, and a tenant for isolation.
- **FR-010**: System MUST stream work progress to the client as an ordered, live step timeline (not only a spinner or a single “thinking” label), updating as each phase begins.
- **FR-011**: System MUST show human-readable step labels for major phases, including at least: searching knowledge/docs, reading sources, writing the answer; and when they occur: grading/rewriting retrieval, tool calls, and waiting for write approval.
- **FR-012**: When searching, the timeline step MUST expose the search query or terms in use (when available) under that step.
- **FR-013**: When reading sources, the timeline step MUST list the sources being used as compact identifiers (title, path, or URL chips/pills).
- **FR-014**: System MUST stream final answer text progressively into the reply under/after the writing step as it is produced.
- **FR-015**: Progress timeline updates MUST arrive while work is in progress (live), not only as a reconstructed summary after completion.
- **FR-016**: System MUST require authentication before creating, listing, or resuming threads.
- **FR-017**: System MUST enforce tenant isolation so users cannot access threads or tool results belonging to another tenant.
- **FR-018**: System MUST provide an evaluation harness that scores representative cases for grounding, refusal correctness, and appropriate tool use.
- **FR-019**: System MUST record inspectable run traces (steps, retrieval/grade/rewrite, tool calls, approval decisions, outcomes) for debugging and quality review.
- **FR-020**: System MUST NOT apply write side effects when the user rejects approval or when the session ends without approval.
- **FR-021**: Users MUST be able to cancel or reject a pending write approval without ending the entire conversation thread.
- **FR-022**: Completed turns MUST retain their step timeline in thread history so users can see how an answer was produced after the fact.

### Key Entities

- **User**: Authenticated internal teammate; has identity and tenant membership.
- **Tenant**: Isolation boundary (team/organization) owning threads and access scope.
- **Thread**: Durable conversation container identified by a stable id; holds message history and run state.
- **Message**: User or assistant turn within a thread; may reference tools, sources, or approvals.
- **Knowledge Source**: Retrievable internal document or chunk used to ground answers.
- **Tool Invocation**: A read or write call to docs, tickets, or CRM (stubs allowed for tickets/CRM).
- **Approval Gate**: Pending human decision required before a write tool executes.
- **Eval Case / Eval Run**: Scenario with expected behavior and recorded score/outcome.
- **Trace**: Ordered record of steps for a single turn or run, used for inspection.
- **Progress Step**: A user-visible phase in the live timeline (label, status, optional detail such as query text or source chips, timestamps optional).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a golden set of at least 20 on-topic questions with known sources, at least 90% of answers are judged grounded (supported by retrieved knowledge, no critical hallucinations).
- **SC-002**: For a golden set of at least 10 off-topic or unanswerable questions, at least 95% result in an explicit refusal (no fabricated procedural or policy answer).
- **SC-003**: 100% of write-tool attempts in test scenarios pause for human approval; 0 writes apply without an approve action.
- **SC-004**: After process restart, users can resume an existing thread and see prior messages within 5 seconds for threads under 100 messages.
- **SC-005**: Cross-tenant access attempts in test scenarios fail 100% of the time (no thread content leakage).
- **SC-006**: On multi-step requests, users see the first timeline progress step within 2 seconds of sending a message (under normal load).
- **SC-007**: For a standard grounded Q&A demo path, at least three distinct timeline phases are visible in order before or during the answer (e.g., searching, reading, writing), with search query and source chips shown when those phases run.
- **SC-008**: In moderated checks with at least 5 internal users, at least 80% can correctly describe what the copilot was doing mid-request (e.g., “searching” vs “writing”) based only on the on-screen timeline—without developer explanation.
- **SC-009**: Eval suite can be run in one command/action and produces a pass/fail or score report covering grounding, refusal, and tool-choice cases.
- **SC-010**: For any sampled failing or successful turn, a reviewer can open a trace and identify retrieval, grade/rewrite, tool, approval, and final outcome steps without reproducing the run.
- **SC-011**: In moderated usability checks with at least 5 internal users, at least 80% successfully complete: ask a grounded question, trigger a read tool, and approve or reject a write—on the first guided attempt.

## Assumptions

- Primary users are internal support and operations teammates, not external customers.
- “Best overall” means a single reference implementation that exercises the full learning path (grounded retrieval with grade/rewrite/refuse, tools, write approval, durable threads, streaming, evals/tracing, auth/tenancy)—not a minimal chatbot.
- Ticket and CRM systems MAY be stubs that simulate realistic read/write behavior; documentation search SHOULD use a real or realistic corpus.
- Write approval is performed by the same authenticated user who requested the action (self-approval interrupt), not a separate four-eyes reviewer—sufficient for an internal learning/ops demo.
- Tenant model is a simple org/team id on each user and thread; fine-grained RBAC beyond auth + tenant isolation is out of scope for v1.
- Off-topic means outside internal support/ops knowledge and connected tool domains (no general web chit-chat, no unrelated creative tasks).
- Retrieval retry/rewrite is bounded (small fixed number of attempts) to avoid unbounded loops.
- Live progress MUST follow a vertical step-timeline pattern (ordered markers with labels and optional detail panels/chips under each step), inspired by common “search → read → write” assistant UIs; exact visual chrome (colors, icons) is left to design/implementation.
- Streaming includes both human-visible step updates and progressive answer text. Preferred approach for emitting live phase updates is graph-style execution streaming (user intent: LangGraph streaming) so each node/phase can publish UI updates as it runs; transport details remain an implementation concern for planning.
- Timeline steps for internal ops map “Searching the web” → searching internal docs/knowledge; “Reading” → reviewing retrieved sources; tool and approval steps are additional phases when used.
- Eval and tracing experiences MAY be builder/operator-facing (CLI, admin view, or exported reports) rather than part of the primary chat UI; the in-chat timeline is end-user facing and separate from builder traces.
- Single-region deployment and standard internal data-handling practices are assumed; formal compliance certifications are out of scope for v1.
- Constitution principles apply: test-first delivery, meaningful coverage (especially approval gates, tenancy, refusal behavior, and streaming timeline behavior), and maintainable design.
