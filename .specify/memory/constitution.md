<!--
Sync Impact Report:
- Version change: 1.1.0 → 1.2.0
- Modified principles: none renamed
- Added sections:
  - Core Principle VI: Industry-Standard Implementation
- Removed sections: none
- Modified sections:
  - Development Workflow review gate: compliance check now covers
    principles I–VI (was I–V)
- Follow-up TODOs: None
-->

# Ops Copilot Constitution

## Core Principles

### I. Code Clarity Over Cleverness

All production code MUST be readable by another engineer without tribal
knowledge. Prefer explicit names, small functions with a single
responsibility, and straightforward control flow over dense abstractions.

- MUST avoid premature generalization; extract shared code only after a
  second concrete use case exists.
- MUST keep modules cohesive: one clear purpose per file or package.
- SHOULD document non-obvious invariants, trade-offs, and "why" comments
  at decision points—not narrate what the code already says.
- Complexity that cannot be simplified MUST be justified in the PR
  description.

**Rationale**: Unclear code is latent defect cost. Clarity is the primary
lever for review speed, onboarding, and long-term maintainability.

### II. Test-First Delivery (NON-NEGOTIABLE)

Behavior changes MUST be specified by failing tests (or equivalent
executable acceptance checks) before implementation lands.

- MUST write or update tests that express the intended behavior first.
- MUST observe the Red → Green → Refactor cycle for new logic.
- MUST NOT merge code that has no automated verification of its
  contract.
- Hotfixes MAY land with a follow-up test within the same change set or
  an immediately linked follow-up PR; untested hotfixes MUST NOT remain
  untested.

**Rationale**: Tests define the contract. Writing them first prevents
over-building and makes regressions detectable by design, not by hope.

### III. Meaningful Test Coverage

Tests MUST protect behavior users and operators depend on—not line counts.

- MUST cover: happy paths, meaningful edge cases, failure modes, and
  boundary conditions for each change.
- MUST include integration or contract tests when touching shared APIs,
  schemas, persistence, or cross-module boundaries.
- MUST NOT rely solely on mocks that assert implementation details;
  prefer testing observable outcomes.
- Flaky tests MUST be fixed or quarantined with an owner; silent flakiness
  is a constitution violation.
- Coverage metrics are a signal, not a goal: gaps in critical paths MUST
  be closed even if overall percentage looks high.

**Rationale**: Low-value tests create false confidence. Meaningful tests
make refactors safe and catch real regressions.

### IV. Maintainable Design

Design MUST optimize for change: small surfaces, clear boundaries, and
minimal coupling.

- MUST prefer simple, reversible designs over speculative architecture
  (YAGNI).
- MUST keep public APIs stable and intentional; breaking changes require
  migration notes and version or compatibility handling.
- MUST avoid deep inheritance and hidden global state; prefer composition
  and explicit dependencies.
- Technical debt MUST be recorded when intentionally accepted, with a
  path to repay it.

**Rationale**: Most engineering cost is modification, not creation.
Designs that are easy to change stay healthy as requirements evolve.

### V. Safe, Reviewable Change

Every change MUST be reviewable, reversible, and sized for confident
merge.

- MUST keep PRs focused on one coherent purpose.
- MUST include enough context in the PR for a reviewer to verify
  constitution compliance (intent, risk, test evidence).
- MUST preserve or improve observability where behavior changes
  (structured logs, clear errors, actionable failure messages).
- MUST NOT bypass CI, lint, typecheck, or required checks without an
  explicit, documented exception.

**Rationale**: Small, reviewable changes reduce merge risk and keep
quality gates enforceable rather than ceremonial.

### VI. Industry-Standard Implementation

Implementation work MUST follow established industry standards and the
idioms of the chosen stack whenever a suitable standard exists.

- MUST prefer official language, framework, and protocol standards over
  one-off custom mechanisms. Examples already in this project: HTTP APIs,
  JWT for auth tokens, Server-Sent Events for streaming, SQL with
  versioned migrations for persistence, and the lint, format, and type
  tools of the stack.
- MUST follow the conventions of the chosen frameworks (Next.js and React
  on the web; FastAPI and Python on the API) instead of inventing a
  parallel way to do the same job.
- MUST prefer a mature, widely used library that implements a standard
  over a hand-rolled equivalent. New dependencies still MUST be justified
  under Quality Constraints.
