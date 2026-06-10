---
name: rollback-and-flags
description: Use when a SEED Unit requires safe rollout, rollback steps, feature flags/config toggles, or risk mitigation. Ensures risks and rollback are explicit and testable.
---

# Rollback and feature flags

Use this skill to make changes safe to deploy and easy to revert.

## Core rules

- Every non-trivial SEED Unit MUST include a **risk and rollback** plan.
- Prefer **feature flags** or config toggles for risky behavior changes.
- Rollback MUST be actionable (exact steps), not aspirational.
- **Hard enforcement (manual PR operations):** This skill MUST NOT create, open, update, comment on, approve, or merge pull requests. Any PR/merge action is **manual developer work**; this skill only defines required content and evidence.

## Required outputs

- Add explicit “Risks & rollback” content to the SEED Unit block.
- Ensure `design.md` documents:
  - risk areas (what could break)
  - rollback options (flag off / developer reverts PR / config change)
  - blast radius containment
