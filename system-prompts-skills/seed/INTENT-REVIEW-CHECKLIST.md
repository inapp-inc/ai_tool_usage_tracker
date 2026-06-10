# SEED intent review checklist

Use this checklist to review **intent first**, not syntax.

## 1) Spec delta review (OpenSpec)

- [ ] The OpenSpec delta (`openspec/changes/<change-id>/specs/**/spec.md`) matches the intended outcome
- [ ] Scope and non-goals are explicit (no hidden work)
- [ ] Requirements use RFC 2119 language (MUST/SHALL/SHOULD/MAY) where appropriate
- [ ] Scenarios cover happy path + relevant failure/edge cases

## 2) Contracts and boundaries

- [ ] API/message/data contracts are correct and version-safe (OpenAPI/message schemas as applicable)
- [ ] Backward compatibility expectations are explicit

## 3) Safety, security, and compliance

- [ ] Authn/authz and tenant isolation are correct where applicable
- [ ] Input validation and injection risks addressed
- [ ] PII/secrets handling is safe (including safe logging)
- [ ] OWASP risks considered for the slice

## 4) Reliability and failure modes

- [ ] Timeouts/retries/fallbacks are specified and tested where applicable
- [ ] Poison message/quarantine/DLQ strategy defined when messaging is involved

## 5) Observability

- [ ] Structured logs include stable keys (and correlation_id where applicable)
- [ ] Metrics/traces exist (or are explicitly out of scope) for runtime-impacting changes

## 6) Evidence and gates

- [ ] Acceptance criteria are measurable and mapped to evidence
- [ ] Evidence is attached (tests, CI run links, screenshots, metrics)
- [ ] **Manual developer operation:** Do not merge unless required checks are green and evidence matches the SEED Unit (merge performed by developer)

## 7) Risks & rollback

- [ ] Risks are explicit and bounded
- [ ] Rollback steps are actionable (flag off / config toggle / revert PR)
