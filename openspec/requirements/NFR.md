# Non-Functional Requirements (NFR)

Non-functional specifications for the **AI Tool Usage Tracker** platform.

Derived from [project.md](../project.md), and cross-cutting functional requirements in [07-platform-security.md](./07-platform-security.md).

> **Deployment context (ADR-013):** Phase 1 runs entirely on **Docker Compose** with **local Docker volumes** for PostgreSQL, Redis, file storage, and backups. Requirements referencing AWS S3, EKS, or ElastiCache apply to **Phase 2 cloud migration** unless explicitly updated below.

## Document Conventions

| Field | Description |
|-------|-------------|
| **Requirement ID** | Stable identifier for traceability (e.g., `NFR-SEC-001`) |
| **Priority** | P0 = MVP release blocker; P1 = MVP should-have; P2 = Phase 2 |
| **RFC 2119** | SHALL = mandatory; SHOULD = recommended; MAY = optional |

## Priority Legend

| Priority | Meaning |
|----------|---------|
| **P0** | Must meet for Phase 1 (MVP) go-live |
| **P1** | Should meet for Phase 1; required for full operational readiness |
| **P2** | Phase 2 or organization-specific hardening |

## Traceability Index

| Category | IDs |
|----------|-----|
| Security | NFR-SEC-001 – NFR-SEC-008 |
| Performance | NFR-PER-001 – NFR-PER-006 |
| Scalability | NFR-SCL-001 – NFR-SCL-005 |
| Availability | NFR-AVL-001 – NFR-AVL-004 |
| Monitoring | NFR-MON-001 – NFR-MON-006 |
| Auditability | NFR-AUD-001 – NFR-AUD-004 |
| Accessibility | NFR-ACC-001 – NFR-ACC-004 |
| Compliance | NFR-CMP-001 – NFR-CMP-005 |
| Backup and Recovery | NFR-BKP-001 – NFR-BKP-005 |
| Localization | NFR-LOC-001 – NFR-LOC-003 |

---

# Security

Protect sensitive usage, cost, and credential data through defense-in-depth controls aligned with the platform stack (FastAPI, PostgreSQL, Redis, **local volume storage**, JWT/RBAC).

---

## NFR-SEC-001: Encryption at Rest

### Description

The system SHALL encrypt sensitive data at rest using AES-256 or equivalent industry-standard algorithms.

### Scope

- Vendor API credentials (FR-ADM-003)
- Database volumes containing usage, cost, and user data
- Uploaded vendor export files on **local storage volume** (`storage_data`)
- Backup artifacts on **`backups_data` volume**

### Acceptance Criteria

- **AC-NFR-SEC-001-01:** Given API credentials stored in the database, when inspected at the storage layer, then values are encrypted and not readable in plaintext.
- **AC-NFR-SEC-001-02:** Given upload/report files on the local storage volume, when host disk encryption is reviewed, then data at rest is protected (host LUKS/BitLocker or equivalent).
- **AC-NFR-SEC-001-03:** Given PostgreSQL Docker data volume, when infrastructure is reviewed, then host/volume encryption at rest is enabled.

### Related Requirements

- FR-ADM-003, FR-ING-001

### Priority

**P0**

---

## NFR-SEC-002: Encryption in Transit

### Description

The system SHALL encrypt all client-server and service-to-service communication using TLS 1.2 or higher.

### Scope

- Browser-to-API traffic
- API-to-database connections
- API-to-Redis and Celery broker connections
- Email and external webhook integrations (where applicable)

### Acceptance Criteria

- **AC-NFR-SEC-002-01:** Given a production endpoint, when TLS configuration is scanned, then only TLS 1.2+ is accepted and weak cipher suites are disabled.
- **AC-NFR-SEC-002-02:** Given HTTP requests to production APIs, when submitted without TLS, then connections are rejected or redirected to HTTPS.

### Priority

**P0**

---

## NFR-SEC-003: Authentication and Session Security

### Description

The system SHALL authenticate users via JWT with secure token lifecycle management.

### Requirements

- JWT signing keys MUST be stored in host `.env` or Docker Compose secrets — not in source code (Phase 2: secrets manager).
- Access tokens MUST expire within a configurable window (default: 15–60 minutes).
- Refresh token rotation SHOULD be supported for long-lived sessions.
- Failed login attempts SHOULD be rate-limited to mitigate brute-force attacks.
- Phase 1 excludes full SSO/SAML (FR-P2-002); JWT-based auth is in scope.

### Acceptance Criteria

- **AC-NFR-SEC-003-01:** Given an expired JWT, when an API request is made, then the system returns 401 Unauthorized.
- **AC-NFR-SEC-003-02:** Given repeated failed login attempts exceeding the configured threshold, when additional attempts occur, then the account or IP is temporarily throttled.

### Related Requirements

- FR-PLT-001

### Priority

**P0**

---

## NFR-SEC-004: Role-Based Access Control

