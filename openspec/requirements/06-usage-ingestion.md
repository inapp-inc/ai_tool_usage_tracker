# Individual Usage Monitoring — Functional Requirements

Module 6: File-based usage ingestion and individual consumption views (Phase 1 MVP).

---

## FR-ING-001: File Upload Ingestion

### Description

The system SHALL ingest individual and team usage data from uploaded vendor export files in CSV, JSON, and XLSX formats so that Phase 1 tracking does not require live API integrations.

### Business Rules

- Supported formats MUST include CSV, JSON, and XLSX.
- Maximum upload size MUST be 50 MB per file.
- System MUST auto-detect file format where possible based on extension and content sniffing.
- Supported vendor export parsers MUST include OpenAI, Anthropic, Azure AI, and Cursor; additional providers MUST be configurable via mapping templates.
- Uploads MUST be stored securely (e.g., AWS S3) with metadata linking uploader, team, timestamp, and processing status.
- Only Super Admins and Team Admins MAY upload files for teams they administer.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-ING-001-01 | SA / TA | As an administrator, I want to upload vendor usage exports so that individual usage is captured without API integration. |
| US-ING-001-02 | TA | As a Team Admin, I want the system to auto-detect file format so that I do not need to specify parser details manually. |
| US-ING-001-03 | SA | As a Super Admin, I want configurable parsers for additional vendors so that new tools can be onboarded. |

### Acceptance Criteria

- **AC-ING-001-01:** Given a valid CSV, JSON, or XLSX vendor export under 50 MB, when uploaded by an authorized user, then the file is stored and queued for parsing.
- **AC-ING-001-02:** Given a supported vendor format, when parsing runs, then usage records are extracted and passed to FR-USG-001 aggregation pipeline.
- **AC-ING-001-03:** Given a file exceeding 50 MB, when upload is attempted, then the system rejects the upload with a clear size limit error.
- **AC-ING-001-04:** Given an unsupported or corrupt file, when parsing runs, then the upload is marked failed with parse error details visible to the uploader.

### Dependencies

- FR-ADM-001 (AI Tool Management)
- FR-ADM-002 (Team Management)
- FR-USG-001 (Team-Level Usage Tracking)
- FR-USG-002 (Usage Data Ingestion)
- FR-PLT-001 (Authentication and RBAC)

### Priority

**P0**

---

## FR-ING-002: Import Preview and Reprocessing

### Description

The system SHALL allow administrators to preview imports, match users by email, flag unmatched users, reprocess uploads, and delete uploads so that data quality is controlled before final ingestion.

### Business Rules

- User matching MUST use email as the primary identifier; unmatched records MUST be flagged for administrator review.
- Preview MUST show parsed row counts, matched users, unmatched users, and sample records before commit where workflow supports staged import.
- Reprocess MUST re-run parsing and matching without requiring re-upload if source file is retained.
- Delete MUST remove upload metadata and associated uncommitted staging data; committed usage already aggregated MUST require explicit rollback or reprocessing policy defined by administrators.
- All preview, reprocess, and delete actions MUST be audit-logged.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-ING-002-01 | SA / TA | As an administrator, I want to preview an import so that I can verify data before it affects reports. |
| US-ING-002-02 | TA | As a Team Admin, I want unmatched users flagged so that I can resolve identity mapping issues. |
| US-ING-002-03 | SA / TA | As an administrator, I want to reprocess or delete an upload so that I can correct ingestion errors. |

### Acceptance Criteria

- **AC-ING-002-01:** Given a parsed upload, when preview is requested, then matched count, unmatched count, and representative sample rows are displayed.
- **AC-ING-002-02:** Given records with emails not matching platform users, when matching runs, then unmatched records are flagged with email and row reference.
- **AC-ING-002-03:** Given a failed or corrected mapping configuration, when reprocess is triggered, then parsing and matching rerun against the stored file.
- **AC-ING-002-04:** Given an upload delete request by an authorized user, when confirmed, then upload record and staging data are removed and action is audit-logged.

### Dependencies

- FR-ING-001 (File Upload Ingestion)
- FR-PLT-002 (Audit Logging)
- FR-ADM-002 (Team Management)

### Priority

**P0**

---

## FR-ING-003: Individual Usage Views

### Description

The system SHALL provide individual usage views showing total consumption, usage by tool, trends, and team comparisons so team members and administrators can monitor personal adoption.

### Business Rules

