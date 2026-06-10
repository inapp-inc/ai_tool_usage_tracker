# Implementation Task Summary

Quick reference of all **65** Phase 1 tasks. See epic files for full Definition of Done.

| Task ID | Description | Complexity | Dependencies | Status |
|---------|-------------|------------|--------------|--------|
| **Foundation** | | | | |
| TASK-INF-001 | Docker Compose stack (Postgres, Redis, API, workers) | M | — | Done¹ |
| TASK-INF-002 | FastAPI application skeleton | M | INF-001 | |
| TASK-INF-003 | Celery worker and Beat setup | M | INF-001, INF-002 | |
| TASK-INF-004 | Alembic migration framework | S | INF-002 | |
| TASK-INF-005 | CI pipeline (GitHub Actions) | M | INF-002 | |
| TASK-INF-006 | React SPA scaffold | M | — | |
| **Database** | | | | |
| TASK-DB-001 | Auth schema migrations | M | INF-004 |
| TASK-DB-002 | Admin schema migrations | L | DB-001 |
| TASK-DB-003 | Ingestion schema migrations | M | DB-002 |
| TASK-DB-004 | Usage schema migrations | L | DB-002 |
| TASK-DB-005 | Notifications, reporting, audit schemas | M | DB-002, DB-004 |
| TASK-DB-006 | Performance indexes | S | DB-004, DB-005 |
| TASK-DB-007 | Repository layer and Unit of Work | L | DB-001–005 |
| **Platform** |
| TASK-PLT-001 | JWT authentication API | M | DB-001, INF-002 |
| TASK-PLT-002 | RBAC middleware and policies | L | PLT-001 |
| TASK-PLT-003 | Audit log service | M | DB-005, PLT-002 |
| TASK-PLT-004 | Audit log query and export API | M | PLT-003 |
| TASK-PLT-005 | Correlation ID and Problem Details | S | INF-002 |
| TASK-PLT-006 | Organization timezone settings | S | DB-001 |
| TASK-PLT-007 | Data retention enforcement job | M | DB-004, DB-005, INF-003 |
| **Administration** |
| TASK-ADM-001 | AI tool management API | M | DB-002, PLT-002, PLT-003 |
| TASK-ADM-002 | Team management API | M | DB-002, PLT-002, PLT-003 |
| TASK-ADM-003 | API credential management API | L | DB-002, PLT-002, PLT-003 |
| TASK-ADM-004 | Threshold management API | M | DB-002, ADM-001, ADM-002, PLT-002 |
| **Ingestion** |
| TASK-ING-001 | Object storage adapter | M | INF-001 |
| TASK-ING-002 | File upload API | M | ING-001, DB-003, ADM-002, PLT-002 |
| TASK-ING-003 | Vendor parser adapters | L | INF-002 |
| TASK-ING-004 | Parse and preview pipeline | L | ING-002, ING-003, INF-003, DB-003 |
| TASK-ING-005 | Import commit with idempotency | L | ING-004, USG-001 |
| TASK-ING-006 | Reprocess upload flow | S | ING-004 |
| TASK-ING-007 | AI usage collector (vendor API sync) | L | ADM-003, USG-001, USG-002, ING-008 |
| TASK-ING-008 | Provider connect API (frontend token + schedule) | M | DB-003, ADM-003, ING-007 |
| **Usage** |
| TASK-USG-001 | Usage event recording and cost calculator | L | DB-004, ADM-001 |
| TASK-USG-002 | Aggregation refresh job | L | USG-001, INF-003 |
| TASK-USG-003 | Batch usage ingestion API | M | USG-001, USG-004, PLT-002 |
| TASK-USG-004 | Idempotency key handling | M | DB-004, USG-001 |
| **Dashboards** |
| TASK-DSH-001 | Redis cache-aside layer | M | INF-001, USG-002 |
| TASK-DSH-002 | Token and cost widget APIs | M | DSH-001, PLT-002, USG-002 |
| TASK-DSH-003 | Usage by tool and team widget APIs | M | DSH-002 |
| TASK-DSH-004 | Top consumers and alert widget APIs | M | DSH-002, NTF-002 |
| TASK-DSH-005 | Trends and my usage widget APIs | M | DSH-002, PLT-006 |
| TASK-DSH-006 | Dashboard export support | M | DSH-002, RPT-001 |
| **Notifications** |
| TASK-NTF-001 | Threshold evaluation engine | L | ADM-004, USG-002, INF-003 |
| TASK-NTF-002 | Alerts and in-app notification persistence | M | DB-005, NTF-001 |
| TASK-NTF-003 | Notification center API | S | NTF-002, PLT-002 |
| TASK-NTF-004 | Email notification worker | M | NTF-001, ADM-003, INF-003 |
| **Reporting** |
| TASK-RPT-001 | Report rendering engine | L | USG-002, PLT-002 |
| TASK-RPT-002 | Sync and async report API | L | RPT-001, ING-001, INF-003 |
| TASK-RPT-003 | Six report type implementations | XL | RPT-001, PLT-004, ADM-003 |
| TASK-RPT-004 | Scheduled report delivery (P1) | L | RPT-002, NTF-004, PLT-006 |
| **Frontend** |
| TASK-UI-001 | Authentication UI | M | INF-006, PLT-001 |
| TASK-UI-002 | Administration screens | XL | UI-001, ADM-001–004 |
| TASK-UI-003 | Upload and import wizard | L | UI-001, ING-002–006 |
| TASK-UI-004 | Dashboard page | XL | UI-001, DSH-002–005 |
| TASK-UI-005 | Reports UI | L | UI-001, RPT-002, RPT-003 |
| TASK-UI-006 | Notification center UI | M | UI-001, NTF-003 |
| TASK-UI-007 | Audit log viewer | S | UI-001, PLT-004 |
| TASK-UI-008 | Individual usage view | M | UI-004, DSH-005 |
| **Operations** |
| TASK-OPS-001 | OpenTelemetry instrumentation | M | INF-002, INF-003, PLT-005 |
| TASK-OPS-002 | Prometheus metrics and Grafana | M | OPS-001, DSH-001 |
| TASK-OPS-003 | PostgreSQL backup script | S | INF-001 |
| TASK-OPS-004 | OpenAPI contract tests | M | INF-005 |
| TASK-OPS-005 | Accessibility baseline (P1) | M | UI-001–006 |
| TASK-OPS-006 | Credential expiry reminder job | S | ADM-003, NTF-002, NTF-004 |
| TASK-OPS-007 | End-to-end MVP smoke test | L | UI-003, UI-004, RPT-003, INF-001 |

**Total estimated engineering:** ~35–45 person-weeks (parallelizable across backend, frontend, and ops tracks).

¹ TASK-INF-001 implemented; live `docker compose up` verification pending where Docker Desktop is unavailable. See [01-foundation.md](./01-foundation.md#implementation-status).