### Description

The system SHALL enforce RBAC on every API endpoint and UI action so users access only authorized data and operations.

### Requirements

- Authorization MUST be evaluated server-side; UI hiding alone is insufficient.
- Roles MUST include: Super Admin, Team Admin, Finance Viewer, Team Member, Auditor.
- Principle of least privilege MUST apply to service accounts and background jobs.

### Acceptance Criteria

- **AC-NFR-SEC-004-01:** Given a Team Member JWT, when a privileged admin endpoint is called, then the system returns 403 Forbidden.
- **AC-NFR-SEC-004-02:** Given automated security tests per role, when executed against the API surface, then no unauthorized data leakage occurs.

### Related Requirements

- FR-PLT-001

### Priority

**P0**

---

## NFR-SEC-005: Secure Credential Handling

### Description

The system SHALL protect vendor API credentials throughout their lifecycle.

### Requirements

- Credentials MUST be masked in UI after creation (show last 4 characters or equivalent).
- Credential values MUST NOT appear in application logs, error messages, or reports.
- Credential decryption MUST occur only in memory at point of use for ingestion jobs.
- Key rotation and expiration tracking MUST be supported (FR-ADM-003).

### Acceptance Criteria

- **AC-NFR-SEC-005-01:** Given a saved API key viewed in the admin UI, when displayed, then the full secret is not shown.
- **AC-NFR-SEC-005-02:** Given application logs during ingestion, when reviewed, then no plaintext credential values are present.

### Related Requirements

- FR-ADM-003, FR-RPT-006

### Priority

**P0**

---

## NFR-SEC-006: Input Validation and Injection Prevention

### Description

The system SHALL validate and sanitize all external input to prevent injection and abuse.

### Requirements

- API inputs MUST be validated using schema validation (e.g., Pydantic models in FastAPI).
- SQL MUST be executed via parameterized queries or ORM; raw string concatenation is prohibited.
- File uploads MUST be validated for type, size (max 50 MB), and malicious content patterns.
- Upload filenames MUST be sanitized before storage.

### Acceptance Criteria

- **AC-NFR-SEC-006-01:** Given malformed JSON or out-of-range parameters, when submitted to an API, then the request is rejected with 422 and no partial side effects occur.
- **AC-NFR-SEC-006-02:** Given a file upload exceeding 50 MB, when submitted, then upload is rejected before processing.

### Related Requirements

- FR-ING-001

### Priority

**P0**

---

## NFR-SEC-007: Security Headers and OWASP Baseline

### Description

The system SHOULD implement OWASP-aligned security controls for web applications.

### Requirements

- Production responses SHOULD include security headers: `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options` or `frame-ancestors`, `Strict-Transport-Security`.
- Dependencies MUST be scanned for known vulnerabilities in CI (GitHub Actions).
- Critical and high CVEs in direct dependencies MUST be remediated before production release or documented with accepted risk.

### Acceptance Criteria

- **AC-NFR-SEC-007-01:** Given production HTTP responses, when security headers are inspected, then baseline OWASP headers are present.
- **AC-NFR-SEC-007-02:** Given CI dependency scan results, when a critical CVE is detected in a direct dependency, then build fails or requires explicit waiver.

### Priority

**P1**

---

## NFR-SEC-008: Secrets and Configuration Management

### Description

The system SHALL manage secrets and environment configuration without embedding sensitive values in code or images.

### Requirements

- Secrets (DB passwords, JWT keys, encryption keys, SMTP credentials) MUST be injected via environment variables, Docker Compose secrets, or a secrets manager (Phase 2).
- `.env` files with production secrets MUST NOT be committed to version control.
- Configuration MUST support separate sandbox and production environments (FR-ADM-003).

### Acceptance Criteria

- **AC-NFR-SEC-008-01:** Given repository scan, when searched for hardcoded secrets, then no production credentials are found in source.
- **AC-NFR-SEC-008-02:** Given deployment to production, when configuration is reviewed, then secrets are sourced from approved secret storage.

### Priority

**P0**

---

# Performance

Ensure responsive user experience and timely background processing for operational and financial workflows.

---

## NFR-PER-001: Dashboard Response Time

### Description

Dashboard views SHALL load within 3 seconds at p95 for standard queries at reference scale.

### Targets

| Metric | Target |
|--------|--------|
| Dashboard time-to-interactive (p95) | ≤ 3 seconds |
| Widget API response (p95) | ≤ 2 seconds |
| Reference scale | 50 tools, 200 teams, 5,000 users |

### Acceptance Criteria

- **AC-NFR-PER-001-01:** Given reference-scale test data, when dashboard load is measured at p95, then time-to-interactive is ≤ 3 seconds.
- **AC-NFR-PER-001-02:** Given concurrent users (minimum 50 simultaneous dashboard sessions), when load test runs, then p95 remains within target under normal operating conditions.

### Related Requirements

- FR-DSH-009, FR-PLT-003

