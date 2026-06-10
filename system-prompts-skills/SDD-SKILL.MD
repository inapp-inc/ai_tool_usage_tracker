---
name: spec-driven-development
description: Use when the user wants work executed through a spec-driven development process. This skill coordinates requirement gathering, architecture, coding, and testing skills so implementation follows an explicit spec, changes map back to approved requirements, and validation proves the delivered behavior matches the spec.
---

# Spec-Driven Development

Use this skill as the orchestration layer for spec-driven delivery.

Assume separate skills already exist for:
- requirement gathering
- architecture
- coding
- testing

This skill does not replace them. It decides when to invoke them, enforces stage gates, and keeps the work traceable from request to shipped behavior.

## Core Rules

- Do not start implementation until there is a written spec or a clearly bounded delta to an existing spec.
- Treat ambiguity as a requirements problem first, not a coding problem.
- Keep a visible mapping from spec items to code changes and tests.
- Prefer small spec slices that can be implemented and validated independently.
- If the user asks to skip a stage, comply only after stating the risk briefly.
- **Manual developer operation:** PR creation, PR updates, and merges are performed **manually by the developer**. This guidance defines artifacts, checkpoints, and evidence only.
- **Stage-gated delivery:** Execute the SDD process in parts. After each stage’s deliverables are produced, **stop and wait for user review/approval** before starting the next stage.

## Review Checkpoints (Hard Stops)

The process must pause for approval at these checkpoints:

- **After requirements**: gaps JSON is created/registered, questionnaire filled & finalized, generated docs exist (`Docs/SDD_Gaps_*.md`), and assumptions doc exists if needed (`Docs/SDD_Assumptions.md`).
- **After spec**: FSD (or spec delta) is drafted and ready for review.
- **After design** (when architecture is invoked): design artifacts are produced (including OpenAPI if relevant) and ready for review.
- **After UI prompt**: `Discovery and Design/FigmaMake_UI_Prompt.txt` is generated and ready for review.
- **After each implementation slice**: code changes complete for the slice and ready for review.
- **After validation**: tests/validation results are ready for review.

## Required Outputs

Maintain these artifacts in whatever lightweight form best fits the task:

- a **gaps questionnaire** (Gap Manager Portal + per-project JSON + generated Markdown), when doing full requirement analysis:
  - Portal (global): `system-prompts-skills/requirement-skill/gaps-questionnaire-web/`
  - Registry (global): `system-prompts-skills/requirement-skill/gaps-questionnaire-web/registry.json`
  - Source-of-truth JSON (per project): registered `jsonPath` in the registry
  - Generated Markdown: `SDD_Gaps_Questionnaire.md` and `SDD_Gaps_Answers.md`
- project folder layout: `<projectDir>/{Discovery and Design, Docs, codebase}/`
- a current spec or spec delta (FSD or equivalent)
- an **OpenSpec specification library** (source of truth + design-phase deltas):
  - Source-of-truth specs: `<projectDir>/openspec/specs/**/spec.md`
  - Design-phase change output: `<projectDir>/openspec/changes/<change-id>/{proposal.md,design.md,tasks.md,specs/**/spec.md}`
- when APIs are involved: an **OpenAPI specification** that frontend and backend both refer to
- a short implementation plan tied to spec sections
- acceptance criteria
- test coverage mapped to the acceptance criteria (including API contract validation against the OpenAPI spec when applicable)
- a closeout note listing delivered items, deferred items, and open risks

When SEED Units are used, also maintain:

- SEED Unit template: `system-prompts-skills/seed/SEED-UNIT-TEMPLATE.md`
- Intent review checklist: `system-prompts-skills/seed/INTENT-REVIEW-CHECKLIST.md`
- Evidence requirements: `system-prompts-skills/seed/EVIDENCE-REQUIREMENTS.md`

At the end of delivery, also create a handover deliverable for downstream teams:

- `<projectDir>/Docs/HANDOVER.md` using `system-prompts-skills/handover/HANDOVER-TEMPLATE.md`

## OpenSpec reproducibility (how to create artifacts)

When OpenSpec CLI is available:

- Install: `npm install -g @fission-ai/openspec@latest`
- Initialize (creates `openspec/config.yaml` in the current project): `openspec init`
- Create a new change: `openspec new change <change-id>`

If the CLI is not used, it is still compliant to create the same structure manually:

- `<projectDir>/openspec/config.yaml`
- `<projectDir>/openspec/specs/**/spec.md` (source-of-truth specs)
- `<projectDir>/openspec/changes/<change-id>/{proposal.md,design.md,tasks.md,specs/**/spec.md}` (design-phase output)

## Workflow

### 1. Requirement analysis and establish the spec

If no usable spec exists, invoke the requirement gathering skill first.

**Requirement analysis phase (hard stage gate):**