- A custom approach MAY be used only when no suitable standard exists, or
  when following the standard would clearly harm safety, clarity, or an
  explicit product constraint. That exception MUST be documented in the
  PR or design notes, including which standard was considered and why it
  was not used.
- MUST NOT introduce a novel protocol, auth scheme, data format, or build
  tool when a standard already used in this repo covers the need.

**Rationale**: Standards make the code predictable, reviewable, and
teachable. Custom mechanisms are reserved for gaps a standard does not
cover.

## Quality Constraints

All contributions MUST meet these baseline quality bars:

- Style and static analysis: project lint and format rules MUST pass.
- Types: where the stack supports static typing, new code MUST be typed
  and MUST NOT introduce unjustified `any`/unchecked escapes.
- Error handling: failures MUST surface with actionable messages; silent
  swallows are forbidden.
- Dependencies: new third-party libraries MUST be justified (size,
  license, maintenance, necessity); prefer the existing stack.
- Secrets: credentials and secrets MUST NEVER be committed; use approved
  secret management.

## Development Workflow

### Branching model

- Integration branch: `develop` is the main working branch. Feature and
  task work MUST NOT land directly on `main` by default; day-to-day
  integration happens on `develop`.
- Task branches: each individual task MUST be done on its own branch
  branched from an up-to-date `develop` (e.g. `task/<short-name>` or the
  Spec Kit feature branch convention already in use).
- Sync before branch: before creating a new task branch, the agent MUST
  update local `develop` from the remote (`git fetch` / `git pull` on
  `develop`, or equivalent) so work starts from the latest shared state.
- Scope: one task per branch whenever practical; do not mix unrelated
  tasks on the same branch.

### Spec-driven delivery

- Spec-driven work: features SHOULD follow Spec Kit specify → plan →
  tasks → implement unless the change is a trivial fix.
- CI gates: merge MUST require green automated checks for lint, types,
  and tests applicable to the change.
- Refactors: pure refactors MUST keep behavior covered by existing tests
  and MUST NOT mix large renames with unrelated feature work.

### Task completion, review, and PRs

- After finishing a task, the agent MUST ask the user whether to open a
  pull request. Do not open a PR unless the user confirms.
- Before opening any PR, the agent MUST perform a code review of the
  change set first (correctness, constitution compliance, tests, secrets,
  and clarity). Findings that block merge MUST be fixed before the PR is
  created; non-blocking notes MAY be listed in the PR body.
- When a PR is opened, it MUST target `develop` unless the user
  explicitly requests another base.
- Reviews: at least one reviewer MUST confirm principles I–VI for
  behavior-changing PRs (human and/or agent pre-PR review as above).

### Teaching feedback (NON-NEGOTIABLE for agent sessions)

When a task is done, the agent MUST give feedback that teaches, not only
summarizes:

- MUST explain what changed in plain language aimed at a beginner
  programmer—define jargon the first time it appears.
- MUST show short, relevant code snippets for the important parts of the
  change and walk through what each snippet does and why it exists.
- MUST connect the change to the larger picture (which principle or
  workflow step it supports) when helpful.
- SHOULD invite questions so learning continues as we proceed.

**Rationale**: Branch hygiene and pre-PR review keep `develop` stable.
Teaching feedback turns each task into a learning step, not only a
delivery step.

## Governance

This constitution supersedes informal team habits and conflicting ad-hoc
guidance. When practices disagree, this document wins until amended.

**Amendments**:
1. Propose the change with rationale, impact on existing principles, and
   migration notes if guidance becomes stricter.
2. Record the amendment in `.specify/memory/constitution.md` with an
   updated version and `Last Amended` date.
3. Communicate the change to active contributors before enforcing new
   MUST-level rules on in-flight work.

**Versioning**:
- MAJOR: remove or redefine a principle in a backward-incompatible way.
- MINOR: add a principle/section or materially expand guidance.
- PATCH: clarifications, wording, and non-semantic refinements.

**Compliance**:
- PRs and reviews MUST verify applicable principle compliance.
- Exceptions MUST be explicit, time-bounded, and documented in the PR.
- Periodic review: revisit this constitution when process friction or
  repeated defects indicate guidance gaps.

**Version**: 1.2.0 | **Ratified**: 2026-09-22 | **Last Amended**: 2026-09-25