### Priority

**P0**

---

## NFR-PER-002: Report Generation Time

### Description

Standard reports SHALL generate within 10 seconds at p95; larger reports MUST use asynchronous processing.

### Targets

| Metric | Target |
|--------|--------|
| Standard report generation (p95) | ≤ 10 seconds |
| Async report job acknowledgment | ≤ 2 seconds |
| Async report completion notification | ≤ 5 minutes for reports up to 1M rows |

### Acceptance Criteria

- **AC-NFR-PER-002-01:** Given standard filtered reports at reference scale, when generated synchronously, then p95 completion is ≤ 10 seconds.
- **AC-NFR-PER-002-02:** Given a report exceeding sync thresholds, when requested, then async job is queued within 2 seconds and user receives completion notification.

### Related Requirements

- FR-RPT-007, FR-PLT-003

### Priority

**P0**

---

## NFR-PER-003: API Latency

### Description

Interactive API endpoints SHALL respond within defined latency budgets.

### Targets

| Endpoint Class | p95 Target |
|----------------|------------|
| Read (list/detail) | ≤ 500 ms |
| Write (create/update) | ≤ 1,000 ms |
| Authentication | ≤ 300 ms |

### Acceptance Criteria

- **AC-NFR-PER-003-01:** Given load testing of CRUD admin APIs, when measured at p95, then latency targets are met at reference scale.

### Priority

**P1**

---

## NFR-PER-004: Usage Ingestion Throughput

### Description

The system SHALL process usage ingestion without blocking interactive workloads.

### Targets

| Metric | Target |
|--------|--------|
| Near real-time ingestion lag | ≤ 5 minutes from event receipt to aggregate update |
| Batch ingestion throughput | ≥ 10,000 records/minute per worker |
| File upload parse initiation | ≤ 30 seconds after upload completes |

### Acceptance Criteria

- **AC-NFR-PER-004-01:** Given near real-time usage events, when ingested continuously, then team aggregates reflect updates within 5 minutes at p95.
- **AC-NFR-PER-004-02:** Given a 50 MB valid vendor export, when uploaded, then parsing job starts within 30 seconds.

### Related Requirements

- FR-USG-002, FR-ING-001

### Priority

**P0**

---

## NFR-PER-005: Notification Delivery Latency

### Description

Critical alerts and email notifications SHALL be delivered within operational SLAs.

### Targets

| Metric | Target |
|--------|--------|
| In-app notification creation after threshold breach | ≤ 1 minute |
| Critical email delivery (p95) | ≤ 5 minutes |

### Acceptance Criteria

- **AC-NFR-PER-005-01:** Given a critical threshold breach, when evaluation completes, then in-app notification exists within 1 minute and email is dispatched within 5 minutes at p95.

### Related Requirements

- FR-NTF-002, FR-NTF-003

### Priority

**P0**

---

## NFR-PER-006: Caching Strategy

### Description

The system SHOULD use Redis caching to meet performance targets without stale data beyond acceptable bounds.

### Requirements

- Dashboard aggregate queries SHOULD be cacheable with TTL aligned to ingestion freshness (default: 1–5 minutes).
- Cache invalidation MUST occur on relevant write operations (tool pricing change, team reassignment).
- Cache keys MUST include tenant/organization and RBAC scope to prevent data leakage.

### Acceptance Criteria

- **AC-NFR-PER-006-01:** Given a pricing configuration change, when saved, then affected dashboard caches are invalidated within 1 minute.
- **AC-NFR-PER-006-02:** Given cached dashboard data, when a user outside authorized scope requests the same cache key pattern, then no cross-scope data is returned.

### Priority

**P1**

---

# Scalability

Support organizational growth in tools, teams, users, and data volume without architectural rework for Phase 1 targets.

---

## NFR-SCL-001: Reference Capacity Targets

### Description

The platform SHALL support the following minimum capacity without degradation beyond defined performance NFRs.

### Targets

| Dimension | Phase 1 Minimum |
|-----------|-----------------|
| AI tools configured | 50 |
| Teams | 200 |
| Users | 5,000 |
| Usage records | 50 million (24-month retention window) |
| Concurrent interactive users | 200 |

### Acceptance Criteria

- **AC-NFR-SCL-001-01:** Given a deployment at reference capacity, when performance tests run, then NFR-PER-001 and NFR-PER-002 targets are met.

### Related Requirements

- FR-PLT-003

### Priority

**P0**

---

## NFR-SCL-002: Horizontal Scaling

### Description

Application and worker tiers SHALL support scaling via **Docker Compose service replicas** on one or more Docker hosts (Phase 2: Kubernetes/EKS).

### Requirements

- API servers MUST be stateless; session state MUST NOT be stored on individual nodes.
- Celery workers MUST scale independently of API replicas.
- Database connection pooling MUST be configured to support scaled API instances.

### Acceptance Criteria

