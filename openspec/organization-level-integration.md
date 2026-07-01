# Organization-Level Integration — Requirements & Development Spec

**Status:** Draft (target behavior)  
**Last updated:** 2026-06-25  
**Scope:** Multi-tenant organization model, Super Admin provisioning, Organization Admin lifecycle, member invitation, and org-wide visibility for customer tenants.

---

## 1. Purpose

This document defines how **organizations**, **roles**, and **member provisioning** must work together. It replaces fragmented flows (separate “create organization”, “create member”, org picker in multiple places) with one coherent model:

- **Super Admin** operates the platform and all customer organizations.
- **Organization Admin** operates a single customer organization (teams, members, tools, usage, costs).
- **Team Admin / Team Member** operate within assigned teams.

The implementation MUST treat **platform organization** (`platform` / `default` slug) and **customer organizations** (tenants) as distinct scopes with explicit rules.

---

## 2. Terminology

| Term | Meaning |
|------|---------|
| **Platform org** | Internal org for Super Admin users only (`slug ∈ {platform, default}`). Not a customer tenant. |
| **Customer org (tenant)** | A provisioned organization identified by **name** in the UI; isolated teams, tools, members, and usage. |
| **Super Admin (SA)** | Platform operator; cross-tenant access when needed; full write access. |
| **Organization Admin (Org Admin)** | Admin of exactly one customer org; org-wide read/write for administration and insights. |
| **System role** | Built-in role seeded per org (`is_system=true`); MUST NOT be deleted. |
| **Username** | Login identifier (email) used for authentication; displayed name is separate (`display_name`). |

---

## 3. Goals

### 3.1 Primary goals

1. Super Admin can perform **all** platform and tenant administration actions.
2. Super Admin can **provision a customer organization** and its **first Organization Admin** in one clear flow (or invite Org Admin via member invitation).
3. When inviting a user as **Organization Admin**, the UI MUST collect **organization name** (create tenant if new, or select existing).
4. Organization Admin sees **all activity in their organization**: all teams, all connected tools, all members they manage, and org-level cost/usage insights—not only teams they personally belong to.
5. System roles (including `org_admin`) are **seeded automatically** per tenant and **cannot be deleted**.

### 3.2 Non-goals (this spec)

- SSO / SAML role mapping (Phase 2).
- Self-service tenant signup (customers are provisioned by Super Admin).
- Billing/invoicing per tenant.
- Hard delete of organizations or users.

---

## 4. Role Model

### 4.1 System roles (per organization)

Each customer org MUST seed at least:

| Role | `is_system` | Deletable | Org scope |
|------|-------------|-----------|-----------|
| `super_admin` | yes | no | Platform org only |
| `org_admin` | yes | no | Customer org only |
| `team_admin` | yes | no | Customer org |
| `team_member` | yes | no | Customer org |
| `finance_viewer` | yes | no | Customer org |
| `auditor` | yes | no | Customer org |

**Business rules**

- `DELETE /roles/{id}` MUST return **409** when `is_system=true`.
- `org_admin` MUST NOT exist as an assignable role on the **platform org** (Org Admins belong to customer orgs only).
- `super_admin` MUST NOT be assignable inside a customer org.

### 4.2 Permission intent (Org Admin)

Organization Admin MUST have org-wide access equivalent to Super Admin **within their tenant**:

| Resource | Read | Write | Scope |
|----------|------|-------|-------|
| Insights / dashboard | yes | — | Entire org |
| Teams | yes | yes | All teams in org |
| Members | yes | yes | All org users (not platform users) |
| Tools (catalogue) | yes | yes | Org catalogue |
| Credentials / connected tools | yes | yes | Org credentials |
| Uploads | yes | yes | Org uploads |
| Alerts / thresholds | yes | yes | Org + all teams |
| Settings / roles | yes | limited | Custom roles only; system roles locked |
| Audit log | yes | — | Org events |

Team Admin remains **team-scoped** for member management and team insights.

---

## 5. User Journeys

