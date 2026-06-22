# Tasks: copilot-schema

## 1. Schema & models

- [x] Requirements doc `openspec/requirements/copilot-productivity-analytics.md`
- [x] Migration `031_copilot_productivity_schema.py`
- [x] SQLAlchemy models in `app/models/copilot.py`

## 2. Ingestion

- [x] `CopilotProductivityParser` — map NDJSON/seats to domain rows
- [x] `CopilotIngestService` — upsert org, user usage, seats
- [x] Fetch org-level metrics in adapter
- [x] Collector: route copilot sync to ingest; skip `usage_events`

## 3. Analytics API

- [x] `GET /copilot/overview`
- [x] `GET /copilot/users` and `GET /copilot/users/{login}`
- [x] `GET /copilot/insights`
- [x] Report endpoints (seats, productivity, cost)

## 4. Frontend

- [x] `api/copilot.ts` client
- [x] `CopilotDashboardPage` — cards + charts
- [x] Route + nav link from Insights

## 5. Validation

- [x] Unit tests: parser
- [x] Exclude copilot from token dashboard queries
- [x] pytest + frontend build