- **AC-NFR-SCL-002-01:** Given increased load, when additional API replicas are deployed, then throughput increases proportionally without code changes.
- **AC-NFR-SCL-002-02:** Given increased ingestion backlog, when Celery workers are scaled, then queue depth decreases measurably.

### Priority

**P0**

---

## NFR-SCL-003: Database Scalability

### Description

PostgreSQL schema and indexing SHALL support growth in usage and reporting queries.

### Requirements

- Usage and aggregation tables MUST include indexes on common filter columns: date range, team_id, tool_id, user_id.
- Long-running analytics SHOULD use read replicas or materialized views where needed (Phase 2 enhancement allowed).
- Schema evolution MUST be backward-compatible per OpenSpec principles.

### Acceptance Criteria

- **AC-NFR-SCL-003-01:** Given explain plans for standard dashboard and report queries, when reviewed at reference scale, then no full-table scans occur on primary fact tables without justification.

### Priority

**P1**

---

## NFR-SCL-004: Object Storage Scalability

### Description

Uploaded files and async report outputs SHALL persist on **dedicated local Docker volumes** without using the container ephemeral filesystem.

### Requirements

- Upload storage MUST use the named volume `storage_data` (or equivalent bind mount on a dedicated disk).
- Operators MUST monitor disk usage; retention jobs purge aged uploads and reports per policy.
- Phase 2 MAY migrate to S3 if disk limits are exceeded at scale.

### Acceptance Criteria

- **AC-NFR-SCL-004-01:** Given upload volume at reference scale, when storage metrics are reviewed, then no ephemeral container filesystem exhaustion occurs and `storage_data` volume has headroom.

### Related Requirements

- FR-ING-001, FR-RPT-007

### Priority

**P0**

---

## NFR-SCL-005: Multi-Tenant Readiness

### Description

The data model SHOULD isolate organizational data to support future multi-tenant deployment.

### Requirements

- All domain entities MUST include organization/tenant identifier.
- Queries MUST filter by tenant context; cross-tenant access MUST be impossible at the application layer.

### Acceptance Criteria

- **AC-NFR-SCL-005-01:** Given two tenant datasets in a shared environment, when a user from tenant A queries any API, then no tenant B data is returned.

### Priority

**P2**

---

# Availability

Maintain reliable access for administrators, finance stakeholders, and team users.

---

## NFR-AVL-001: Uptime SLA

### Description

The production application SHALL maintain 99.5% uptime measured monthly.

### Targets

| Metric | Target |
|--------|--------|
| Monthly uptime | ≥ 99.5% |
| Maximum planned maintenance window | 4 hours/month with 72-hour notice |
| Unplanned downtime budget | ≤ 3.6 hours/month |

### Acceptance Criteria

- **AC-NFR-AVL-001-01:** Given production monitoring over a rolling 30-day window, when uptime is calculated excluding approved maintenance, then result is ≥ 99.5%.

### Related Requirements

- FR-PLT-003

### Priority

**P0**

---

## NFR-AVL-002: High Availability Deployment

### Description

Production deployments SHOULD eliminate single points of failure for stateless tiers.

### Requirements

- Minimum 2 API replicas across availability zones.
- PostgreSQL MUST run in Docker with a persistent volume; streaming replica optional Phase 2 (not Amazon RDS).
- Redis SHOULD use clustered or managed HA configuration for cache and Celery broker.

### Acceptance Criteria

- **AC-NFR-AVL-002-01:** Given loss of a single API pod, when traffic continues, then service remains available without manual intervention.
- **AC-NFR-AVL-002-02:** Given AZ failure simulation on stateless tier, when tested, then failover completes within RTO defined in NFR-BKP-002.

### Priority

**P1**

---

## NFR-AVL-003: Graceful Degradation

### Description

The system SHOULD degrade non-critical features before failing core read paths.

### Requirements

- If email delivery fails, in-app notifications MUST still be created.
- If async report workers are unavailable, synchronous reports within NFR-PER-002 MUST still function.
- If cache is unavailable, system MUST fall back to database queries with acceptable latency increase (≤ 2× baseline p95).

### Acceptance Criteria

- **AC-NFR-AVL-003-01:** Given Redis unavailable, when dashboard is loaded, then data is served from database with increased but bounded latency.
- **AC-NFR-AVL-003-02:** Given email service outage, when critical alert fires, then in-app notification is still created and email failure is logged.

### Priority

**P1**

---

## NFR-AVL-004: Health Checks and Readiness

### Description

All deployable services SHALL expose health endpoints for orchestrator probes.

### Requirements

- Liveness probe MUST verify process responsiveness.
- Readiness probe MUST verify database connectivity and critical dependencies.
- Unready instances MUST be removed from load balancing automatically.

### Acceptance Criteria

- **AC-NFR-AVL-004-01:** Given database connectivity loss, when readiness probe runs, then instance is marked unready and removed from rotation.

### Priority

**P0**

---

# Monitoring

