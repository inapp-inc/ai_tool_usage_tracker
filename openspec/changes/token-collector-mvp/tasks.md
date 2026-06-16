# Tasks: Token Collector MVP

## 1. Infrastructure

- [x] 1.1 Simplify `docker-compose.yml` to postgres + migrate + api
- [x] 1.2 Remove Redis/Celery from required config and health check
- [x] 1.3 Update `.env.example` with collector settings

## 2. Database

- [x] 2.1 Alembic `002_collector_usage` migration
- [x] 2.2 SQLAlchemy models in `app/models/collector.py`

## 3. Collector core

- [x] 3.1 `CollectorService` — CRUD, run, persist usage
- [x] 3.2 Provider adapter registry + OpenAI/Anthropic stubs
- [x] 3.3 APScheduler in FastAPI lifespan
- [x] 3.4 Token encrypt/mask helpers

## 4. API

- [x] 4.1 `GET/POST /api/v1/collectors`
- [x] 4.2 `GET/PATCH/DELETE /api/v1/collectors/{id}`
- [x] 4.3 `POST /api/v1/collectors/{id}/run`
- [x] 4.4 `GET /api/v1/collectors/{id}/runs`
- [x] 4.5 `GET /api/v1/usage/events` and `/usage/summary`

## 5. Tests

- [x] 5.1 Unit tests: token crypto, adapter stub
- [ ] 5.2 Integration tests with Postgres (docker compose)

## 6. Frontend (follow-up — user work steps)

- [ ] 6.1 Wire Tools/Integrations UI to `/collectors` API
- [ ] 6.2 Replace mock `usage.ts` / `dashboard.ts` with `/usage/*` endpoints
- [ ] 6.3 Schedule picker → `pull_interval_minutes`

## 7. Hardening (follow-up)

- [ ] 7.1 JWT auth on collector routes
- [ ] 7.2 Production vendor adapters
- [ ] 7.3 Align schema with full `database.md` FK model
- [ ] 7.4 OpenAPI paths in `openapi.yaml` + Redocly lint
