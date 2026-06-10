# Reporting — Functional Requirements

Module 4: Operational and financial reports with export, scheduling, and async generation.

---

## FR-RPT-001: Tool Usage Summary Report

### Description

The system SHALL generate a Tool Usage Summary report filterable by period, team, and tool so stakeholders can analyze consumption by AI tool.

### Business Rules

- Report MUST include token counts (input, output, total) and usage share per tool for the selected filters.
- Filters MUST support period, team, and tool; multiple teams or tools MAY be selected where RBAC permits.
- Report data MUST match dashboard and usage tracking aggregates (FR-USG-001).

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-RPT-001-01 | SA / FV / TA / AU | As a stakeholder, I want a tool usage summary report so that I can review consumption by vendor platform. |

### Acceptance Criteria

- **AC-RPT-001-01:** Given valid filters, when the report is generated, then each selected tool shows usage metrics for the period within 10 seconds for standard queries.
- **AC-RPT-001-02:** Given a Team Admin filter, when the report runs, then only authorized teams appear in results.

### Dependencies

- FR-USG-001 (Team-Level Usage Tracking)
- FR-PLT-001 (Authentication and RBAC)
- FR-RPT-007 (Report Delivery Features)

### Priority

**P0**

---

## FR-RPT-002: Team Usage Report

### Description

The system SHALL generate a Team Usage report filterable by period and team so administrators can compare team consumption.

### Business Rules

- Report MUST include per-team token totals, package utilization, and estimated costs.
- Team filter MUST respect RBAC scope.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-RPT-002-01 | SA / FV / TA | As an administrator, I want a team usage report so that I can review team-level consumption trends. |

### Acceptance Criteria

- **AC-RPT-002-01:** Given period and team filters, when the report is generated, then each team row includes tokens, utilization, and cost for the period.
- **AC-RPT-002-02:** Given export via FR-RPT-007, when CSV or PDF is requested, then output matches on-screen filtered data.

### Dependencies

- FR-ADM-002 (Team Management)
- FR-USG-001 (Team-Level Usage Tracking)
- FR-RPT-007 (Report Delivery Features)

### Priority

**P0**

---

## FR-RPT-003: Cost Report

### Description

The system SHALL generate a Cost report filterable by period, team, and tool so finance can monitor spend, allowances, and overages.

### Business Rules

- Report MUST separate actual spend, package allowance consumed, and overage costs.
- Cost calculations MUST align with FR-DSH-002 and FR-USG-001.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-RPT-003-01 | SA / FV | As a finance viewer, I want a cost report so that I can oversee AI expenditure by team and tool. |

### Acceptance Criteria

- **AC-RPT-003-01:** Given filters for period, team, and tool, when the cost report runs, then spend, allowance, and overage columns are populated accurately.
- **AC-RPT-003-02:** Given Finance Viewer role, when accessing the report, then user has read-only access without modification capabilities.

### Dependencies

- FR-ADM-001 (AI Tool Management)
- FR-USG-001 (Team-Level Usage Tracking)
- FR-RPT-007 (Report Delivery Features)

### Priority

**P0**

---

## FR-RPT-004: User Usage Report

### Description

The system SHALL generate a User Usage report filterable by period, team, and user so administrators can review individual consumption.

### Business Rules

- Report MUST include per-user token totals and estimated costs within the selected team and period.
- Team Members MUST access only their own user row unless elevated by RBAC.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-RPT-004-01 | SA / TA | As an administrator, I want a user usage report so that I can identify individuals with high consumption. |
| US-RPT-004-02 | TM | As a team member, I want to run a report for my own usage so that I can track personal consumption. |

### Acceptance Criteria

- **AC-RPT-004-01:** Given period, team, and user filters, when the report generates, then each user row shows usage and cost for the authorized scope.
- **AC-RPT-004-02:** Given a Team Member, when they request the report without user filter, then only their personal data is returned.

### Dependencies

