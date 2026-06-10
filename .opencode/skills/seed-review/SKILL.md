---
name: seed-review
description: Use to enforce SEED intent review: validate spec deltas first, then risk/rollback, then code. Produces a reviewer-facing checklist and required evidence set.
---

# SEED intent review

Use this skill to prepare and execute reviews that focus on **intent and evidence**, not syntax.

**Manual developer operation:** Creating PRs, requesting reviews, and merging is performed **manually by the developer**. This skill only defines the review order and checklist content.

## Review order

1. **Spec delta** (OpenSpec change folder `specs/**/spec.md`) — does intent match the desired outcome?
2. **Risk & rollback** (`proposal.md` / `design.md`) — is it safe to ship and easy to revert?
3. **Evidence** (`tasks.md` + CI results) — do checks prove acceptance criteria?
4. **Code scan** — sanity check implementation aligns with the above.

## Required outputs

- A completed checklist from `system-prompts-skills/seed/INTENT-REVIEW-CHECKLIST.md`
- A statement of missing evidence (if any) and the next required gate to satisfy
