# Testing Specifications — Traceability Index

Quick-reference matrices linking test layers to requirements. Full strategy: [testing.md](./testing.md).

---

## Test Layer → Tooling

| Layer | Primary tools | CI job |
|-------|---------------|--------|
| Unit | pytest, Vitest, React Testing Library | `test-unit`, `test-frontend` |
| Integration | pytest, httpx, Testcontainers / Compose | `test-integration` |
| Contract | Schemathesis, `@redocly/cli lint` | `test-contract`, `lint` |
| E2E | Playwright | `test-e2e` (nightly) |
| Performance | k6, pytest-benchmark | `test-performance` (nightly) |
| Security | Bandit, pip-audit, gitleaks, OWASP ZAP | `security-static`, nightly ZAP |
| Acceptance | pytest + Playwright mapped to AC-* IDs | Release gate checklist |

---

## NFR → Performance / Security Test Mapping

| NFR | Test ID(s) | Layer |
|-----|------------|-------|
| NFR-PER-001 | PERF-001, PERF-002 | Performance |
| NFR-PER-002 | PERF-003, PERF-004 | Performance |
| NFR-PER-003 | PERF-005, PERF-006 | Performance |
| NFR-PER-004 | PERF-007, PERF-008, PERF-009 | Performance |
| NFR-PER-005 | PERF-010 | Performance + Integration |
| NFR-SEC-003 | SEC-003, SEC-007 | Security + Integration |
| NFR-SEC-004 | SEC-001 | Security + Integration |
| NFR-SEC-005 | SEC-005, SEC-009 | Security + Integration |
| NFR-SEC-006 | SEC-004 | Security + Contract |
| NFR-SEC-007 | SEC-006, SEC-010 | Security |
| NFR-SEC-008 | SEC-008 | Security (CI scan) |
| NFR-SCL-005 | SEC-002, E2E-007 | Integration + E2E |
| NFR-AVL-004 | Integration health tests | Integration |
| NFR-ACC-001 – 003 | axe, keyboard walkthrough | Acceptance (TASK-OPS-005) |
| NFR-MON-001 | Metrics scrape verification | Integration / manual staging |

---

## FR Module → Minimum Test Surfaces

| Module | Unit | Integration | E2E | Contract |
|--------|------|-------------|-----|----------|
| Platform (FR-PLT) | JWT, RBAC helpers | Auth API, audit | E2E-006 | Auth, audit tags |
| Administration (FR-ADM) | Business rules | CRUD APIs | E2E-001 | Tools, teams tags |
| Ingestion (FR-ING) | Parsers | Upload pipeline + local storage | E2E-002 | Uploads tag |
| Usage (FR-USG) | Cost calculator | Idempotency, batch API | — | Usage tag |
| Dashboards (FR-DSH) | Cache key logic | Widget APIs | E2E-003 | Dashboard tag |
| Notifications (FR-NTF) | Threshold eval | Alert persistence | E2E-004 | Notifications tag |
| Reporting (FR-RPT) | Report builders | Sync/async API | E2E-005 | Reports tag |
| Infrastructure | Connectivity | Compose health | — | Health (interim `/health`) |

---

## Acceptance Criteria Automation Policy

| Priority | Automation requirement |
|----------|------------------------|
| **P0** | MUST have automated test (unit, integration, contract, E2E, or performance as appropriate) |
| **P1** | SHOULD be automated; manual allowed with documented evidence |
| **P2** | Manual acceptable |

---

## See Also

- [testing.md](./testing.md) — full specification
- [apis/openapi.yaml](./apis/openapi.yaml) — contract source of truth
- [requirements/NFR.md](../requirements/NFR.md) — non-functional acceptance criteria
- [tasks/11-operations.md](../tasks/11-operations.md) — OPS test tasks
