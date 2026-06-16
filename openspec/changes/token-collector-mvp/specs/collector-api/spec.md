# Collector API — Delta Specification (MVP)

## ADDED Requirements

### Requirement: Configure token collector with pull interval

The system SHALL expose `POST /api/v1/collectors` accepting provider name, API token, collector display name, and `pull_interval_minutes` between 5 and 1440.

#### Scenario: Create collector with hourly pull

- **GIVEN** a valid request body with `pull_interval_minutes: 60`
- **WHEN** `POST /collectors` is called
- **THEN** the response status is 201
- **AND** the response includes `id`, `provider`, `pull_interval_minutes`, and masked token
- **AND** the plaintext token is not returned

#### Scenario: Invalid pull interval rejected

- **GIVEN** `pull_interval_minutes: 2`
- **WHEN** `POST /collectors` is called
- **THEN** the response status is 422

### Requirement: Update pull schedule from frontend

The system SHALL allow updating `pull_interval_minutes` and `active` via `PATCH /api/v1/collectors/{collectorId}` and reload the in-process scheduler.

#### Scenario: Update interval reschedules jobs

- **GIVEN** an existing active collector with interval 60
- **WHEN** `PATCH` sets `pull_interval_minutes: 15`
- **THEN** the response status is 200 with updated interval
- **AND** the next scheduled pull uses the new interval

### Requirement: Manual and scheduled collection

The system SHALL run collection via APScheduler inside the API container and support on-demand `POST /api/v1/collectors/{collectorId}/run`.

#### Scenario: Manual run ingests usage

- **GIVEN** an active collector
- **WHEN** `POST /collectors/{id}/run` is called
- **THEN** the response status is 202
- **AND** a `collector_runs` row is created with terminal status `completed` or `failed`
- **AND** on success, `usage_events` rows are inserted

#### Scenario: Idempotent vendor events

- **GIVEN** a usage row with the same `provider` and `vendor_event_id` already exists
- **WHEN** collection runs again
- **THEN** duplicate rows are not created

### Requirement: Read collected token usage

The system SHALL expose `GET /api/v1/usage/events` and `GET /api/v1/usage/summary` for dashboard consumption.

#### Scenario: Usage summary aggregates tokens

- **GIVEN** ingested usage events exist
- **WHEN** `GET /usage/summary` is called
- **THEN** the response includes `total_tokens`, `total_cost`, and `event_count`

## Payload reference

### `CollectorCreateRequest`

| Field | Type | Required |
|-------|------|----------|
| `name` | string | yes |
| `provider` | enum | yes |
| `api_token` | string | yes |
| `pull_interval_minutes` | integer (5–1440) | yes (default 60) |
| `active` | boolean | no (default true) |

### `CollectorResponse`

| Field | Type |
|-------|------|
| `id` | uuid |
| `name` | string |
| `provider` | string |
| `api_token_masked` | string |
| `pull_interval_minutes` | integer |
| `active` | boolean |
| `last_run_at` | datetime \| null |
| `last_success_at` | datetime \| null |
| `last_error` | string \| null |
| `created_at` | datetime |
| `updated_at` | datetime |

### `UsageEventResponse`

| Field | Type |
|-------|------|
| `id` | uuid |
| `collector_id` | uuid \| null |
| `provider` | string |
| `model` | string \| null |
| `occurred_at` | datetime |
| `input_tokens` | integer |
| `output_tokens` | integer |
| `total_tokens` | integer |
| `estimated_cost` | decimal |
| `vendor_event_id` | string \| null |