Provide observability for operations, performance validation, and incident response.

---

## NFR-MON-001: Metrics Collection

### Description

The system SHALL emit application and infrastructure metrics compatible with Prometheus.

### Required Metrics

- HTTP request rate, latency (p50/p95/p99), and error rate by endpoint
- Celery queue depth, task success/failure rate, task duration
- Database connection pool utilization
- Cache hit/miss ratio
- Ingestion records processed per minute
- Active threshold alerts count

### Acceptance Criteria

- **AC-NFR-MON-001-01:** Given production deployment, when Prometheus scrapes targets, then all required metric families are present.
- **AC-NFR-MON-001-02:** Given Grafana dashboards, when reviewed, then API latency, error rate, and worker queue depth panels exist.

### Related Requirements

- FR-PLT-003

### Priority

**P0**

---

## NFR-MON-002: Distributed Tracing

### Description

The system SHALL implement distributed tracing via OpenTelemetry across API, workers, and database calls.

### Requirements

- Trace context MUST propagate from API requests to Celery tasks where applicable.
- Traces MUST include correlation IDs linking user requests to background jobs.
- Sampling rate SHOULD default to 10% in production with ability to increase during incidents.

### Acceptance Criteria

- **AC-NFR-MON-002-01:** Given a report generation request triggering async work, when trace is inspected, then API span links to worker span via shared trace ID.

### Priority

**P1**

---

## NFR-MON-003: Structured Logging

### Description

The system SHALL emit structured JSON logs suitable for centralized log aggregation.

### Requirements

- Logs MUST include: timestamp, level, service name, correlation/request ID, user ID (where authenticated), action, outcome.
- Logs MUST NOT contain secrets, full API keys, or full JWT tokens.
- Log levels MUST be configurable per environment.

### Acceptance Criteria

- **AC-NFR-MON-003-01:** Given a sample of production logs, when parsed, then required fields are present and no credential leakage is detected.

### Priority

**P0**

---

## NFR-MON-004: Alerting

### Description

Operational alerts SHALL notify on-call personnel when SLAs or system health thresholds are breached.

### Alert Conditions (minimum)

| Alert | Threshold |
|-------|-----------|
| API error rate | > 1% over 5 minutes |
| API p95 latency | > 3 seconds over 10 minutes |
| Queue depth | > 1,000 tasks for 15 minutes |
| Database connectivity | Any readiness failure |
| Disk/storage | > 85% utilization |
| Uptime budget burn | Projected monthly uptime < 99.5% |

### Acceptance Criteria

- **AC-NFR-MON-004-01:** Given simulated API error spike, when threshold exceeded, then alert fires to configured channel within 5 minutes.

### Priority

**P0**

---

## NFR-MON-005: Business KPI Dashboards

### Description

The system SHOULD expose operational dashboards for business-critical platform metrics.

### Metrics

- Daily active users
- Ingestion success vs. failure rate
- Threshold alerts fired per day
- Report generation volume and async backlog

### Acceptance Criteria

- **AC-NFR-MON-005-01:** Given Grafana business dashboard, when reviewed, then ingestion and alert KPI panels are available to platform operators.

### Priority

**P2**

---

## NFR-MON-006: Synthetic Monitoring

### Description

Production SHOULD run synthetic checks for critical user journeys.

### Checks (minimum)

- Login and JWT issuance
- Dashboard load (authenticated)
- Health endpoint availability

### Acceptance Criteria

- **AC-NFR-MON-006-01:** Given synthetic monitor schedule, when checks run every 5 minutes, then failures trigger operational alerts.

### Priority

**P2**

---

# Auditability

Enable forensic review, compliance validation, and accountability for administrative actions.

---

## NFR-AUD-001: Audit Log Completeness

### Description

The system SHALL record immutable audit logs for security-sensitive and administrative actions.

### Required Events

- Authentication success/failure (privileged roles)
- AI tool create/update/deactivate
- Team create/update/deactivate; member assign/remove
- API credential create/rotate/delete
- Threshold create/update/delete
- File upload preview/reprocess/delete
- Report export (CSV/PDF) by privileged roles
- Retention policy changes

### Log Fields

- Event ID, timestamp (UTC), actor ID, actor role, action, resource type, resource ID, outcome, source IP, correlation ID

### Acceptance Criteria

- **AC-NFR-AUD-001-01:** Given each required event type, when triggered in test, then a corresponding audit record is persisted with all required fields.

### Related Requirements

- FR-PLT-002, FR-RPT-006

### Priority

**P0**

---

## NFR-AUD-002: Audit Log Integrity

### Description

Audit logs SHALL be protected from tampering and unauthorized modification.

### Requirements

- Audit records MUST be append-only; update and delete by application users MUST be prohibited.
- Audit storage SHOULD be segregated from operational tables or protected by restricted DB roles.
- Audit log access MUST be read-only for Auditor role.

### Acceptance Criteria

