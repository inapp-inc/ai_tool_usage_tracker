---
name: spec-driven-development
description: Use when the user wants work executed through a spec-driven development process. This skill coordinates requirement gathering, architecture, coding, and testing skills so implementation follows an explicit spec, changes map back to approved requirements, and validation proves the delivered behavior matches the spec.
---

# Spec-Driven Development

Use this skill as the **orchestration layer** for spec-driven delivery. It is the **master** that drives all other skills.

Assume separate skills exist for: **requirements**, **architecture**, **coding**, **testing**. This skill does not replace them. It decides when to invoke them, enforces stage gates, and keeps the work traceable from request to shipped behavior.

## Core Rules

- Do not start implementation until there is a written spec or a clearly bounded delta to an existing spec.
- Treat ambiguity as a requirements problem first, not a coding problem.
- Keep a visible mapping from spec items to code changes and tests.
- Prefer small spec slices that can be implemented and validated independently.
- If the user asks to skip a stage, comply only after stating the risk briefly.
- **PR operations are manual:** Creating PRs, updating PR descriptions, requesting reviews, and merging are performed **manually by the developer**. This skill defines artifacts, review checkpoints, and required evidence only.
- **Stage-gated delivery:** Execute the SDD process in parts. After each stage’s deliverables are produced, **stop and wait for user review/approval** before starting the next stage.

## Review Checkpoints (Hard Stops)

The process must pause for approval at these checkpoints:

- **After requirements**: gaps JSON is created/registered, questionnaire filled & finalized, generated docs exist (`Docs/SDD_Gaps_*.md`), and assumptions doc exists if needed (`Docs/SDD_Assumptions.md`).
- **After spec**: FSD (or spec delta) is drafted and ready for review.
- **After design** (when architecture is invoked): design artifacts are produced (including OpenAPI if relevant) and ready for review.
- **After UI prompt**: `Discovery and Design/FigmaMake_UI_Prompt.txt` is generated and ready for review.
- **After each implementation slice**: code changes complete for the slice and ready for review.
- **After validation**: tests/validation results are ready for review.
- **After SEED planning (when SEED is used)**: SEED Units are defined with explicit acceptance criteria, constraints, evidence, and rollback, and each unit is tied to an OpenSpec change folder.
- **After handover**: a handover deliverable exists at `<projectDir>/Docs/HANDOVER.md` for downstream teams.

## Required Outputs

Maintain these artifacts in whatever lightweight form best fits the task:

- a **gaps questionnaire** (Gap Manager Portal + per-project JSON + generated Markdown) when doing full requirement analysis:
  - Portal (global): `system-prompts-skills/requirement-skill/gaps-questionnaire-web/`
  - Registry (global): `system-prompts-skills/requirement-skill/gaps-questionnaire-web/registry.json`
  - Source-of-truth JSON (per project): registered `jsonPath` in the registry
  - Generated outputs: `SDD_Gaps_Questionnaire.md` + `SDD_Gaps_Answers.md` (generated from JSON)
- project folder layout: `<projectDir>/{Discovery and Design, Docs, codebase}/`
- a current spec or spec delta (FSD or equivalent) — use `system-prompts-skills/requirement-skill/fsd-template.md` for structure
- an **OpenSpec specification library** (source of truth + design-phase deltas):
  - Source-of-truth specs: `<projectDir>/openspec/specs/**/spec.md`
  - Design-phase change output: `<projectDir>/openspec/changes/<change-id>/{proposal.md,design.md,tasks.md,specs/**/spec.md}`
- when APIs are involved: an **OpenAPI specification** that frontend and backend both refer to
- a short implementation plan tied to spec sections
- acceptance criteria
- test coverage mapped to the acceptance criteria (including API contract validation against the OpenAPI spec when applicable)
- a closeout note listing delivered items, deferred items, and open risks
- when SEED is used: SEED Unit blocks and evidence expectations:
  - Template: `system-prompts-skills/seed/SEED-UNIT-TEMPLATE.md`
  - Intent review checklist: `system-prompts-skills/seed/INTENT-REVIEW-CHECKLIST.md`
  - Evidence requirements: `system-prompts-skills/seed/EVIDENCE-REQUIREMENTS.md`
- handover deliverable:
  - `<projectDir>/Docs/HANDOVER.md` using `system-prompts-skills/handover/HANDOVER-TEMPLATE.md`

## Workflow

### 1. Requirement analysis and establish the spec

If no usable spec exists, **invoke the requirements skill** first.

**Requirement analysis phase (hard stage gate):**

- **Project root convention:** `<projectDir>` is the folder directly under the repo root (`Presales/<ProjectName>`). The **project name** is `<ProjectName>`.
- **Ensure the Gap Manager Portal is running** (auto-start if needed):
  - Run `node system-prompts-skills/requirement-skill/gaps-questionnaire-web/ensure-portal-running.mjs`
  - Policy: always use port **4317**; if something else is on that port, stop it and start the portal.