- FR-ING-003 (Individual Usage Views)
- FR-USG-001 (Team-Level Usage Tracking)
- FR-RPT-007 (Report Delivery Features)

### Priority

**P0**

---

## FR-RPT-005: Alert History Report

### Description

The system SHALL generate an Alert History report filterable by period, team, tool, and alert type so stakeholders can audit threshold events.

### Business Rules

- Report MUST include alert type, severity, threshold, actual value, timestamp, and resolution status.
- Alert types MUST map to threshold configurations from FR-ADM-004.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-RPT-005-01 | SA / TA / AU | As an administrator or auditor, I want alert history so that I can review past threshold breaches. |

### Acceptance Criteria

- **AC-RPT-005-01:** Given filters for period, team, tool, and alert type, when the report runs, then matching alert events are listed chronologically.
- **AC-RPT-005-02:** Given Auditor role, when accessing the report, then access is read-only across authorized organizational scope.

### Dependencies

- FR-ADM-004 (Threshold Management)
- FR-NTF-003 (Threshold Alert Triggering)
- FR-RPT-007 (Report Delivery Features)

### Priority

**P1**

---

## FR-RPT-006: API Key Activity Report

### Description

The system SHALL generate an API Key Activity report filterable by period, team, and tool so administrators can audit credential usage and rotation events.

### Business Rules

- Report MUST include credential scope (org/team), environment, rotation events, and expiration status changes.
- Full credential secrets MUST NEVER appear in the report.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-RPT-006-01 | SA / AU | As a Super Admin or auditor, I want API key activity history so that I can verify secure credential lifecycle management. |

### Acceptance Criteria

- **AC-RPT-006-01:** Given filters for period, team, and tool, when the report runs, then credential lifecycle events are listed without exposing secret values.
- **AC-RPT-006-02:** Given rotation or expiration events, when included in the period, then actor and timestamp are recorded.

### Dependencies

- FR-ADM-003 (API Key Management)
- FR-PLT-002 (Audit Logging)
- FR-RPT-007 (Report Delivery Features)

### Priority

**P1**

---

## FR-RPT-007: Report Delivery Features

### Description

The system SHALL support CSV and PDF export, scheduled report generation, email delivery, and asynchronous processing for large reports.

### Business Rules

- Standard reports MUST generate within 10 seconds; larger reports MUST queue for async generation with user notification on completion.
- Scheduled reports MUST support recurring schedules (daily, weekly, monthly) with email delivery to authorized recipients.
- Exported files MUST contain only data the requester is authorized to view.
- Async jobs MUST be processed via background workers (Celery) with retrievable job status.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-RPT-007-01 | SA / FV / TA / AU | As a user, I want to export reports to CSV or PDF so that I can archive or share them. |
| US-RPT-007-02 | SA / FV | As a finance stakeholder, I want scheduled cost reports emailed to me so that I receive regular updates without manual action. |
| US-RPT-007-03 | SA | As a Super Admin, I want large reports generated asynchronously so that the UI remains responsive. |

### Acceptance Criteria

- **AC-RPT-007-01:** Given a standard report query, when export to CSV or PDF is requested, then the file downloads within 10 seconds.
- **AC-RPT-007-02:** Given a scheduled report configuration, when the schedule triggers, then the report is generated and emailed to configured recipients with RBAC-validated content.
- **AC-RPT-007-03:** Given a report exceeding standard performance thresholds, when generation is requested, then the job is queued, a job ID is returned, and the user is notified when complete.
- **AC-RPT-007-04:** Given async report completion, when the user downloads the result, then content matches the requested filters and format.

### Dependencies

- FR-NTF-001 (Notification Center)
- FR-NTF-002 (Email Notifications)
- FR-PLT-001 (Authentication and RBAC)
- All report features FR-RPT-001 through FR-RPT-006

### Priority

**P0** (CSV/PDF/async); **P1** (scheduled email delivery)