- **AC-NFR-AUD-002-01:** Given an application user (including Super Admin), when attempting to modify or delete audit records via API, then operation is denied.
- **AC-NFR-AUD-002-02:** Given database role permissions, when reviewed, then application role lacks UPDATE/DELETE on audit tables.

### Priority

**P0**

---

## NFR-AUD-003: Audit Log Retention and Query

### Description

Audit logs SHALL be retained and queryable for compliance review.

### Requirements

- Minimum retention: 24 months (aligned with FR-PLT-004).
- Super Admins and Auditors MUST query audit logs with filters: date range, actor, action type, resource.
- Export of audit logs to CSV MUST be supported for Auditor role.

### Acceptance Criteria

- **AC-NFR-AUD-003-01:** Given audit events over a 24-month window, when queried by an Auditor, then results are returned within 10 seconds for standard filters at reference scale.

### Related Requirements

- FR-PLT-004

### Priority

**P1**

---

## NFR-AUD-004: Correlation and Traceability

### Description

Audit and operational logs SHALL support end-to-end traceability via correlation IDs.

### Requirements

- Each authenticated request MUST propagate a correlation ID through logs, traces, and audit entries where applicable.
- Background jobs MUST inherit correlation ID from triggering request or ingestion batch.

### Acceptance Criteria

- **AC-NFR-AUD-004-01:** Given an administrative action triggering a background job, when logs are searched by correlation ID, then API and worker entries are linked.

### Priority

**P1**

---

# Accessibility

Ensure the web application is usable by people with disabilities for Phase 1 core workflows.

---

## NFR-ACC-001: WCAG Conformance Target

### Description

The web UI SHOULD conform to WCAG 2.1 Level AA for Phase 1 core user journeys.

### Core Journeys

- Login
- Dashboard viewing and date filtering
- Report generation and export
- Administration: tool, team, threshold management
- Notification center

### Acceptance Criteria

- **AC-NFR-ACC-001-01:** Given automated accessibility scan (axe or equivalent) on core pages, when run, then no critical violations remain unresolved.
- **AC-NFR-ACC-001-02:** Given manual keyboard-only navigation of core journeys, when tested, then all interactive elements are reachable and operable.

### Priority

**P1**

---

## NFR-ACC-002: Keyboard and Focus Management

### Description

All interactive UI components SHALL be operable via keyboard with visible focus indicators.

### Requirements

- Modal dialogs MUST trap focus and restore on close.
- Skip navigation link SHOULD be provided to main content.
- Material UI components MUST use accessible patterns without disabling ARIA attributes.

### Acceptance Criteria

- **AC-NFR-ACC-002-01:** Given keyboard-only use of admin forms, when tabbing through fields and submitting, then all actions complete without mouse dependency.

### Priority

**P1**

---

## NFR-ACC-003: Visual Accessibility

### Description

The UI SHALL meet minimum visual accessibility standards.

### Requirements

- Text contrast MUST meet WCAG AA ratios (4.5:1 normal text, 3:1 large text).
- Color MUST NOT be the sole indicator of alert severity; icons or labels MUST accompany Warning/Critical states.
- Charts SHOULD provide data tables or textual summaries as alternates where feasible.

### Acceptance Criteria

- **AC-NFR-ACC-003-01:** Given contrast analysis on primary theme, when measured, then text/background pairs meet WCAG AA.
- **AC-NFR-ACC-003-02:** Given alert severity indicators in dashboard widgets, when rendered, then non-color cues distinguish Warning from Critical.

### Related Requirements

- FR-DSH-006, FR-NTF-001

### Priority

**P1**

---

## NFR-ACC-004: Screen Reader Support

### Description

Core pages SHALL provide meaningful labels and announcements for assistive technologies.

### Requirements

- Form inputs MUST have associated labels.
- Dynamic content updates (notifications, async report completion) SHOULD use ARIA live regions.
- Data tables MUST include header associations.

### Acceptance Criteria

- **AC-NFR-ACC-004-01:** Given screen reader testing on dashboard and reports, when navigated, then landmarks, headings, and table headers are announced correctly.

### Priority

**P2**

---

# Compliance

Meet organizational governance, data protection, and regulatory expectations for a financial and usage monitoring platform.

---

## NFR-CMP-001: Data Retention and Minimization

### Description

The system SHALL retain data according to defined policies and minimize collection to stated purposes.

### Requirements

- Usage data minimum retention: 24 months (FR-PLT-004).
- Retention policies MUST be configurable by Super Admin within allowed bounds.
- Data no longer required MUST be purged or anonymized per retention job schedule.
- Personal data collected MUST be limited to identifiers needed for usage attribution (e.g., email, name).

### Acceptance Criteria

- **AC-NFR-CMP-001-01:** Given default retention configuration, when retention job runs, then data older than 24 months is purged or archived per policy.
- **AC-NFR-CMP-001-02:** Given attempt to set retention below 24 months without documented exception, when saved, then configuration is rejected.

