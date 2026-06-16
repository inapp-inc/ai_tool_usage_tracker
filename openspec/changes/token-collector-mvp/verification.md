# Verification: Token Collector MVP

## Manual test plan

1. Copy `.env.example` → `.env` and set `POSTGRES_PASSWORD`.
2. `docker compose run --rm migrate`
3. `docker compose up api`
4. `GET http://localhost:8000/api/v1/health` → `database: ok`
5. `POST http://localhost:8000/api/v1/collectors` with body:

```json
{
  "name": "OpenAI Production",
  "provider": "openai",
  "api_token": "sk-test",
  "pull_interval_minutes": 15
}
```

6. `POST http://localhost:8000/api/v1/collectors/{id}/run` → status `completed`, `records_ingested >= 1`
7. `GET http://localhost:8000/api/v1/usage/summary` → non-zero `total_tokens`
8. `GET http://localhost:8000/api/v1/usage/events` → list contains ingested rows
9. Wait 15+ minutes (or PATCH interval to 5) and confirm new run via `GET /collectors/{id}/runs`

## Automated tests

```bash
cd backend && pytest tests/test_token_crypto.py tests/test_collector_adapters.py -q
```

## Evidence log

| Date | Check | Result |
|------|-------|--------|
| 2026-06-16 | Unit tests | pending CI |