- **Create the per-project gaps JSON** (JSON-first) and **auto-register** it with the portal:
  - Ensure folder layout exists (via `init-project-structure.mjs`)
  - Create `<projectDir>/Discovery and Design/gap-questionnaire.json` if missing (via `init-gap-json.mjs`)
  - Call `POST /api/register-from-path` with `{ jsonPath }` (project name inferred from `<projectDir>` folder name)
- **Stop execution here** until the questionnaire is completed by stakeholders.
- Completion criterion: **Status is set to Complete in the portal** (confirmation required; portal finalizes and saves per-project JSON `status === "Complete"`).
- After completion, **generate** the Markdown artifacts (`SDD_Gaps_Questionnaire.md` and `SDD_Gaps_Answers.md`) from the JSON (and optionally `POST /api/register-artifact`) and use them as reviewable inputs.
- Before proceeding beyond requirements, if any gaps are not fully addressed (missing answers and/or confidence L, plus open decisions), **generate** an assumptions doc from the JSON:
  - `generate-assumptions-md.mjs --in "<projectDir>/Discovery and Design/gap-questionnaire.json" --projectDir "<projectDir>"`
  - This produces `<projectDir>/Docs/SDD_Assumptions.md` and must explicitly state how each unresolved item is handled (assume/defer/block).

**STOP for review:** Present the requirements deliverables and wait for approval before drafting or changing the FSD.

Once the questionnaire is filled (or explicitly marked as N/A for small tasks), use it as the primary input to create or update the **Functional Specification Document (FSD)**. Use `system-prompts-skills/requirement-skill/fsd-template.md` for FSD structure. The FSD should be derived from the answered questionnaire so that requirements are explicit and traceable.

**STOP for review:** Present the drafted/updated FSD and wait for approval before invoking architecture or beginning implementation planning.

A usable spec must define: problem statement, user or system goals, scope and non-goals, functional requirements, constraints, acceptance criteria.

### 1a. Establish or update OpenSpec specs (source of truth)

After the FSD is drafted (or when a usable spec already exists), ensure the project has OpenSpec specs that capture behavior intent in a stable, agent-readable format:

- Create/update `<projectDir>/openspec/config.yaml` (project context + OpenSpec generation rules).
- Create/update behavior specs under `<projectDir>/openspec/specs/` using OpenSpec format:
  - `# <domain> Specification`
  - `## Purpose`
  - `## Requirements`
  - `### Requirement: ...` with RFC 2119 keywords (MUST/SHALL/SHOULD/MAY)
  - `#### Scenario: ...` with Given/When/Then bullets

**Reproducible creation (CLI or manual):**

- **CLI (recommended when available):**
  - Install: `npm install -g @fission-ai/openspec@latest`
  - Initialize (creates `openspec/config.yaml` in the current project): `openspec init`
  - Create a design-phase change folder: `openspec new change <change-id>`
- **Manual fallback (always acceptable in this repo):**
  - Create `<projectDir>/openspec/config.yaml`
  - Create `<projectDir>/openspec/specs/<domain>/spec.md`
  - Create `<projectDir>/openspec/changes/<change-id>/{proposal.md,design.md,tasks.md,specs/**/spec.md}`

### 2. Normalize the implementation target

Before design or coding, rewrite the work into a stable execution target: what will change, what will not change, what success looks like, what evidence will prove success. If the user request conflicts with current system behavior, call that out and treat the spec as the source of truth once confirmed.

### 2a. Convert the work into SEED Units (AI-executable slices)

When the work is non-trivial (multiple boundaries, multiple concerns, higher risk, or multiple PRs), use SEED Units:

- Invoke the **seed-unit** skill to break work into PR-sized units.
- For each SEED Unit, require: goal, scope, constraints (perf/security/BC/cost), acceptance criteria, evidence required, risks & rollback, and an OpenSpec spec link.
- Tie each unit to an OpenSpec change folder under `<projectDir>/openspec/changes/<seed-id>/`.

Use these supporting artifacts:

- Template: `system-prompts-skills/seed/SEED-UNIT-TEMPLATE.md`
- Intent review checklist: `system-prompts-skills/seed/INTENT-REVIEW-CHECKLIST.md`
- Evidence requirements: `system-prompts-skills/seed/EVIDENCE-REQUIREMENTS.md`

**STOP for review:** Present the SEED Units (and their OpenSpec change folders) before any implementation begins.

### 3. Drive architecture and design

**Invoke the architecture skill** when the spec affects: system boundaries, data contracts, APIs, persistence, concurrency, security, performance-sensitive paths, cross-team or cross-module behavior.

**Design obligations (when architecture is invoked):**
- **SOLID principles** and appropriate design patterns; document choices in design or ADRs.
- **Major patterns must be considered explicitly:** Use the patterns library as a checklist and record **chosen vs rejected** patterns (with brief rationale). This includes architecture style, module boundaries, integration/API patterns, data/consistency patterns, reliability/resiliency patterns, and security/multi-tenancy patterns — not only OO patterns.
- **Patterns library (required input):** `system-prompts-skills/architecture-patterns/ARCHITECTURE-AND-DESIGN-PATTERNS.md`
- **OpenAPI spec:** Produce and maintain an OpenAPI specification (`openapi.yaml` or `openapi.json`) as the **contract** for frontend and backend.

