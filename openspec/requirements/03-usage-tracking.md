# Usage Tracking — Functional Requirements

Module 3: Team-level usage measurement, cost calculation, and data ingestion.

---

## FR-USG-001: Team-Level Usage Tracking

### Description

The system SHALL track team-level AI consumption including input tokens, output tokens, total tokens, package utilization, estimated costs, and overage costs so that usage can be monitored and reported accurately.

### Business Rules

- Each usage record MUST be attributable to a tool, team, user (where available), and timestamp.
- Cost estimation MUST use the active pricing configuration for the tool at ingestion time unless a reprocessing job explicitly recalculates historical records.
- Package utilization MUST be computed as consumed allowance divided by configured package allowance, expressed as a percentage.
- Overage costs MUST apply when consumption exceeds package allowance per tool pricing rules.
- Usage data MUST be retained for a minimum of 24 months (FR-PLT-004).

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-USG-001-01 | SA | As a Super Admin, I want team usage aggregated automatically so that dashboards and reports reflect current consumption. |
| US-USG-001-02 | TA | As a Team Admin, I want accurate package utilization for my team so that I know when we approach limits. |
| US-USG-001-03 | FV | As a Finance Viewer, I want estimated and overage costs per team so that I can oversee spend. |

### Acceptance Criteria

- **AC-USG-001-01:** Given ingested usage events, when aggregation runs, then input, output, and total tokens are stored per team, tool, and user.
- **AC-USG-001-02:** Given a tool with package allowance configured, when usage exceeds the allowance, then overage cost is calculated and stored separately from base estimated cost.
- **AC-USG-001-03:** Given usage records older than 24 months and default retention policy, when retention job runs, then data is purged or archived per FR-PLT-004 configuration.
- **AC-USG-001-04:** Given aggregated team usage, when dashboard or report queries run, then figures match the underlying stored records within rounding tolerance.

### Dependencies

- FR-ADM-001 (AI Tool Management)
- FR-ADM-002 (Team Management)
- FR-USG-002 (Usage Data Ingestion)
- FR-PLT-004 (Data Retention Policy)

### Priority

**P0**

---

## FR-USG-002: Usage Data Ingestion

### Description

The system SHALL ingest usage data through batch processing and near real-time synchronization so that team-level metrics stay current without manual spreadsheet consolidation.

### Business Rules

- Batch ingestion MUST support scheduled and on-demand processing via background jobs (Celery).
- Near real-time synchronization MUST update aggregated metrics within a defined SLA (target: under 5 minutes from event receipt for MVP).
- Ingested records MUST validate tool, team, and user references; invalid references MUST be rejected or quarantined with error detail.
- Duplicate events MUST be detected using vendor event identifiers or deterministic idempotency keys where available.
- API-based ingestion MUST authenticate via FR-PLT-001; vendor credential usage MUST follow FR-ADM-003.
- Scheduled vendor API collection MUST follow FR-ING-004 (hourly or daily collector jobs feeding this pipeline).

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-USG-002-01 | SA | As a Super Admin, I want usage synced from vendor APIs so that data stays current without manual uploads. |
| US-USG-002-02 | SA | As a Super Admin, I want batch ingestion for large datasets so that historical data can be loaded efficiently. |
| US-USG-002-03 | TA | As a Team Admin, I want ingestion errors reported clearly so that I can fix configuration issues. |

### Acceptance Criteria

- **AC-USG-002-01:** Given valid usage payloads, when batch ingestion is triggered, then records are processed asynchronously and aggregation updates upon job completion.
- **AC-USG-002-02:** Given near real-time usage events, when received by the ingestion endpoint, then team-level aggregates reflect new usage within the near real-time SLA.
- **AC-USG-002-03:** Given a duplicate event with the same idempotency key, when ingestion runs again, then the duplicate is ignored and no double-counting occurs.
- **AC-USG-002-04:** Given invalid team or tool references, when ingestion is attempted, then the record is rejected or quarantined with a retrievable error reason.

### Dependencies

- FR-ADM-001 (AI Tool Management)
- FR-ADM-002 (Team Management)
- FR-ADM-003 (API Key Management)
- FR-USG-001 (Team-Level Usage Tracking)
- FR-ING-001 (File Upload Ingestion) — parallel ingestion path for Phase 1

### Priority

**P0**