### 5.1 Super Admin — full platform access

**As** Super Admin  
**I want** unrestricted access to all customer organizations and platform settings  
**So that** I can configure tools, teams, credentials, members, and insights for any tenant.

**Acceptance criteria**

- **AC-SA-01:** SA can switch tenant context via org selector (“All organizations” or a specific customer org).
- **AC-SA-02:** With a tenant selected, SA sees the same admin surfaces as Org Admin for that tenant, plus cross-tenant list/breakdown when “All organizations” is selected.
- **AC-SA-03:** SA can invite users into any customer org with any assignable role (including `org_admin`).
- **AC-SA-04:** SA cannot invite `org_admin` into the platform org.

### 5.2 Super Admin — create Organization Admin (primary provisioning flow)

**As** Super Admin  
**I want** to create an Organization Admin with username (email), password, and organization name  
**So that** a customer tenant exists and the customer can administer their own org.

**Unified flow (target — single “Invite / Provision user” entry point)**

1. SA opens **Members → Invite** (or **Organizations → Provision**, merged into one UX).
2. SA selects role **Organization Admin**.
3. Form expands:
   - **Organization name** (required; creates new tenant if that name does not already exist)
   - **Username (email)** (required)
   - **Display name** (optional)
   - **Password** (required or auto-generated once)
4. On submit:
   - If tenant does not exist → create org → seed roles & catalogue tools → create user as `org_admin`.
   - If tenant exists (SA selected existing org) → create user as `org_admin` in that org only.
5. Response shows one-time credentials if password was generated.

**Acceptance criteria**

- **AC-PROV-01:** Creating Org Admin with a **new organization name** creates tenant + org admin in one transaction.
- **AC-PROV-02:** Creating Org Admin for an **existing organization** does not create a duplicate tenant.
- **AC-PROV-03:** Org Admin user is linked to `role_id` of seeded `org_admin` role for that tenant.
- **AC-PROV-04:** No separate “Create Organization” dialog that uses a different member model (team_member default)—Org Admin path is explicit.

### 5.3 Super Admin — invite other roles

**As** Super Admin  
**I want** to invite Team Admin, Team Member, Finance Viewer, etc. into a selected customer org  
**So that** day-to-day users are onboarded without creating new tenants.

**Business rules**

- Target org MUST be selected (header org selector **or** inline org picker when “All organizations” is active).
- Role dropdown MUST load roles from **target tenant’s** `auth.roles`, not platform org roles.
- `team_admin` / `team_member` require at least one team assignment.
- `org_admin` / `finance_viewer` / `auditor` MUST NOT require team assignment.

**Acceptance criteria**

- **AC-INV-01:** Role list loads after tenant is known; shows loading state while fetching.
- **AC-INV-02:** Inviting into tenant T uses `organization_id=T` on create-user API regardless of SA’s platform org membership.
- **AC-INV-03:** Submitting without tenant selected returns validation error (UI + API 422).

### 5.4 Organization Admin — org-wide visibility

**As** Organization Admin  
**I want** to see all teams, tools, credentials, usage, and costs for my organization  
**So that** I can govern AI adoption without being assigned to every team.

**Acceptance criteria**

- **AC-OA-01:** Org Admin Insights shows **organization total cost** cards for their org (same rollup as Teams summary).
- **AC-OA-02:** Org Admin can list **all teams** in the org (not only teams they belong to).
- **AC-OA-03:** Org Admin can list **all connected tools** and credentials in the org.
- **AC-OA-04:** Org Admin can view usage for any team in the org (read) and manage members according to permission matrix.
- **AC-OA-05:** Org Admin MUST NOT see other customer organizations or platform org data.

---

## 6. Data & API Requirements

### 6.1 Organization entity

```
auth.organizations
  id, name, slug, created_at
```

- **`name`** is the only user-facing identifier for customer organizations (shown in UI, org selector, invite forms).
- **`slug`** is an **internal** unique key (auto-generated from `name` by the backend). Users MUST NOT enter or edit slugs.
- Reserved internal slugs: `platform`, `default` (platform org only).
- Creating tenant triggers: `_ensure_system_roles`, `sync_org_builtin_catalogue_tools`.

