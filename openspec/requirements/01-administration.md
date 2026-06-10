# Administration — Functional Requirements

Module 1: Platform administration for AI tools, teams, credentials, and alert thresholds.

---

## FR-ADM-001: AI Tool Management

### Description

The system SHALL allow Super Admins to register, configure, and deactivate AI tools so that usage and cost can be tracked consistently across vendors (e.g., OpenAI, Anthropic, Azure AI, Cursor).

### Business Rules

- Each AI tool MUST have a unique name within the organization.
- Tool configuration MUST include: tool name, vendor, pricing model, token pricing, package allowances, and overage pricing.
- Deactivated tools MUST NOT accept new usage ingestion but MUST retain historical data for reporting and audit.
- Pricing model changes MUST NOT retroactively alter previously calculated costs unless explicitly reprocessed by an administrator.
- Only Super Admins MAY create, edit, or deactivate AI tools.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-ADM-001-01 | SA | As a Super Admin, I want to add a new AI tool with pricing configuration so that the platform can track usage and costs for that vendor. |
| US-ADM-001-02 | SA | As a Super Admin, I want to edit an existing tool's pricing or package allowance so that cost calculations stay accurate when contracts change. |
| US-ADM-001-03 | SA | As a Super Admin, I want to deactivate an AI tool so that it no longer appears for new tracking while preserving historical records. |

### Acceptance Criteria

- **AC-ADM-001-01:** Given a Super Admin on the tool management screen, when they submit a valid new tool with all required fields, then the tool is persisted and appears in the active tools list.
- **AC-ADM-001-02:** Given an active AI tool, when a Super Admin updates token pricing or package allowance, then subsequent cost calculations use the updated values and the change is audit-logged.
- **AC-ADM-001-03:** Given an active AI tool with historical usage, when a Super Admin deactivates it, then the tool is marked inactive, excluded from new ingestion mappings, and historical reports remain accessible.
- **AC-ADM-001-04:** Given a non–Super Admin user, when they attempt to create or edit a tool, then the system denies the action with an authorization error.

### Dependencies

- FR-PLT-001 (Authentication and RBAC)
- FR-PLT-002 (Audit Logging)
- FR-USG-001 (Team-Level Usage Tracking) — consumes tool configuration for cost calculation

### Priority

**P0**

---

## FR-ADM-002: Team Management

### Description

The system SHALL allow Super Admins to create and manage teams, assign and remove members, and support users belonging to multiple teams so that usage and costs can be attributed to organizational units.

### Business Rules

- Each team MUST have a unique name within the organization.
- A user MAY belong to one or more teams simultaneously.
- Deactivated teams MUST NOT accept new usage attribution but MUST retain historical data.
- Removing a user from a team MUST NOT delete that user's historical usage attributed to the team.
- Team Admins MAY manage members only for teams they administer; Super Admins MAY manage all teams.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-ADM-002-01 | SA | As a Super Admin, I want to create and update teams so that usage can be organized by business unit. |
| US-ADM-002-02 | SA / TA | As an administrator, I want to assign users to teams so that their AI consumption is attributed correctly. |
| US-ADM-002-03 | SA / TA | As an administrator, I want to remove users from a team without losing historical usage data. |
| US-ADM-002-04 | SA | As a Super Admin, I want to deactivate a team so that it no longer receives new usage assignments. |

### Acceptance Criteria

- **AC-ADM-002-01:** Given a Super Admin, when they create a team with a unique name, then the team is available for member assignment and usage attribution.
- **AC-ADM-002-02:** Given a user and multiple teams, when the user is assigned to more than one team, then usage ingested with team context is attributed to the correct team without conflict.
- **AC-ADM-002-03:** Given a team member with historical usage, when they are removed from the team, then past usage records remain visible in team reports for the periods they belonged.
- **AC-ADM-002-04:** Given a deactivated team, when new usage is ingested without explicit team override, then the system rejects attribution to the deactivated team.

### Dependencies

- FR-PLT-001 (Authentication and RBAC)
- FR-PLT-002 (Audit Logging)
- FR-USG-001 (Team-Level Usage Tracking)

### Priority

**P0**

---

## FR-ADM-003: API Key Management

### Description

The system SHALL allow Super Admins to configure and manage vendor API credentials at organization or team scope, with support for sandbox and production environments, rotation tracking, and expiration reminders.