### Related Requirements

- FR-PLT-004

### Priority

**P0**

---

## NFR-CMP-002: Data Subject Access and Deletion

### Description

The system SHOULD support organizational processes for user data access and deletion requests.

### Requirements

- Super Admin MUST be able to export all data associated with a user identifier.
- User deactivation MUST revoke access immediately; historical usage attribution MAY be anonymized rather than deleted to preserve financial records.
- Deletion/anonymization actions MUST be audit-logged.

### Acceptance Criteria

- **AC-NFR-CMP-002-01:** Given a user data export request, when processed by Super Admin, then export includes usage records and profile data within 10 business days (process SLA; automation Phase 2).

### Priority

**P2**

---

## NFR-CMP-003: Regulatory Alignment

### Description

The platform SHOULD align controls with common enterprise compliance frameworks applicable to SaaS financial monitoring tools.

### Framework Mapping (informative)

| Control Area | Alignment |
|--------------|-----------|
| Access control | SOC 2 CC6.1 – logical access |
| Encryption | SOC 2 CC6.7 – transmission; CC6.1 – storage |
| Monitoring | SOC 2 CC7.2 – anomaly detection |
| Change management | SOC 2 CC8.1 – via CI/CD and audit logs |

### Requirements

- Compliance evidence (audit logs, access reviews, encryption configs) MUST be exportable for auditor review.
- Phase 1 does not require formal certification; controls MUST be implementable for future SOC 2 audit.

### Acceptance Criteria

- **AC-NFR-CMP-003-01:** Given compliance evidence checklist, when mapped to implemented controls, then no P0 control gap remains undocumented.

### Priority

**P1**

---

## NFR-CMP-004: Privacy and Consent for Notifications

### Description

Email and in-app notifications SHALL comply with organizational communication policies.

### Requirements

- Users MUST be able to opt out of non-critical email notifications where role permits.
- Critical security and Critical severity cost alerts MAY be mandatory and not opt-outable.
- Notification content MUST NOT include full credentials or excessive personal data.

### Acceptance Criteria

- **AC-NFR-CMP-004-01:** Given a user disabling non-critical email alerts, when Warning threshold fires, then email is suppressed but in-app notification is still created.

### Related Requirements

- FR-NTF-002

### Priority

**P1**

---

## NFR-CMP-005: Geographic Data Residency

### Description

Production data SHOULD be stored in customer-approved geographic regions.

### Requirements

- PostgreSQL, local storage volumes, and backup storage MUST reside on infrastructure in the customer-approved geography (Docker host location / data center).
- Cross-site replication MUST be documented and opt-in (Phase 2).

### Acceptance Criteria

- **AC-NFR-CMP-005-01:** Given deployment configuration, when infrastructure is reviewed, then primary data stores reside in the designated region.

### Priority

**P2**

---

# Backup and Recovery

Protect against data loss and enable recovery within defined objectives.

---

## NFR-BKP-001: Database Backup Policy

### Description

PostgreSQL production data SHALL be backed up on a defined schedule with verified restorability.

### Targets

| Parameter | Target |
|-----------|--------|
| Backup frequency | Daily full; continuous WAL/archive where supported |
| Retention | Minimum 30 days online; 24-month archive optional |
| Backup encryption | AES-256 or provider-managed equivalent |
| Restore test frequency | Quarterly |

### Acceptance Criteria

- **AC-NFR-BKP-001-01:** Given backup job history, when reviewed for 30 days, then daily successful backups exist with no gaps > 24 hours.
- **AC-NFR-BKP-001-02:** Given quarterly restore drill, when executed, then database restores to a test environment successfully within RTO.

### Priority

**P0**

---

## NFR-BKP-002: Recovery Time and Point Objectives

### Description

The platform SHALL define and meet RTO/RPO targets for disaster recovery.

### Targets

| Parameter | Target |
|-----------|--------|
| RPO (Recovery Point Objective) | ≤ 1 hour |
| RTO (Recovery Time Objective) | ≤ 4 hours for full platform restore |
| Single-component failure (API pod) | ≤ 5 minutes automatic recovery |

### Acceptance Criteria

- **AC-NFR-BKP-002-01:** Given disaster recovery tabletop or drill, when full restore is executed, then platform is operational within 4 hours using latest valid backup.
- **AC-NFR-BKP-002-02:** Given measured data loss during simulated failure, when compared to RPO, then loss is ≤ 1 hour of transactions.

### Priority

**P0**

---

## NFR-BKP-003: Object Storage Durability

### Description

Uploaded files and generated report artifacts SHALL be protected against loss on local storage.

### Requirements

- `storage_data` and `backups_data` volumes MUST reside on durable host disks (not ephemeral container layers).
- Weekly tarball backups of `storage_data` SHOULD be copied to off-host storage (rsync/NAS).
- Deleted uploads (FR-ING-002) MUST remove files from local storage within 30 days of soft-delete confirmation.