### 6.2 Provisioning API (target contract)

**Option A — extend user invite (preferred for unified UX)**

`POST /api/v1/users`

| Field | Required when | Description |
|-------|---------------|-------------|
| `email` | always | Username / login |
| `password` | optional | Generated if omitted |
| `display_name` | optional | Shown name |
| `role_id` or `role` | always | Target role |
| `organization_id` | SA inviting into existing tenant | Tenant UUID |
| `organization_name` | SA + role=`org_admin` + no `organization_id` | Creates tenant (name only; slug generated server-side) |
| `team_ids` | team-scoped roles | UUID[] |

**Option B — dedicated endpoint (alternative)**

`POST /api/v1/organizations/provision`

Body: `{ name, admin: { email, password, display_name? } }`

Response: `{ organization, admin_user }`

Only one public provisioning path SHOULD exist in the UI to avoid divergence.

### 6.3 Roles API

`GET /api/v1/roles?organization_id={tenantId}`

- SA: MUST resolve roles for requested tenant (query param or org scope header).
- Org Admin: roles for own org only.
- System roles returned with `is_system: true`.

### 6.4 Scope resolution (all list endpoints)

| Actor | `organization_id` scope | Team filter |
|-------|-------------------------|-------------|
| SA, “All orgs” | Aggregate or require pick | Optional |
| SA, tenant selected | That tenant | Optional |
| Org Admin | Own tenant only | Optional (all teams allowed) |
| Team Admin | Own tenant | Managed teams only |
| Team Member | Own tenant | Member teams only |

---

## 7. UI Requirements

### 7.1 Single entry point for provisioning

| Current (problem) | Target |
|-------------------|--------|
| Separate “Create Organization” + “Invite Member” with different defaults | One **Invite / Provision** flow with role-driven fields |
| Org picker in header AND in invite form | Org picker in **one place**: header when browsing; inline only when header = “All organizations” |
| Role dropdown empty for SA | Role dropdown loads tenant roles after org context is set |

### 7.2 Role-driven invite form

| Selected role | Additional fields |
|---------------|-------------------|
| Organization Admin | Organization name (new) **or** existing org selector; email; password; display name |
| Team Admin / Team Member | Organization (if not in header); teams (multi-select); email; password; display name |
| Finance Viewer / Auditor | Organization (if not in header); email; password; display name |

### 7.3 Super Admin org selector (header)

- **All organizations** — cross-tenant views (insights breakdown, org list).
- **Specific customer org** — all admin pages scoped to that tenant; invite form omits redundant org picker.

### 7.4 Organization Admin navigation

Org Admin sees the same admin menu items as SA **except**:

- No cross-tenant org selector.
- No platform-only actions (e.g. create tenant—optional: hide or SA-only).
- Settings → Roles: system roles read-only, not deletable.

---

## 8. Insights & Cost Visibility (Org Admin)

Organization Admin MUST see at top of Insights (org-wide, all-time or agreed period):

1. **Organization Total Cost**
2. **Total Tools Cost** (subscriptions / priced tooling)
3. **Additional Billable Cost**

Below that: period + team + tool filters for **detailed** charts (scoped drill-down).

Org Admin rollup MUST match Teams page org summary for the same org and period.

---

## 9. Security & Audit

- All provisioning actions MUST write audit events: `organization.create`, `user.invite`, `user.role_change`.
- SA cross-tenant access MUST be logged with target `organization_id`.
- Passwords MUST be hashed (bcrypt/argon2); plaintext only returned once at creation if generated.
- Email uniqueness: **global** across platform (one account per email).

---

## 10. Current Implementation vs Target (gap analysis)

