---
name: observability
description: Use when a change affects runtime behavior and requires logs/metrics/traces, correlation IDs, dashboards/alerts, or evidence of observability in CI/PR. Ensures SEED evidence includes telemetry where applicable.
---

# Observability

Use this skill when a SEED Unit or spec slice requires **observability**: structured logs, traces, metrics, correlation IDs, and operational evidence.

## Core rules

- Prefer **structured logs** with stable keys, not ad-hoc strings.
- Propagate a **correlation ID** through the request/workflow where applicable.
- Add telemetry for failure paths as well as success paths.
- Evidence MUST be captured in the SEED Unit (tests, log examples, metrics, or CI output).
- **Hard enforcement (manual PR operations):** This skill MUST NOT create, open, update, comment on, approve, or merge pull requests. Any PR/merge action is **manual developer work**; this skill only defines required content and evidence.

## Required outputs

- Update the SEED Unit’s **Evidence required** section to include telemetry evidence.
- Update OpenSpec deltas if they introduce observability requirements (e.g., “MUST include correlation_id”).
- For higher-risk changes, add a short “operational notes” section to `design.md` covering:
  - key metrics (latency/error rate/retry counts)
  - log fields (including correlation_id)
  - trace spans / boundaries (if tracing exists)
  - alerting signals (if applicable)

## Failure modes to avoid

- Logging sensitive data (PII/secrets/task content) unintentionally
- Adding telemetry only for happy paths
- Emitting logs without correlation IDs for multi-step flows
