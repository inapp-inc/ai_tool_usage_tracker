# Handover (Delivery Summary)

**Project:** `<ProjectName>`  
**Date:** `<YYYY-MM-DD>`  
**Owner(s):** `<names/roles>`  
**Scope:** `<SEED IDs / change IDs / sprint / release>`  

## 1) Executive summary (for PMs/BAs)

- **What changed:**  
- **Why it matters:**  
- **What is explicitly out of scope:**  

## 2) Specs and contracts (source of truth)

- **OpenSpec specs (source-of-truth):**
  - `<projectDir>/openspec/specs/...`
- **OpenSpec changes implemented (intent + deltas):**
  - `<projectDir>/openspec/changes/<change-id>/`
- **API contract (OpenAPI), if applicable:**
  - `<projectDir>/Docs/openapi.yaml`

## 3) What was built (for developers/architects)

- **Capabilities delivered:**
  - `<capability>`
- **Key design decisions:**
  - `<decision> — rationale`
- **Patterns considered (chosen vs rejected):**
  - Chosen:
  - Rejected:

## 4) QA validation guide (for QAs)

- **Acceptance criteria covered:**
  - `<AC id> — evidence`
- **Test execution:**
  - Automated: `<test suite / command / file>`
  - Manual: `<steps + expected results>`
- **Edge/failure cases to validate:**
  - `<case>`
- **Known limitations:**
  - `<limitation>`

## 5) Evidence and quality gates (for all)

- **CI runs (manual links):**
  - `<link>`
- **Tests added/updated:**
  - `<name/path>`
- **Contract validation (OpenAPI/schema), if applicable:**
  - `<where/how>`
- **Performance evidence, if applicable:**
  - Budgets: `<p95/p99>`
  - Results: `<numbers + environment assumptions>`
- **Security checkpoint (OWASP / authz / input validation):**
  - `<summary>`
- **Observability evidence:**
  - Logs: `<key fields e.g. correlation_id>`
  - Metrics/traces: `<what exists>`

## 6) Ops notes (for SREs/devs)

- **Configuration keys / env vars:**
  - `<KEY> — purpose`
- **Data migrations / backfills:**
  - `<what ran / what’s required>`
- **Rollout steps:**
  - `<steps>`
- **Rollback plan (actionable):**
  - `<flag off / config toggle / revert steps (manual)>`

## 7) Risks, open questions, and follow-ups

- **Residual risks:**
  - `<risk> — mitigation`
- **Open questions:**
  - `<question> — owner — due`
- **Deferred work (parking lot):**
  - `<item>`
