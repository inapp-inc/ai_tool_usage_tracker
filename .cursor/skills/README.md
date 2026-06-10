# Project skills (spec-driven development)

These skills are **project-scoped** and used by the agent when working in this repo.

## Master skill

- **spec-driven-development** — Orchestrates the full flow: requirements → architecture → coding → testing. Use when work should follow an explicit spec, traceable to acceptance criteria and validation. **This is the master that drives all others.**

## Supporting skills (invoked by spec-driven-development)

| Skill | When to use |
|-------|-------------|
| **requirements** | No usable spec exists; produce gaps questionnaire and FSD. Templates: `system-prompts-skills/requirement-skill/`. |
| **architecture** | Spec affects boundaries, APIs, data, security, scaling. ADRs: `system-prompts-skills/architecture-adr/`. |
| **coding** | Implementing a spec slice. Language guidelines: `system-prompts-skills/coding-skills/` (React, Node, Python, JS, PHP, CI/CD). |
| **testing** | Validating implementation against acceptance criteria and (when applicable) OpenAPI contract. |

## Engineering skills (SEED / AI-native delivery)

These skills operationalize SEED Units (small PR-sized deliverables) and the engineering evidence expected for AI-native delivery:

| Skill | When to use |
|-------|-------------|
| **seed-unit** | Break work into SEED Units with scope/constraints/acceptance/evidence/rollback and tie each unit to an OpenSpec change folder. |
| **seed-review** | Prepare/execute intent-first reviews: spec delta → risk/rollback → evidence → code scan. |
| **observability** | Add telemetry requirements and evidence (logs/metrics/traces/correlation IDs) when runtime behavior changes. |
| **security-engineering** | Add explicit security constraints, acceptance criteria, and evidence; align with OWASP and authn/authz needs. |
| **performance-engineering** | Turn performance constraints into budgets and measurable evidence (p95/p99, profiling/benchmarks). |
| **rollback-and-flags** | Define safe rollout and rollback steps; prefer feature flags/config toggles for risky behavior changes. |
| **handover** | Produce `<projectDir>/Docs/HANDOVER.md` so downstream teams (BAs, architects, developers, QAs, PMs) have a holistic view of what was built, why, and what evidence exists. |

## Source of truth

- **Skill logic and triggers:** `.cursor/skills/<skill-name>/SKILL.md`
- **Templates and detailed guidelines:** `system-prompts-skills/` (gaps questionnaire, FSD template, ADRs, coding SKILLS.md files)

The SDD (spec-driven-development) skill references those paths so one set of specs and guidelines drives both human and agent workflows.
