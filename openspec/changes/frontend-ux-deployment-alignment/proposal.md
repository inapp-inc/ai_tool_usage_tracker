# Proposal: Frontend UX, Terminology, and Deployment Alignment

## Summary

Document implemented frontend and backend alignment work (2026-06-15) that was delivered outside the original mock-API documentation track:

- Admin UI terminology: **Teams** (API connections) vs **Groups** (member org units)
- Live HTTP integration replacing in-memory mocks for core admin, alerts, uploads, and dashboard modules
- Auth session persistence across browser reload (`sessionStorage` + bootstrap)
- Production Docker frontend gateway (`/aitool/` SPA + `/aitool/api/v1/` API proxy)
- Insights **Usage by Team** backed by API team (`admin.tools`) usage metrics
- Alert scope options: Organization, Group, Team (API connection), User
- CSV upload inspect/preview with column mapping; CSV-imported teams skip vendor sync
- Groups CRUD fix (`Team` model import in teams service)

## Motivation

OpenSpec still described mock-only frontend APIs, legacy routes (`/admin/tools`), and group-based dashboard usage. Operators and developers need accurate docs for navigation, data semantics, and production URLs.

## Scope

| In scope | Out of scope |
|----------|--------------|
| Route map, UI/API terminology glossary | Full OpenAPI rewrite |
| Insights usage-by-team data source | Top-consumers user ranking (still team rollup) |
| Auth session restore behaviour | SSO / logout API |
| Docker frontend/nginx production layout | AWS/EKS migration |
| Alert scope UI labels and `tool` scope value | Alert evaluation engine |
| CSV import UX for tools and uploads | New vendor parsers |

## Related changes

- `sync-openspec-frontend-mock-apis` — superseded in part (mocks removed for implemented modules)
- `authentication-backend` — session persistence extends D4
- `dashboard-backend` — usage-by-team semantics clarified
- `user-management-backend` — `/teams` API = Groups in UI