### Acceptance Criteria

- **AC-NFR-BKP-003-01:** Given backup configuration, when reviewed, then weekly storage tarballs exist on `backups_data` or off-host copy with verifiable restore.

### Related Requirements

- FR-ING-001, FR-ING-002, FR-RPT-007

### Priority

**P1**

---

## NFR-BKP-004: Configuration and Secrets Backup

### Description

Infrastructure configuration and non-secret metadata SHALL be recoverable from version control and IaC.

### Requirements

- Application configuration templates MUST be stored in Git (excluding secrets).
- Kubernetes manifests or ECS task definitions MUST be version-controlled.
- Secrets MUST be recoverable from secrets manager with documented rotation procedure.

### Acceptance Criteria

- **AC-NFR-BKP-004-01:** Given loss of application deployment config, when redeployed from Git and secrets manager, then platform reaches healthy state without manual reconstruction of non-secret config.

### Priority

**P1**

---

## NFR-BKP-005: Disaster Recovery Runbook

### Description

Operations SHALL maintain a documented disaster recovery runbook tested at least annually.

### Runbook Contents (minimum)

- Contact tree and escalation
- Backup locations and restore procedures
- RTO/RPO targets
- Failover steps for database and stateless tiers
- Communication templates for stakeholders

### Acceptance Criteria

- **AC-NFR-BKP-005-01:** Given DR runbook, when annual test is conducted, then RTO/RPO results are recorded and gaps remediated within 90 days.

### Priority

**P1**

---

# Localization

Support international deployment with language, locale, and formatting considerations.

---

## NFR-LOC-001: Phase 1 Language Support

### Description

Phase 1 SHALL ship with English (en-US) as the default and sole UI language.

### Requirements

- All user-facing strings MUST be externalized (i18n-ready) even if only English is shipped.
- No hardcoded user-facing text in components without translation keys.
- Date, number, and currency formatting MUST use locale-aware libraries (default: en-US).

### Acceptance Criteria

- **AC-NFR-LOC-001-01:** Given codebase review, when UI strings are scanned, then user-facing text uses i18n resource keys.
- **AC-NFR-LOC-001-02:** Given en-US locale, when dates and currency display in dashboards/reports, then formatting follows US conventions.

### Priority

**P0** (i18n-ready); **P2** (additional languages)

---

## NFR-LOC-002: Time Zone Handling

### Description

The system SHALL store timestamps in UTC and display dates in the user's or organization's configured time zone.

### Requirements

- All persisted timestamps MUST be UTC.
- Organization default time zone MUST be configurable by Super Admin.
- Reports and dashboards MUST respect selected date filters in the configured time zone.
- Scheduled reports (FR-RPT-007) MUST execute according to organization time zone.

### Acceptance Criteria

- **AC-NFR-LOC-002-01:** Given an organization time zone of `America/New_York`, when a user filters dashboard to a calendar day, then boundaries align to that zone.
- **AC-NFR-LOC-002-02:** Given stored usage events, when retrieved, then API returns UTC with display conversion in UI.

### Priority

**P1**

---

## NFR-LOC-003: Multi-Language Expansion (Phase 2)

### Description

The platform SHOULD support additional UI languages post-MVP without architectural rework.

### Requirements

- Translation files MUST support namespace organization by module.
- RTL layout support SHOULD be evaluated when Arabic or Hebrew is added.
- Locale MUST affect number/date formatting but MUST NOT alter RBAC or calculation logic.

### Planned Languages (Phase 2 candidates)

- English (en-US) — Phase 1 default
- Additional languages per customer demand

### Acceptance Criteria

- **AC-NFR-LOC-003-01:** Given a new locale file added, when language selector is enabled, then UI renders translated strings without code changes to components.

### Priority

**P2**

---

# Verification and Evidence

Each NFR MUST be verifiable before Phase 1 release. Recommended evidence mapping:

| Category | Evidence Type |
|----------|---------------|
| Security | Pen test summary, dependency scan, encryption config review |
| Performance | Load test report (k6/Locust) with p95 metrics |
| Scalability | Capacity test at reference scale |
| Availability | 30-day uptime report, HA failover test |
| Monitoring | Grafana dashboard screenshots, alert test records |
| Auditability | Audit log sample export, tamper test results |
| Accessibility | axe scan report, keyboard walkthrough checklist |
| Compliance | Control matrix vs. NFR-CMP requirements |
| Backup and Recovery | Restore drill report with RTO/RPO |
| Localization | i18n key coverage report, time zone test cases |

---

# Related Documents

- [Functional Requirements README](./README.md)
- [07-platform-security.md](./07-platform-security.md) — FR-PLT-001 through FR-PLT-004
- [project.md](../project.md) — product specification
- [deployment.md](../specifications/deployment.md) — Docker Compose deployment
- [ADR-013](../decisions/ADR-013-docker-compose-local-storage.md) — Phase 1 deployment decision
