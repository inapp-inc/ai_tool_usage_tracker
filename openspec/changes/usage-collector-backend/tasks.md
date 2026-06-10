# Tasks: Usage Collector Backend

---

## 1. Schema

- [ ] 1.1 Alembic migration: `ingestion.collector_configs`, `ingestion.collector_runs`
- [ ] 1.2 SQLAlchemy models and repositories

## 2. OpenAPI

- [ ] 2.1 Add `Collectors` tag and schemas to `openapi.yaml`
- [ ] 2.2 Redocly lint

## 3. Provider connect API

- [ ] 3.1 Implement `GET/POST /api/v1/collectors`
- [ ] 3.2 Implement `GET/PATCH/DELETE /api/v1/collectors/{id}`
- [ ] 3.3 Implement `POST /api/v1/collectors/{id}/run`
- [ ] 3.4 RBAC + audit logging on mutations

## 4. Collector adapters

- [ ] 4.1 `CollectorAdapter` protocol per ADR-011
- [ ] 4.2 OpenAI, Anthropic, Azure AI, Cursor adapters
- [ ] 4.3 Wire to usage ingest service (idempotent)

## 5. Scheduling

- [ ] 5.1 Celery task `ingestion.collect_usage`
- [ ] 5.2 Beat hourly + daily scanner tasks
- [ ] 5.3 `last_run_at` dedupe guard; skip inactive configs

## 6. Pipeline hooks

- [ ] 6.1 Enqueue aggregate refresh after successful collection
- [ ] 6.2 Invoke threshold evaluation org hook

## 7. Tests

- [ ] 7.1 All scenarios in verification.md § Spec Alignment

## 8. Update downstream change docs

- [ ] 8.1 Confirm dashboard/reporting/notifications changes reference collector dependency (done in proposals)

## 9. Verification & Evidence

- [ ] 9.1 Run all acceptance tests; populate Evidence Log
- [ ] 9.2 Audit Record sign-off
- [ ] 9.3 `openspec validate usage-collector-backend --type change --strict`
