---
name: performance-engineering
description: Use when a SEED Unit includes performance constraints (latency/throughput/p95/p99, large datasets, UI responsiveness). Converts constraints into measurable budgets and evidence.
---

# Performance engineering

Use this skill when performance requirements are part of a SEED Unit or spec slice.

## Core rules

- Convert performance constraints into **explicit budgets** (p50/p95/p99, throughput, payload size).
- Ensure test intent and evidence are explicit (benchmarks, profiling, load tests, or targeted measurements).
- Avoid “performance vibes”: evidence must map to stated budgets or explicitly call out missing budgets.
- **Hard enforcement (manual PR operations):** This skill MUST NOT create, open, update, comment on, approve, or merge pull requests. Any PR/merge action is **manual developer work**; this skill only defines required content and evidence.

## Required outputs

- Update OpenSpec deltas to include any new performance requirements using RFC 2119 language.
- Add performance evidence requirements to the SEED Unit block:
  - tests/benchmarks names and commands
  - captured metrics (p95, error rate, CPU/mem)
  - environment assumptions
- Add a short “performance notes” section to `design.md` when constraints exist.
