# Frontend Tasks

React SPA implementation aligned with OpenAPI contract.

---

## TASK-UI-001: Authentication UI

### Description

Build login page, token storage, refresh flow, protected routes, and auth context integrated with TanStack Query. Redirect by role after login.

### Dependencies

TASK-INF-006, TASK-PLT-001

### Estimated Complexity

**M**

### Definition of Done

- [ ] Login/logout flows work against API
- [ ] Expired token triggers refresh or re-login
- [ ] Protected routes block unauthenticated access
- [ ] MUI forms meet basic accessibility (labels, focus)

**FR:** FR-PLT-001 · **NFR:** NFR-ACC-002

---

## TASK-UI-002: Administration Screens

### Description

Build admin UI for tools, teams (with member management), credentials (masked display, rotate), and thresholds with role-based visibility.

### Dependencies

TASK-UI-001, TASK-ADM-001 – TASK-ADM-004

### Estimated Complexity

**XL**

### Definition of Done

- [ ] Super Admin can CRUD all admin entities
- [ ] Team Admin sees only administered teams
- [ ] Validation errors display from Problem Details
- [ ] FR-ADM-001–004 primary user stories walkthrough pass

**FR:** FR-ADM-001 – FR-ADM-004

---

## TASK-UI-003: Upload and Import Wizard

### Description

Build upload form (drag-drop, team selector), status polling, preview table (matched/unmatched), commit with idempotency key, reprocess and delete actions.

### Dependencies

TASK-UI-001, TASK-ING-002 – TASK-ING-006

### Estimated Complexity

**L**

### Definition of Done

- [ ] 50 MB client-side size check before upload
- [ ] Preview shows sample rows and unmatched emails
- [ ] Commit disabled until preview_ready status
- [ ] FR-ING-001–002 user flows complete end-to-end

**FR:** FR-ING-001 – FR-ING-002

---

## TASK-UI-004: Dashboard Page

### Description

Build dashboard with date range filter, widgets (tokens, cost, by-tool, by-team, top consumers, alerts, trends, my-usage) using Recharts, `last_updated_at` display, drill-down navigation.

### Dependencies

TASK-UI-001, TASK-DSH-002 – TASK-DSH-005

### Estimated Complexity

**XL**

### Definition of Done

- [ ] All widgets load with shared date filter
- [ ] Role-appropriate data shown (TM vs SA)
- [ ] Dashboard initial load perceived ≤3s with loading skeletons
- [ ] FR-DSH-001–009 widget stories verified manually

**FR:** FR-DSH-001 – FR-DSH-009 · **NFR:** NFR-PER-001

---

## TASK-UI-005: Reports UI

### Description

Build report request forms per type, sync download, async job polling, and presigned download link display.

### Dependencies

TASK-UI-001, TASK-RPT-002, TASK-RPT-003

### Estimated Complexity

**L**

### Definition of Done

- [ ] User can generate each report type with filters
- [ ] Async jobs show progress and notification link
- [ ] Finance Viewer has read-only report access
- [ ] FR-RPT-001–007 core flows complete

**FR:** FR-RPT-001 – FR-RPT-007

---

## TASK-UI-006: Notification Center UI

### Description

Build header notification bell with unread badge, notification drawer/list, mark-as-read, deep link navigation.

### Dependencies

TASK-UI-001, TASK-NTF-003

### Estimated Complexity

**M**

### Definition of Done

- [ ] Unread count updates on mark-read
- [ ] Deep links navigate to alert context
- [ ] ARIA live region announces new notifications (NFR-ACC-004)
- [ ] FR-NTF-001 user stories pass

**FR:** FR-NTF-001

---

## TASK-UI-007: Audit Log Viewer

### Description

Build audit log search UI with filters and CSV export for Super Admin and Auditor roles.

### Dependencies

TASK-UI-001, TASK-PLT-004

### Estimated Complexity

**S**

### Definition of Done

- [ ] Auditor can query and export; write actions hidden
- [ ] Pagination works with cursor
- [ ] FR-PLT-002 and FR-RPT-006 audit visibility verified

**FR:** FR-PLT-002, FR-RPT-006

---

## TASK-UI-008: Individual Usage View (P0)

### Description

Build personal usage page: total usage, by-tool breakdown, trends, team comparison per FR-ING-003 (may reuse dashboard my-usage widget).

### Dependencies

TASK-UI-004, TASK-DSH-005

### Estimated Complexity

**M**

### Definition of Done

- [ ] Team Member sees only own data
- [ ] Team Admin can view team members when authorized
- [ ] FR-ING-003 acceptance criteria pass

**FR:** FR-ING-003
