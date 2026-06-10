# Dashboards — Functional Requirements

Module 2: Unified dashboards and widgets for usage, cost, alerts, and trends.

---

## FR-DSH-001: Total Token Usage Widget

### Description

The dashboard SHALL display aggregate token consumption and current-period totals so stakeholders can monitor overall AI resource usage at a glance.

### Business Rules

- Totals MUST include input tokens, output tokens, and combined total tokens.
- Displayed period MUST respect the dashboard date filter (FR-DSH-009).
- Role-based data scope MUST apply: Team Members see only personal totals; Team Admins see team scope; Super Admins and Finance Viewers see organization scope per RBAC.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-DSH-001-01 | SA / FV / TA | As an administrator or finance viewer, I want to see organization or team token totals so that I understand overall consumption. |
| US-DSH-001-02 | TM | As a team member, I want to see my personal token totals so that I can monitor my own usage. |

### Acceptance Criteria

- **AC-DSH-001-01:** Given a dashboard with default date range, when the page loads, then aggregate input, output, and total token counts for the authorized scope are displayed within 3 seconds.
- **AC-DSH-001-02:** Given a changed date filter, when applied, then token totals recalculate for the selected period only.

### Dependencies

- FR-PLT-001 (Authentication and RBAC)
- FR-USG-001 (Team-Level Usage Tracking)
- FR-DSH-009 (Dashboard Common Features)

### Priority

**P0**

---

## FR-DSH-002: Cost Overview Widget

### Description

The dashboard SHALL display actual spend, package allowance utilization, and overage costs so finance and administrators can monitor financial impact.

### Business Rules

- Cost figures MUST be derived from tool pricing configuration (FR-ADM-001) and recorded usage (FR-USG-001).
- Package allowance MUST show consumed vs. allocated amounts where applicable.
- Overage costs MUST be calculated separately when usage exceeds package limits.
- Finance Viewers MUST have read-only access to cost data within their authorized scope.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-DSH-002-01 | SA / FV | As a finance stakeholder, I want to see actual spend versus package allowance so that I can identify budget risk early. |
| US-DSH-002-02 | TA | As a Team Admin, I want to see my team's cost breakdown including overages so that I can take corrective action. |

### Acceptance Criteria

- **AC-DSH-002-01:** Given usage and pricing data for the selected period, when the Cost Overview widget loads, then actual spend, allowance, and overage amounts are displayed consistently with reporting (FR-RPT-003).
- **AC-DSH-002-02:** Given a tool with no package allowance configured, when costs are displayed, then only actual spend is shown and overage is zero or not applicable.

### Dependencies

- FR-ADM-001 (AI Tool Management)
- FR-USG-001 (Team-Level Usage Tracking)
- FR-DSH-009 (Dashboard Common Features)

### Priority

**P0**

---

## FR-DSH-003: Usage by Tool Widget

### Description

The dashboard SHALL display consumption broken down by AI tool with comparative analysis so users can identify which tools drive the most usage.

### Business Rules

- Inactive tools with historical usage in the selected period MUST still appear in breakdowns.
- Comparison MUST support at minimum relative share (percentage) and absolute token or cost values.
- Data MUST be scoped per user role.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-DSH-003-01 | SA / FV | As an administrator, I want to compare usage across AI tools so that I can prioritize vendor negotiations. |

### Acceptance Criteria

- **AC-DSH-003-01:** Given multiple active tools with usage in the period, when the widget renders, then each tool shows consumption metrics and comparative share.
- **AC-DSH-003-02:** Given drill-down is enabled (FR-DSH-009), when a user selects a tool segment, then detailed usage for that tool is navigable.

### Dependencies

- FR-ADM-001 (AI Tool Management)
- FR-USG-001 (Team-Level Usage Tracking)
- FR-DSH-009 (Dashboard Common Features)

### Priority

**P0**

---

## FR-DSH-004: Usage by Team Widget

### Description

The dashboard SHALL display team-level consumption comparisons so administrators can identify high-usage teams.

### Business Rules

- Team comparisons MUST respect RBAC; Team Admins see only their teams unless granted broader access.
- Deactivated teams with usage in the selected period MUST appear in historical comparisons.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-DSH-004-01 | SA / FV | As an administrator, I want to compare AI usage across teams so that I can allocate budgets fairly. |
| US-DSH-004-02 | TA | As a Team Admin, I want to see how my team compares to others where permitted so that I understand relative consumption. |

### Acceptance Criteria

- **AC-DSH-004-01:** Given organization-wide access, when the widget loads, then teams are ranked or charted by consumption for the selected period.
- **AC-DSH-004-02:** Given a Team Admin with single-team access, when the widget loads, then only authorized team data is shown.

### Dependencies

- FR-ADM-002 (Team Management)
- FR-USG-001 (Team-Level Usage Tracking)
- FR-DSH-009 (Dashboard Common Features)

### Priority

**P0**

---

## FR-DSH-005: Top Consumers Widget

### Description

The dashboard SHALL display ranked lists of top-consuming teams and users so stakeholders can focus on outliers.

### Business Rules

- Default ranking MUST be by total tokens or cost (configurable display; default total tokens).
- Minimum top-N display SHOULD default to 10 entries with pagination or expand option.
- Personal identifiable information MUST be limited to users within the viewer's authorized scope.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-DSH-005-01 | SA / TA | As an administrator, I want to see top-consuming users and teams so that I can address excessive usage. |