- Individual views MUST include total usage, breakdown by tool, trend charts, and comparison to team averages where team membership exists.
- Team Members MUST view only their own individual data by default.
- Team Admins MAY view individual usage for members of their teams; Super Admins MAY view all users.
- Data MUST originate from ingested usage records (FR-ING-001, FR-USG-002) and align with FR-DSH-008 My Usage widget.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-ING-003-01 | TM | As a team member, I want to see my usage by tool and over time so that I understand my AI consumption patterns. |
| US-ING-003-02 | TA | As a Team Admin, I want to compare a member's usage to team averages so that I can coach on efficient tool use. |

### Acceptance Criteria

- **AC-ING-003-01:** Given a team member with ingested usage, when they open individual usage view, then total usage, per-tool breakdown, and trend chart display for the selected period.
- **AC-ING-003-02:** Given team membership, when individual view loads, then team average comparison is shown alongside personal metrics.
- **AC-ING-003-03:** Given a Team Admin viewing a team member, when authorized, then that member's individual view is accessible; unauthorized members return access denied.

### Dependencies

- FR-ING-001 (File Upload Ingestion)
- FR-USG-001 (Team-Level Usage Tracking)
- FR-DSH-008 (My Usage Widget)
- FR-PLT-001 (Authentication and RBAC)

### Priority

**P0**

---

## FR-ING-004: AI Tool Usage Collector (API Sync)

### Description

The system SHALL collect usage data directly from vendor AI tool APIs using configured credentials, on a schedule of **hourly** or **daily** per integration, so that usage stays current without manual file uploads.

### Business Rules

- Each collector integration MUST be linked to an AI tool (FR-ADM-001), optional team scope, and a vendor API credential (FR-ADM-003).
- Collection schedule MUST be configurable as `hourly` or `daily` per integration; default `daily`.
- The frontend MUST support a **provider-managed connection** flow: user selects vendor/provider, submits an API token (or selects an existing stored credential), and configures schedule.
- Super Admins MAY configure collectors for any org tool/team; Team Admins MAY configure collectors only for tools and teams they administer.
- Collector runs MUST execute via background jobs (Celery) on the `ingestion` queue; manual on-demand collection MAY be triggered from the UI.
- Fetched usage MUST normalize to the canonical usage event format and feed the FR-USG-002 ingestion pipeline (idempotent, aggregate refresh).
- Vendor API tokens MUST never be returned in API responses after initial connect; only masked credential references.
- Failed collection runs MUST record error details without logging full secrets; consecutive failures SHOULD surface an in-app notification to administrators.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-ING-004-01 | SA | As a Super Admin, I want to connect an AI provider with an API token and schedule automatic collection so that usage syncs without manual uploads. |
| US-ING-004-02 | TA | As a Team Admin, I want to configure hourly collection for my team's OpenAI integration so that dashboards stay near real-time. |
| US-ING-004-03 | SA | As a Super Admin, I want to trigger an on-demand collection run so that I can refresh data immediately after configuration changes. |
| US-ING-004-04 | SA / TA | As an administrator, I want collection errors visible in the UI so that I can fix token or scope issues. |

### Acceptance Criteria

- **AC-ING-004-01:** Given a valid provider, API token, and tool mapping, when an administrator completes the connect flow, then a collector configuration is persisted with encrypted credential reference and selected schedule.
- **AC-ING-004-02:** Given an active collector with `hourly` schedule, when the scheduled job runs, then usage is fetched from the vendor API and ingested without duplicate events for the same vendor event id.
- **AC-ING-004-03:** Given an active collector with `daily` schedule, when the daily Beat task fires, then usage for the prior period is collected and aggregates refresh within the near real-time SLA (NFR-PER-004).
- **AC-ING-004-04:** Given an invalid or revoked API token, when collection runs, then the run fails with a retrievable error status and no secret values appear in logs or API responses.
- **AC-ING-004-05:** Given a Team Admin without access to team T, when they attempt to configure a collector for team T, then the system returns 403 Forbidden.

### Dependencies

- FR-ADM-001 (AI Tool Management)
- FR-ADM-002 (Team Management)
- FR-ADM-003 (API Key Management)
- FR-USG-001 (Team-Level Usage Tracking)
- FR-USG-002 (Usage Data Ingestion)
- FR-PLT-001 (Authentication and RBAC)
- FR-PLT-002 (Audit Logging)

### Priority

**P0**

### Related OpenSpec Change

- [usage-collector-backend](../changes/usage-collector-backend/proposal.md)
