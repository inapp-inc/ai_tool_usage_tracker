---
name: testing
description: Use when implementation needs to be validated against a spec, acceptance criteria, or a defined behavior change. Turns requirements into a concrete test strategy, adds or updates tests, runs validation when possible, and reports coverage and gaps in terms of the spec. Invoked by spec-driven-development after each meaningful slice or before handoff.
---

# Testing

Use this skill to **validate behavior against an explicit spec**, acceptance criteria, or a well-defined bug report. It is invoked by the spec-driven-development skill after each meaningful slice or at minimum before handoff. It should translate intended behavior into evidence, not merely exercise code paths.

## Core Rules

- Test against the **stated behavior change**, not assumptions about the implementation.
- Prefer the smallest test surface that gives credible confidence.
- Add or update automated tests when the project supports them and the change is expected to persist.
- If behavior cannot be tested automatically, provide the narrowest reliable manual verification plan.
- Call out untestable requirements, environment gaps, and missing observability explicitly.
- **NFRs and performance requirements are first-class test targets:** non-functional requirements (security, reliability, performance, accessibility, etc.) must be explicitly evaluated and reported, not implied.
- Prefer mapping validation evidence to **OpenSpec requirements/scenarios** (from `<projectDir>/openspec/specs/**/spec.md`) so coverage stays durable across refactors.
- **Hard enforcement (manual PR operations):** This skill MUST NOT create, open, update, comment on, approve, or merge pull requests. Any PR/merge action is **manual developer work**; this skill only produces validation evidence and test changes.

## Inputs To Gather

Before writing or running tests:

- the spec item or acceptance criterion being validated
- the **non-functional requirements (NFRs)** and **performance requirements** that apply to the slice or system
- the code paths or user flows affected
- the relevant test layers already present in the codebase
- environmental constraints (services, fixtures, auth, network)
- any non-goals that must remain unchanged

If the request is underspecified, ask for or infer the intended observable behavior before proceeding.

## Workflow

### 1. Restate the target behavior

Convert the request into testable statements: what should happen, under which conditions, what should not change, what evidence would prove success. Keep acceptance criteria distinct.

### 1a. Extract and restate NFRs / performance requirements

Treat NFRs as explicit requirements with their own IDs (or reference the spec section). Convert each NFR into a measurable or observable check.

Common NFR categories to look for (from FSD, gaps answers, architecture notes, ADRs):

- **Performance**: latency budgets (p50/p95/p99), throughput, concurrency, payload sizes, cold start, UI responsiveness.
- **Reliability**: retries/timeouts behavior, idempotency, error handling guarantees, recovery behavior, data integrity.
- **Security & privacy**: authn/authz, tenant isolation, input validation, secrets handling, OWASP concerns, PII handling.
- **Scalability & capacity**: expected growth, rate limits, backpressure.
- **Availability/DR**: SLOs, RTO/RPO (if applicable), degradation modes.
- **Accessibility & UX**: WCAG targets, keyboard navigation, screen reader semantics (when UI changes).
- **Observability**: logs/metrics/traces, correlation IDs, alerting signals for critical paths.
- **Compatibility**: API contract/versioning, browser support, backward compatibility expectations.

### 2. Choose the test surface

Select the lowest-cost layer that credibly validates the behavior:

- **Unit tests** — isolated logic and branching
- **Integration tests** — component boundaries, persistence, contracts
- **End-to-end tests** — user workflows and critical system paths
- **Manual checks** — only when automation is impractical

Do not default to end-to-end when a smaller layer would validate the same behavior more reliably.

### 3. Map coverage to the spec

For each spec item or acceptance criterion: existing test covers it / should be updated / new test required / manual verification / cannot currently be validated. Use a compact mapping:

| Spec ID | Behavior | Validation Type | Evidence |
| --- | --- | --- | --- |
| T1 | ... | unit / integration / e2e / manual | file, command, or note |

#### Include NFRs and performance requirements in the mapping

Extend the same mapping to include NFR/performance requirements so reviewers can see what was evaluated and how:

| Req ID | Requirement (NFR / perf / security / reliability) | Validation Type | Evidence |
| --- | --- | --- | --- |
| NFR-1 | p95 latency <= X ms for endpoint Y | perf (load) / integration / manual | report, script, command |

### 4. API contract validation (when OpenAPI spec exists)

When the project has an **OpenAPI specification** and the change touches APIs:

- Validate API definitions and calls against the spec. Use schema/contract validation so request/response payloads, status codes, and (where applicable) headers conform to the OpenAPI contract.
- Prefer **Zod** (or an OpenAPI-derived validator) to assert: client requests match the spec’s request body/query/path schemas; server responses match the spec’s response schemas for the given status code.
- Run **contract tests** with the existing test rig (unit, integration, e2e). Failures must clearly indicate spec violations or implementation drift.
- Document where contract validation runs and how to regenerate types/schemas from the OpenAPI spec if the project supports it.

### 4a. Performance evaluation (when performance requirements exist or risk is non-trivial)

Performance is evaluated against **budgets**, not vibes. If the spec provides budgets, test them; if it does not, report the gap and propose minimal budgets aligned with the user flow.

Minimum performance validation menu (choose the smallest credible set):

- **Micro-level**: targeted profiling/benchmark of hot functions (CPU/memory) when code changes affect loops, serialization, parsing, rendering, or DB query shaping.
- **Endpoint-level**: measure latency and error rate for specific endpoints under representative concurrency and payload sizes.
- **Flow-level**: measure user-perceived responsiveness for critical UI flows (time to interactive, key interactions).

Always report:

- test environment assumptions (machine, dataset size, network)
- traffic model (concurrency, RPS, payload)
- metrics captured (p50/p95/p99, throughput, error rate, resource usage)
- whether results meet the stated budgets (or which are missing)

### 5. Implement or update tests

- Follow existing project conventions; keep fixtures and setup minimal.
- Test observable outcomes over internal implementation details.
- Cover happy path plus the most important edge cases implied by the spec.
- For bug fixes, add a test that fails before the fix and passes after it.

### 6. Run the appropriate validation

Run the narrowest command set that meaningfully validates the change: targeted test files first, broader suites when risk warrants, full suite when justified by scope or user request. If you cannot run tests, state why and give the command the user or a later agent should run.

### 7. Report results in spec language

Summarize: which acceptance criteria passed, which failed, which were not exercised, what residual risk remains. Do not stop at “tests pass” — explain what those tests prove.

Include an explicit section for:

- **Functional coverage** (acceptance criteria)
- **NFR coverage** (security, reliability, accessibility, observability, etc.)
- **Performance coverage** (budgets, evidence, gaps)

## Decision Heuristics

- **Lighter validation:** localized change, single branch or output in spec, strong surrounding coverage.
- **Broader validation:** contracts or schemas changed, persistence or migrations, concurrency/caching/background work, user-visible workflows, regressions across multiple layers.

## Manual Verification

When automation is not practical, provide a short manual plan: setup/prerequisites, exact actions, expected result, failure signal. Manual verification should still map back to acceptance criteria.

## Failure Modes To Avoid

- Writing tests for current behavior when the spec intends different behavior
- Validating only the happy path when edge cases are part of the requirement
- Overfitting tests to implementation details that may legitimately change
- Claiming coverage without naming what was actually exercised
- Skipping regression checks for adjacent touched behavior
- Skipping API contract validation when an OpenAPI spec exists and the change touches API requests or responses

## Handoff Style

Lead with the validated spec items; name the test layer used; cite the commands run; note unvalidated areas and why they remain open. This skill succeeds when the output answers: what behavior was promised, what evidence was gathered, and what uncertainty remains.