Skip deep architecture for local or low-risk changes; still produce or update the OpenAPI spec for API-bearing work. Architecture ADRs and governance live in `system-prompts-skills/architecture-adr/`.

**Design-phase OpenSpec output (required):**

At the end of design, generate an OpenSpec change folder capturing intent, technical design, an execution checklist, and the spec deltas for impacted domains:

- `<projectDir>/openspec/changes/<change-id>/proposal.md`
- `<projectDir>/openspec/changes/<change-id>/design.md`
- `<projectDir>/openspec/changes/<change-id>/tasks.md`
- `<projectDir>/openspec/changes/<change-id>/specs/**/spec.md`

**STOP for review:** Present architecture/design outputs (OpenSpec change folder + OpenAPI if relevant) and wait for approval before proceeding to slicing/implementation.

### 4. Break the spec into execution slices

Turn the spec into a small ordered plan. Each slice: spec item(s) covered, intended code area(s), validation approach, dependencies or blockers. Prefer slices that can be reviewed and tested independently.

### 5. Implement against the spec

**Pre-development UI design prompt (required):**

Before any coding begins, create a Figma Make-ready UI prompt (max 4950 characters) based on the project’s features (FSD) and architecture notes, and save it to:

- `<projectDir>/Discovery and Design/FigmaMake_UI_Prompt.txt`

Generate it with:

- `generate-figma-make-prompt.mjs --projectDir "<projectDir>"`

**STOP for review:** Present `FigmaMake_UI_Prompt.txt` and wait for approval before any coding begins.

**Invoke the coding skill** with the spec slice, not just the original user prompt.

When the slice involves frontend-backend integration, both sides must **refer to the OpenAPI spec**. If during coding a change to the API is needed, **edit the OpenAPI spec first**, then implement against the updated spec.

During implementation: keep code changes within approved scope; surface spec gaps immediately; avoid extra behavior unless the spec is updated; document assumptions when a code decision depends on interpretation. If implementation reveals the spec is wrong or incomplete, pause, update the spec (and OpenAPI if applicable), then continue.

### 6. Validate against acceptance criteria

**Invoke the testing skill** after each meaningful slice or at minimum before handoff.

Validation must cover: acceptance criteria, regressions in touched behavior, edge cases implied by the spec, non-goals that must remain unchanged, and **API contract** (when OpenAPI exists) via schema/contract validation (e.g. Zod or OpenAPI-based validator). Tests should answer “did we satisfy the spec?” not “does the code seem reasonable?”

### 7. Close the loop

End with a concise delivery summary: implemented spec items, evidence of validation, deviations, deferred follow-ups, residual risks. If something was omitted, state whether it is out of scope, blocked, or deferred.

### 8. Produce handover deliverable (required)

At the end of delivery, create `<projectDir>/Docs/HANDOVER.md` (using `system-prompts-skills/handover/HANDOVER-TEMPLATE.md`) so downstream teams (BAs, architects, developers, QAs, PMs) have a holistic view of what was built, what changed, and what evidence exists.

## Decision Heuristics

- **Lightweight path:** small bug fix, isolated change, requirements already clear, acceptance provable with few checks.
- **Fuller spec cycle:** new or ambiguous behavior, multiple modules, user-visible workflows, security/reliability/migration risk, success depends on more than a single code edit.

## Traceability Template

| Spec ID | Requirement / Acceptance Criterion | Implementation Area | Validation |
| --- | --- | --- | --- |
| S1 | ... | ... | ... |

When APIs are involved, add **OpenAPI / contract** (endpoint, request/response schema) so contract tests can be traced to the spec.

## Security Evaluation

Before delivery is complete, validate against **OWASP Top 10** (A01–A10). Add a security checkpoint to the closeout note: each item as passed, not applicable (with reason), or flagged (risk and remediation). Do not ship a spec slice with unresolved OWASP findings without explicit acknowledgment in the spec.

## Configuration Management

- Never hardcode environment-specific values in source code.
- Store configuration in dedicated files or environment variables injected at deploy time.
- Document every configuration key. Only configuration files should change on platform migration — no application code edits.
- Treat configuration changes as spec changes: update spec and acceptance criteria before implementation.

## Failure Modes To Avoid

- Coding from an implied spec that was never written down
- Allowing architecture work to expand scope without updating the spec
- Merging “nice to have” into required behavior
- Writing tests only for the happy path when the spec implies edge cases
- Declaring success without showing which acceptance criteria were satisfied
- Shipping without OWASP Top 10 review when the product handles user data, auth, or external input
- Embedding host-specific or environment-specific configuration in application code
- Changing API behavior or payloads during coding without updating the OpenAPI spec first
- Skipping API contract validation when an OpenAPI spec exists and the change touches APIs

## Handoff Style

When reporting progress or completion: lead with current spec status; name the slice being implemented or validated; note any spec changes before describing code changes; make open questions explicit and bounded.

**Success:** requested behavior → specified behavior → implemented behavior → verified behavior.
