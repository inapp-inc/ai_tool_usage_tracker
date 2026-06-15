# Delta Spec: OpenAPI Frontend Mapping

Aligns OpenSpec API documentation with frontend mock contracts and records gaps for backend implementation.

## ADDED Requirements

### Requirement: Mock-to-REST mapping table

OpenSpec SHALL publish a mapping from each frontend mock function to a target REST endpoint under `/api/v1`.

#### Scenario: Mapping covers all mock domain modules

- **GIVEN** mock modules in `frontend/src/api/` (excluding pure `client.ts`)
- **WHEN** `openspec/specifications/apis/frontend-mock-mapping.md` is created
- **THEN** each exported mock function SHALL have a row with: TypeScript signature summary, HTTP method, path, OpenAPI schema ref (or `GAP`), mock/live status

#### Scenario: Live auth endpoints mapped

- **GIVEN** `auth.ts` uses real HTTP for refresh and me
- **WHEN** the mapping table is published
- **THEN** `refreshToken` SHALL map to `POST /auth/refresh` and `fetchCurrentUser` to `GET /auth/me` with status **live**
- **AND** `login` SHALL map to `POST /auth/login` with status **mock delay wrapper** until full integration

### Requirement: OpenAPI gap register

The mapping documentation SHALL explicitly list frontend-implemented features without corresponding OpenAPI paths or schemas.

#### Scenario: Report subscriptions flagged as gap

- **GIVEN** `reports.ts` implements subscription CRUD
- **WHEN** the gap register is published
- **THEN** it SHALL list missing paths: `GET/POST /reports/{reportId}/subscriptions`, `DELETE /reports/{reportId}/subscriptions/{subscriptionId}`
- **AND** it SHALL reference follow-up change `reporting-backend` or new subscription change

#### Scenario: Credential environment model flagged

- **GIVEN** credentials redesigned per BRD 5.1.3 with `CredentialEnvironment`
- **WHEN** the gap register is published
- **THEN** it SHALL note OpenAPI credential schemas may still reflect legacy ingest-scope model
- **AND** it SHALL reference `user-management-backend` / ADM-003 alignment

#### Scenario: Daily breakdown endpoint flagged

- **GIVEN** `fetchDailyBreakdown(date, teamId, toolId)` used by Insights chart drill-down
- **WHEN** the gap register is published
- **THEN** it SHALL list missing or unverified path for single-day team/user breakdown (e.g. `GET /usage/daily/{date}/breakdown`)

### Requirement: APIs README index update

`openspec/specifications/apis/README.md` SHALL index the new frontend contract documents.

#### Scenario: README links catalog and mapping

- **GIVEN** new companion documents are added
- **WHEN** `apis/README.md` is updated
- **THEN** it SHALL link to `frontend-mock-api-catalog.md` and `frontend-mock-mapping.md`
- **AND** it SHALL note that frontend mock APIs are the interim contract until backend modules ship

## MODIFIED Requirements

### Requirement: Frontend standards API access section

The frontend standards document SHALL reflect that domain API modules currently use in-memory mocks with planned swap to `apiRequest`.

#### Scenario: Mock layer documented in standards

- **GIVEN** `openspec/specifications/frontend-standards.md` API Access section
- **WHEN** the delta is applied
- **THEN** it SHALL state mock modules live in `src/api/*.ts` with artificial latency
- **AND** it SHALL require new domain methods to match types documented in the mock API catalog until OpenAPI is updated
- **AND** it SHALL reference the catalog path under `openspec/specifications/apis/`

#### Scenario: Named exports for pages

- **GIVEN** implemented pages use named exports with `React.lazy` named re-exports
- **WHEN** frontend standards export rules are updated
- **THEN** pages SHALL be documented as named exports (aligning with current codebase over prior default-export exception)