| Area | Current behavior | Target | Priority |
|------|------------------|--------|----------|
| Org creation UX | Separate dialog; optional team_member seed | Unified invite when role = Org Admin; **name only** (no slug) | P0 |
| Org Admin provisioning | Was org-admin-only on `POST /organizations`; recently changed to optional team_member | Restore Org Admin as primary provision path | P0 |
| SA role dropdown | Depends on org context; was broken when scope missing | Load tenant roles reliably | P0 |
| Org picker duplication | Header + form | Single source of truth | P1 |
| Org Admin insights | Partially implemented | Full org-wide teams/tools/usage | P0 |
| System role delete | Implemented (409) | Keep | — |
| Verification file dumps | Removed from UI; disabled by default | No file push | Done |

---

## 11. Development Phases

### Phase 1 — Stabilize provisioning (P0)

1. **Backend:** Extend `POST /users` (or single provision endpoint) with `organization_name` when role is `org_admin` and no `organization_id` (slug generated server-side).
2. **Backend:** Fix `GET /roles` tenant resolution for SA (query param + org scope).
3. **Frontend:** Replace separate Create Organization dialog with role-driven invite form.
4. **Frontend:** Org name field visible **only** when role = Organization Admin.
5. **Tests:** API tests for create-tenant-on-invite, duplicate organization name, org_admin on platform org rejected.

### Phase 2 — Org Admin visibility (P0)

1. Ensure Org Admin bypasses team membership for **read** on teams, tools, credentials, insights.
2. Align org cost cards with Teams rollup for Org Admin (same period rules).
3. Integration tests: Org Admin sees all teams; Team Admin sees subset.

### Phase 3 — Polish (P1)

1. Merge Organizations list into Admin (optional nav item for SA).
2. Post-provision success modal with credentials + link to select new org in header.
3. OpenAPI update for provision fields.

---

## 12. Test Plan (acceptance)

| ID | Scenario | Expected |
|----|----------|----------|
| T-01 | SA invites Org Admin with new org name “Acme Corp” | Tenant created with name “Acme Corp”; user is org_admin |
| T-02 | SA invites Org Admin into existing tenant | No new tenant; user added to existing org |
| T-03 | SA invites Team Member without selecting org | UI validation error |
| T-04 | SA with tenant selected in header invites Team Admin | Roles load; teams list filtered to tenant |
| T-05 | Org Admin opens Insights | Org cost cards visible; all teams in team filter |
| T-06 | Org Admin lists teams | Sees teams they are not a member of |
| T-07 | Delete system role `org_admin` | HTTP 409 |
| T-08 | Org Admin logs in | Cannot access other tenant’s data |

---

## 13. Open Questions

1. **Email uniqueness:** Global (current) vs per-tenant—confirm global remains.
2. **Org Admin create tenant:** Should Org Admin ever create sub-orgs? (Default: **no**, SA only.)
3. **Default team on org create:** Auto-create “Default Team” when first team-scoped user is added? (Recommended: yes.)
4. **Insights period for org totals:** All-time vs selected period—align Teams bar and Insights cards (document per product decision).

---

## 14. Related Documents

- [openspec/requirements/01-administration.md](./requirements/01-administration.md)
- [openspec/changes/user-management-backend/design.md](./changes/user-management-backend/design.md)
- [openspec/changes/dynamic-role-access-control/design.md](./changes/dynamic-role-access-control/design.md)
- [openspec/changes/dashboard-backend/specs/dashboard-rbac-scope/spec.md](./changes/dashboard-backend/specs/dashboard-rbac-scope/spec.md)
- [openspec/project.md](./project.md) — Users and Roles (to be updated for Org Admin)

---

## 15. Summary (product rules)

1. **Super Admin** can do everything, across all customer orgs.
2. **Organization Admin** is created by Super Admin with **username (email)**; selecting Org Admin on invite shows **organization name** only (creates tenant if needed; no slug field).
3. **System roles** (`org_admin` included) are seeded per tenant and **cannot be deleted**.
4. **Organization Admin** sees **all teams, tools, usage, and costs** in their organization—not only their own team memberships.
5. **One integrated provisioning UX**—no conflicting “create org” vs “invite member” flows.
