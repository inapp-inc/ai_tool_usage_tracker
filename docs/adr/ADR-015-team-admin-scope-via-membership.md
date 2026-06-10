# ADR-015: Team Admin Scope via Active Membership

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

FR-ADM-002 and FR-PLT-001 require Team Admins to manage members only for teams they administer. The database schema (`admin.team_memberships`) does not include a per-membership `is_admin` flag — only `joined_at` and `removed_at`.

The platform assigns `team_admin` as a **user-level RBAC role** in `auth.users.role`.

---

## Decision

A user with platform role `team_admin` MAY perform team member mutations (add/remove/list) on team T **if and only if** they have an **active** membership on team T (`removed_at IS NULL`).

Users with role `super_admin` MAY perform team member mutations on **any** team in their organization without membership requirement.

Team create/update/deactivate remains **`super_admin` only** per OpenAPI.

---

## Consequences

### Positive

- No schema change required beyond `admin.team_memberships`.
- Clear, testable authorization rule.
- Aligns Team Admin role with team membership for scoped administration.

### Negative

- A Team Admin must be added as a member before they can manage a team's roster (operational step for Super Admin).
- Cannot designate a team admin who is not also a member of that team.

### Neutral

- Future per-team admin flag can supersede this ADR if product requires non-member team admins.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **`is_team_admin` column on membership** | Valid but adds migration complexity; defer unless product requires |
| **Team Admin manages all org teams** | Violates FR-PLT-001 least-privilege |
| **Separate `administered_teams` table** | Over-engineered for Phase 1 |

**Supersedes:** None  
**Superseded by:** None  
**Related:** ADR-005, FR-ADM-002