- **Project root convention:** `<projectDir>` is the folder directly under the repo root (`Presales/<ProjectName>`). The **project name** is `<ProjectName>`.
- **Ensure the Gap Manager Portal is running** (auto-start if needed):
  - Run `node system-prompts-skills/requirement-skill/gaps-questionnaire-web/ensure-portal-running.mjs`
  - Policy: always use port **4317**; if something else is on that port, stop it and start the portal.
- The portal maintains a global **registry** and each project maintains its own gaps in a **per-project JSON** file registered with the portal.
- **Generate the original gaps document as JSON** and auto-register it:
  - Ensure folder layout exists (via `init-project-structure.mjs`)
  - Create `<projectDir>/Discovery and Design/gap-questionnaire.json` if missing (via `init-gap-json.mjs`)
  - Call `POST /api/register-from-path` with `{ jsonPath }` (project name inferred from folder name)
- **STOP execution at this step.** Do not proceed to FSD, architecture, or coding until the questionnaire is completed.
- Completion criterion: **Status is set to Complete in the portal** (confirmation required; portal finalizes and saves per-project JSON `status === "Complete"`).
- After completion, **generate** the Markdown artifacts (`SDD_Gaps_Questionnaire.md` and `SDD_Gaps_Answers.md`) from the JSON (via `generate-gap-md.mjs`) and use them as the primary input to create/update the FSD.
- Before proceeding beyond requirements, if any gaps are not fully addressed (missing answers and/or confidence L, plus open decisions), **generate** an assumptions doc from the JSON:
  - `generate-assumptions-md.mjs --in "<projectDir>/Discovery and Design/gap-questionnaire.json" --projectDir "<projectDir>"`
  - This produces `<projectDir>/Docs/SDD_Assumptions.md` and must explicitly state how each unresolved item is handled (assume/defer/block).

**STOP for review:** Present the requirements deliverables and wait for approval before drafting or changing the FSD.

Once the questionnaire is filled (or explicitly marked as N/A for small tasks), use it as the primary input to create or update the **Functional Specification Document (FSD)**. The FSD should be derived from the answered questionnaire so that requirements are explicit and traceable.

**STOP for review:** Present the drafted/updated FSD and wait for approval before invoking architecture or beginning implementation planning.

A usable spec should define:
- problem statement
- user or system goals
- scope and non-goals
- functional requirements
- constraints
- acceptance criteria

If the request is small, the spec can be brief and the questionnaire may be a short checklist. It still must be explicit enough that another engineer could tell whether the work is done.

### 2. Normalize the implementation target

Before design or coding, rewrite the work into a stable execution target:

- what will change
- what will not change
- what success looks like
- what evidence will prove success

If the user request conflicts with current system behavior, call that out clearly and treat the spec as the source of truth once confirmed.

### 3. Drive architecture and design

Invoke the architecture skill when the spec affects:
- system boundaries
- data contracts
- APIs
- persistence
- concurrency
- security
- performance-sensitive paths
- cross-team or cross-module behavior

**Design obligations (when architecture is invoked):**
- **SOLID principles:** Ensure the design adheres to Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion so the application remains stable and evolvable.
- **Design patterns:** Apply appropriate patterns for clarity, testability, and consistency; document pattern choices in the design or ADRs.
- **Major patterns must be considered explicitly:** Use the patterns library as a checklist and record **chosen vs rejected** patterns (with brief rationale). This includes architecture style, module boundaries, integration/API patterns, data/consistency patterns, reliability/resiliency patterns, and security/multi-tenancy patterns — not only OO patterns.
- **Patterns library (required input):** `system-prompts-skills/architecture-patterns/ARCHITECTURE-AND-DESIGN-PATTERNS.md`
- **OpenAPI spec:** Produce and maintain an **OpenAPI specification** (e.g., `openapi.yaml` or `openapi.json`) that defines all API endpoints, request/response schemas, and auth used by the feature. This spec is the **contract** for both frontend and backend; both sides must refer to it for types, routes, and payloads.

Skip deep architecture work for local or low-risk changes. In those cases, record only the minimal design decision needed to keep implementation aligned. For API-bearing work, still produce or update the OpenAPI spec so frontend and backend stay in sync.

**STOP for review:** Present architecture/design outputs (and OpenAPI if relevant) and wait for approval before proceeding to slicing/implementation.

### 4. Break the spec into execution slices

Turn the spec into a small ordered plan. Each slice should include:
- spec item(s) covered
- intended code area(s)
- validation approach
- dependencies or blockers

Prefer slices that can be reviewed and tested independently.

### 5. Implement against the spec

**Pre-development UI design prompt (required):**

Before any coding begins, create a Figma Make-ready UI prompt (max 4950 characters) based on the project’s features (FSD) and architecture notes, and save it to:

- `<projectDir>/Discovery and Design/FigmaMake_UI_Prompt.txt`

Generate it with:

