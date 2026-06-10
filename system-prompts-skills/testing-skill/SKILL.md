---
name: testing
description: Use when implementation needs to be validated against a spec, acceptance criteria, or a defined behavior change. This skill turns requirements into a concrete test strategy, adds or updates the right tests, runs appropriate validation when possible, and reports coverage, failures, and remaining gaps in terms of the spec.
---

# Testing

Use this skill to validate behavior against an explicit spec, acceptance criteria, or a well-defined bug report.

This skill is especially effective when paired with a spec-driven workflow. It should translate intended behavior into evidence, not merely exercise code paths.

## Core Rules

- Test against the stated behavior change, not assumptions about the implementation.
- Prefer the smallest test surface that gives credible confidence.
- Add or update automated tests when the project supports them and the change is expected to persist.
- If behavior cannot be tested automatically, provide the narrowest reliable manual verification plan.
- Call out untestable requirements, environment gaps, and missing observability explicitly.

## Inputs To Gather

Before writing or running tests, identify:

- the spec item or acceptance criterion being validated
- the code paths or user flows affected
- the relevant test layers already present in the codebase
- environmental constraints such as services, fixtures, auth, or network dependencies
- any non-goals that must remain unchanged

If the request is underspecified, ask for or infer the intended observable behavior before proceeding.

## Workflow

### 1. Restate the target behavior

Convert the request into testable statements:

- what should happen
- under which conditions
- what should not change
- what evidence would prove success

If multiple acceptance criteria exist, keep them distinct.

### 2. Choose the test surface

Select the lowest-cost layer that credibly validates the behavior:

- unit tests for isolated logic and branching behavior
- integration tests for component boundaries, persistence, or contracts
- end-to-end tests for user workflows and critical system paths
- manual checks only when automation is impractical or unavailable

Do not default to end-to-end coverage when a smaller layer would validate the same behavior more reliably.

### 3. Map coverage to the spec

For each spec item or acceptance criterion, decide:

- existing test already covers it
- existing test should be updated
- new test is required
- manual verification is required
- cannot currently be validated

Prefer a compact mapping such as:

| Spec ID | Behavior | Validation Type | Evidence |
| --- | --- | --- | --- |
| T1 | ... | unit / integration / e2e / manual | file, command, or note |

### 3b. API contract validation (when OpenAPI spec exists)

When the project has an **OpenAPI specification** and the change touches APIs:

- **Validate API definitions and calls against the spec.** Use schema/contract validation so that request and response payloads, status codes, and (where applicable) headers conform to the OpenAPI contract.
- **Prefer Zod** (or an OpenAPI-derived validator) to define or import schemas and assert that:
  - Client requests match the spec’s request body/query/path schemas
  - Server responses match the spec’s response schemas for the given status code
- Run these **contract tests in conjunction with the existing test rig** (unit, integration, e2e). Contract tests should be part of the same pipeline; failures must clearly indicate spec violations or implementation drift.
- Document where contract validation runs (e.g., integration tests, dedicated contract test file) and how to regenerate types/schemas from the OpenAPI spec if the project supports it.

### 4. Implement or update tests

When editing tests:

- follow existing project conventions
- keep fixtures and setup minimal
- test observable outcomes over internal implementation details
- cover the happy path plus the most important edge cases implied by the spec
- avoid brittle assertions unless the output format itself is part of the requirement

If a bug fix is involved, first try to add a test that fails before the fix and passes after it.

### 5. Run the appropriate validation

Run the narrowest command set that meaningfully validates the change.

Prefer:
- targeted test files first
- broader related suites next when risk warrants it
- full suite only when justified by scope, project norms, or user request

If you cannot run tests, say exactly why and provide the command the user or a later agent should run.

### 6. Report results in spec language

Summarize validation by answering:

- which acceptance criteria passed
- which failed
- which were not exercised
- what residual risk remains

Do not stop at “tests pass.” Explain what those tests prove.

## Decision Heuristics

Use lighter validation when:
- the change is localized
- the spec covers a single branch or output
- the module already has strong surrounding coverage

Use broader validation when:
- contracts or schemas changed
- persistence or migrations are involved
- concurrency, caching, or background work is touched
- user-visible workflows changed
- the spec includes regressions across multiple layers

## Manual Verification Guidance

When automation is not practical, provide a short manual plan with:

- setup or prerequisites
- exact actions
- expected result
- failure signal

Manual verification should still map back to acceptance criteria.

## Failure Modes To Avoid

- writing tests for current behavior when the spec intends different behavior
- validating only the happy path when edge cases are part of the requirement
- overfitting tests to implementation details that may legitimately change
- claiming coverage without naming what was actually exercised
- skipping regression checks for adjacent touched behavior
- skipping API contract validation (e.g., Zod against OpenAPI) when an OpenAPI spec exists and the change touches API requests or responses

## Handoff Style

When reporting test work:

- lead with the validated spec items
- name the test layer used
- cite the commands run, if any
- note unvalidated areas and why they remain open

This skill is successful when the final output makes it easy to answer: what behavior was promised, what evidence was gathered, and what uncertainty remains.
