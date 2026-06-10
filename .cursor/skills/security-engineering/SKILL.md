---
name: security-engineering
description: Use when a SEED Unit has security constraints (authn/authz, tenant isolation, input validation, secrets, OWASP risks). Ensures security acceptance criteria and evidence are explicit.
---

# Security engineering

Use this skill to ensure SEED Units and design artifacts include explicit **security requirements**, validation, and evidence.

## Core rules

- Treat authn/authz and tenant isolation as **first-class requirements** when applicable.
- Prefer **deny by default**; ensure safe errors (no enumeration, no leakage).
- Require evidence: security tests, static checks, or reviewable proofs.
- Close each slice with an OWASP Top 10 check when the change touches user input, auth, or data access.
- **Hard enforcement (manual PR operations):** This skill MUST NOT create, open, update, comment on, approve, or merge pull requests. Any PR/merge action is **manual developer work**; this skill only defines required content and evidence.

## Required outputs

- Add security constraints + acceptance criteria to the SEED Unit block.
- Add security evidence requirements (tests, scans, checks) to the SEED Unit block.
- If APIs change, ensure OpenAPI reflects auth requirements.
- Record security-related decisions in `design.md` (threats, mitigations, residual risk).

## Minimum checklist

- Input validation & injection safety
- Authn/authz correctness
- Data isolation / least privilege
- Secrets handling (no secrets in repo; env/config only)
- Safe logging (no sensitive payloads)