### Business Rules

- API credentials MUST be encrypted at rest using AES-256.
- Full credential values MUST be masked in the UI after initial creation; only authorized roles MAY reveal or rotate keys through controlled workflows.
- Credentials MAY be scoped globally or to a specific team.
- Each credential MUST be tagged with environment (sandbox or production).
- The system MUST track key rotation dates and notify administrators before expiration based on configured reminders.
- Credential access and rotation events MUST be audit-logged.

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-ADM-003-01 | SA | As a Super Admin, I want to store vendor API credentials securely so that automated usage sync can authenticate with AI providers. |
| US-ADM-003-02 | SA | As a Super Admin, I want team-specific credentials so that different teams can use separate vendor accounts. |
| US-ADM-003-03 | SA | As a Super Admin, I want expiration reminders so that I can rotate keys before they disrupt ingestion. |
| US-ADM-003-04 | SA | As a Super Admin, I want to distinguish sandbox and production keys so that test data does not pollute production metrics. |

### Acceptance Criteria

- **AC-ADM-003-01:** Given a Super Admin submitting a new API key, when the key is saved, then it is encrypted at rest and displayed masked on subsequent views.
- **AC-ADM-003-02:** Given a team-scoped credential, when usage is ingested for that team and tool, then the system uses the team credential where configured, falling back to organization default if defined.
- **AC-ADM-003-03:** Given a credential approaching its expiration date, when the reminder threshold is reached, then administrators receive an in-app notification and optional email per FR-NTF-002.
- **AC-ADM-003-04:** Given any credential create, update, or rotation action, when the action completes, then an audit log entry is recorded with actor, timestamp, and affected tool/team.

### Dependencies

- FR-PLT-001 (Authentication and RBAC)
- FR-PLT-002 (Audit Logging)
- FR-NTF-001 (Notification Center)
- FR-NTF-002 (Email Notifications)
- FR-USG-002 (Usage Data Ingestion)
- FR-RPT-006 (API Key Activity Report)

### Priority

**P0**

---

## FR-ADM-004: Threshold Management

### Description

The system SHALL allow Super Admins and Team Admins to configure usage and cost thresholds at tool, team, or user scope, with warning and critical severity levels, triggering notifications when breached.

### Business Rules

- Threshold types MUST include: token count, package utilization percentage, and cost amount.
- Threshold scope MUST be one of: tool level, team level, or user level.
- Severity MUST be classified as Warning or Critical.
- Notification channels MUST include in-app notifications and email.
- Team Admins MAY configure thresholds only within their administered teams; Super Admins MAY configure thresholds at any scope.
- A threshold evaluation MUST use aggregated usage for the configured period (default: current billing or calendar period unless overridden).

### User Stories

| ID | Role | Story |
|----|------|-------|
| US-ADM-004-01 | SA | As a Super Admin, I want to set organization-wide cost thresholds so that finance is alerted before budgets are exceeded. |
| US-ADM-004-02 | TA | As a Team Admin, I want to set team-level token thresholds so that I can manage my team's consumption proactively. |
| US-ADM-004-03 | SA / TA | As an administrator, I want to define warning and critical levels so that stakeholders receive appropriately prioritized alerts. |

### Acceptance Criteria

- **AC-ADM-004-01:** Given a valid threshold configuration (type, scope, limit, severity), when saved, then the system evaluates it on each usage update or scheduled evaluation cycle.
- **AC-ADM-004-02:** Given a team-level threshold and a Team Admin, when they configure a threshold for their team, then the configuration is accepted; when they attempt another team's threshold, then access is denied.
- **AC-ADM-004-03:** Given usage crossing a warning threshold without reaching critical, when evaluation runs, then a warning-severity notification is generated exactly once per breach cycle until reset or acknowledged per FR-NTF-003.
- **AC-ADM-004-04:** Given usage crossing a critical threshold, when evaluation runs, then critical notifications are sent via configured channels including email.

### Dependencies

- FR-ADM-001 (AI Tool Management)
- FR-ADM-002 (Team Management)
- FR-USG-001 (Team-Level Usage Tracking)
- FR-NTF-001 (Notification Center)
- FR-NTF-002 (Email Notifications)
- FR-NTF-003 (Threshold Alert Triggering)

### Priority

**P0**