### Acceptance Criteria

- **AC-DSH-005-01:** Given usage data exists, when the widget loads, then top teams and top users lists are populated in descending order by consumption.
- **AC-DSH-005-02:** Given insufficient data (fewer than N entities), when the widget loads, then all available entities are shown without error.

### Dependencies

- FR-USG-001 (Team-Level Usage Tracking)
- FR-ING-003 (Individual Usage Views)
- FR-DSH-009 (Dashboard Common Features)

### Priority

**P1**

---

## FR-DSH-006: Alert Status Widget

### Description

The dashboard SHALL display active alerts and threshold breaches so administrators can respond to usage or cost exceptions promptly.

### Business Rules

- Active alerts MUST reflect unresolved threshold breaches from FR-ADM-004 and FR-NTF-003.
- Alerts MUST show severity (Warning or Critical) and affected tool, team, or user.
- Acknowledged alerts MAY remain visible in history but MUST not count as active unless re-triggered.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-DSH-006-01 | SA / TA | As an administrator, I want to see active threshold breaches on the dashboard so that I can act before costs escalate. |

### Acceptance Criteria

- **AC-DSH-006-01:** Given active threshold breaches, when the dashboard loads, then each breach appears with severity, scope, and current value versus threshold.
- **AC-DSH-006-02:** Given no active alerts, when the widget loads, then a clear empty state is shown.

### Dependencies

- FR-ADM-004 (Threshold Management)
- FR-NTF-003 (Threshold Alert Triggering)
- FR-DSH-009 (Dashboard Common Features)

### Priority

**P0**

---

## FR-DSH-007: Trend Analysis Widget

### Description

The dashboard SHALL display daily, weekly, and monthly usage trends so stakeholders can identify patterns and forecast demand.

### Business Rules

- Trend granularity MUST support daily, weekly, and monthly views.
- Trend data MUST align with the selected date filter and authorized scope.
- Missing data points MUST be represented as zero or explicitly marked as no data, not omitted silently.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-DSH-007-01 | SA / FV / TA | As a stakeholder, I want to view usage trends over time so that I can understand growth patterns. |

### Acceptance Criteria

- **AC-DSH-007-01:** Given historical usage for the selected range, when the user switches between daily, weekly, and monthly granularity, then the chart updates without full page reload.
- **AC-DSH-007-02:** Given a date range spanning multiple months, when monthly view is selected, then data is aggregated correctly by calendar month.

### Dependencies

- FR-USG-001 (Team-Level Usage Tracking)
- FR-DSH-009 (Dashboard Common Features)

### Priority

**P1**

---

## FR-DSH-008: My Usage Widget

### Description

The dashboard SHALL provide team members with a personal consumption summary including total usage and breakdown by tool.

### Business Rules

- Widget MUST show only the authenticated user's usage unless viewed by an administrator with explicit user scope.
- Data MUST include totals and trends consistent with FR-ING-003 individual views.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-DSH-008-01 | TM | As a team member, I want a personal usage summary on my dashboard so that I can self-manage consumption. |

### Acceptance Criteria

- **AC-DSH-008-01:** Given a logged-in team member, when they open the dashboard, then personal token and cost summaries for the selected period are displayed.
- **AC-DSH-008-02:** Given a Super Admin viewing another user's dashboard scope, when authorized, then that user's summary is displayed; otherwise access is denied.

### Dependencies

- FR-PLT-001 (Authentication and RBAC)
- FR-ING-003 (Individual Usage Views)
- FR-DSH-009 (Dashboard Common Features)

### Priority

**P0**

---

## FR-DSH-009: Dashboard Common Features

### Description

All dashboards SHALL support custom date filters, drill-down navigation, and export to CSV and PDF so users can analyze and share insights.

### Business Rules

- Date filters MUST support custom start and end dates and common presets (e.g., current month, last 30 days).
- Drill-down MUST navigate from aggregate widgets to detailed team, user, or tool views without losing filter context.
- CSV and PDF export MUST include data visible to the user under RBAC for the active filter set.
- Dashboard initial load MUST complete within 3 seconds for standard queries (NFR).

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-DSH-009-01 | SA / FV / TA / AU | As a user, I want to filter dashboards by date range so that I analyze specific periods. |
| US-DSH-009-02 | SA / FV / TA | As a user, I want to drill down from summary widgets so that I can investigate details. |
| US-DSH-009-03 | SA / FV / TA / AU | As a user, I want to export dashboard data to CSV or PDF so that I can share insights offline. |

### Acceptance Criteria

- **AC-DSH-009-01:** Given any dashboard view, when the user sets a custom date range, then all widgets refresh using the same filter.
- **AC-DSH-009-02:** Given an aggregate widget with drill-down enabled, when the user selects a data point, then the system navigates to a detail view preserving date and scope filters.
- **AC-DSH-009-03:** Given visible dashboard data, when the user exports to CSV or PDF, then the file contains the filtered dataset and generates within acceptable performance limits.
- **AC-DSH-009-04:** Given standard organizational data volumes (up to 200 teams, 5,000 users), when the dashboard loads, then time-to-interactive is under 3 seconds.

### Dependencies

- FR-PLT-001 (Authentication and RBAC)
- FR-USG-001 (Team-Level Usage Tracking)

### Priority

**P0**
