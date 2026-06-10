---
name: seed-unit
description: Use to break work into SEED Units (small PR-sized deliverables) with explicit scope, constraints, acceptance criteria, evidence, and rollback. Produces SEED Unit artifacts and ties them to OpenSpec change folders.
---

# SEED Unit

Use this skill to convert a vague or large request into **AI-executable SEED Units**: small, independently shippable PR-sized slices with explicit outcomes and required evidence.

## Core rules

- Each SEED Unit MUST have: **goal**, **scope boundaries**, **constraints**, **acceptance criteria**, **evidence required**, **risks & rollback**, and a **spec link** (OpenSpec path).
- Keep SEED Units small enough to implement and validate in a single PR.
- Do not allow “hidden work”: if it’s required for the unit to be done, it must appear in acceptance criteria and/or tasks.
- **PR operations are manual:** Creating PRs, updating PR descriptions, requesting reviews, and merging are performed **manually by the developer**. This skill only defines the content and artifacts that should be included.

## Required outputs

For each SEED Unit, produce:

- A SEED Unit block (copy/paste) using the template in `system-prompts-skills/seed/SEED-UNIT-TEMPLATE.md`
- An OpenSpec change folder under `<projectDir>/openspec/changes/<seed-id>/`:
  - `proposal.md` (why/what)
  - `design.md` (technical approach + constraints + patterns + risk/rollback)
  - `tasks.md` (implementation checklist; SEED-sized)
  - `specs/**/spec.md` (delta specs for impacted domains)

## Engineering checklist (intent-first)

Before marking the unit ready for implementation, confirm:

- Spec slice exists (OpenSpec delta) and is readable
- Acceptance criteria are measurable (Given/When/Then where applicable)
- Constraints are explicit (perf/security/backward compatibility/cost)
- Evidence requirements are listed (tests/metrics/screenshots/logs/CI run links)
- Failure cases and rollback approach are defined

Use `system-prompts-skills/seed/INTENT-REVIEW-CHECKLIST.md` as the canonical checklist.