- `generate-figma-make-prompt.mjs --projectDir "<projectDir>"`

**STOP for review:** Present `FigmaMake_UI_Prompt.txt` and wait for approval before any coding begins.

Invoke the coding skill with the spec slice, not just the original user prompt.

**API and OpenAPI:** When the slice involves frontend-backend integration, both sides must **refer to the OpenAPI spec** for endpoints, request/response shapes, and types. Generate or consume clients and server stubs from the spec where the project supports it. If during coding a change to the API is needed (new field, different status, new endpoint), **edit the OpenAPI spec first**, then implement against the updated spec; do not drift from the spec without updating it.

During implementation:
- keep code changes within the approved scope
- surface any discovered spec gaps immediately
- avoid “helpful” extra behavior unless the spec is updated
- document assumptions when a code decision depends on interpretation

If implementation reveals the spec is wrong or incomplete, pause, update the spec (and OpenAPI if applicable), then continue.

### 6. Validate against acceptance criteria

Invoke the testing skill after each meaningful slice or at minimum before handoff.

Validation should cover:
- acceptance criteria
- regressions in touched behavior
- edge cases implied by the spec
- any explicitly stated non-goals that must remain unchanged
- **API contract:** When an OpenAPI spec exists, validate that API definitions and actual requests/responses conform to the spec. Use schema/contract validation (e.g., **Zod** or an OpenAPI-based validator) in conjunction with the existing test rig so that both behavioral tests and contract tests run; failures should indicate spec violations or implementation drift.

Tests should answer “did we satisfy the spec?” rather than “does the code seem reasonable?”

### 7. Close the loop

End with a concise delivery summary:
- implemented spec items
- evidence of validation
- deviations from the original plan
- deferred follow-ups
- residual risks

If something was intentionally omitted, say whether it is out of scope, blocked, or deferred.

## Decision Heuristics

Use a lightweight path when:
- the task is a small bug fix
- the change is isolated
- requirements are already clear
- acceptance can be proven with a small number of checks

Use a fuller spec cycle when:
- behavior is new or ambiguous
- multiple modules are involved
- user-visible workflows change
- the task has security, reliability, or migration risk
- success depends on more than a single code edit

## Traceability Template

Use this compact structure when helpful:

| Spec ID | Requirement / Acceptance Criterion | Implementation Area | Validation |
| --- | --- | --- | --- |
| S1 | ... | ... | ... |
| S2 | ... | ... | ... |

When APIs are involved, add a column or separate row for **OpenAPI / contract** (e.g., endpoint, request/response schema) so contract tests (e.g., Zod) can be traced to the spec. Keep it lightweight. The point is traceability, not process theater.

## Security Evaluation

Before any delivery is considered complete, validate the product against the OWASP Top 10:

- A01 Broken Access Control
- A02 Cryptographic Failures
- A03 Injection
- A04 Insecure Design
- A05 Security Misconfiguration
- A06 Vulnerable and Outdated Components
- A07 Identification and Authentication Failures
- A08 Software and Data Integrity Failures
- A09 Security Logging and Monitoring Failures
- A10 Server-Side Request Forgery (SSRF)

Add a security checkpoint to the closeout note. Each item should be listed as: passed, not applicable (with reason), or flagged (with the risk and proposed remediation). Do not ship a spec slice that has unresolved OWASP findings without explicit acknowledgment in the spec.

## Configuration Management

All configuration files must be maintained separately from application code:

- Never hardcode environment-specific values (hosts, ports, credentials, feature flags, timeouts) in source code.
- Store configuration in dedicated files or environment variables that are injected at deploy time.
- Document every configuration key: purpose, valid values, and which environments require it.
- When a platform migration occurs, only configuration files should need to change — no application code edits should be required.
- Treat configuration changes as spec changes: update the spec and acceptance criteria to reflect the new values or structure before implementation.

If the spec involves infrastructure, deployment targets, or cross-environment behavior, flag configuration portability as a first-class requirement in the architecture step.

## Failure Modes To Avoid

- coding from an implied spec that was never written down
- allowing architecture work to expand scope without updating the spec
- merging “nice to have” behavior into required behavior
- writing tests only for the happy path when the spec implies edge cases
- declaring success without showing which acceptance criteria were satisfied
- shipping without an OWASP Top 10 review when the product handles user data, authentication, or external input
- embedding host-specific or environment-specific configuration in application code
- changing API behavior or payloads during coding without updating the OpenAPI spec first
- skipping API contract validation (e.g., Zod vs. OpenAPI) when an OpenAPI spec exists and the change touches APIs

## Handoff Style

When reporting progress or completion:
- lead with current spec status
- name the slice being implemented or validated
- note any spec changes before describing code changes
- make open questions explicit and bounded

This skill is successful when the final delivery can be explained as: requested behavior -> specified behavior -> implemented behavior -> verified behavior.
