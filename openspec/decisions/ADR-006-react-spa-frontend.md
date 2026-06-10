# ADR-006: React SPA Frontend

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

The platform requires rich interactive dashboards (9 widget types), administration screens, file upload workflows, notification center, and report generation UI. Users include administrators, finance viewers, team members, and auditors. Dashboard load time must be under 3 seconds (NFR-PER-001). Mobile-native applications are out of Phase 1 scope.

Project technical direction specifies **React**, **TypeScript**, **Material UI**, **TanStack Query**, and **Recharts**.

---

## Decision

Deliver the user interface as a **React Single Page Application (SPA)**:

- **TypeScript** for type safety aligned with API contracts.
- **Material UI (MUI)** for accessible, consistent enterprise UI components.
- **TanStack Query** for server state, caching, and optimistic updates.
- **Recharts** for dashboard trend and comparison visualizations.
- **i18n-ready** string externalization with English (en-US) only in Phase 1 (NFR-LOC-001).
- Production hosting via **S3 + CloudFront**; API at separate subdomain (`app.` / `api.`).

No dedicated **Backend-for-Frontend (BFF)** layer; SPA consumes FastAPI REST directly.

---

## Consequences

### Positive

- Rich client-side interactivity for dashboards, drill-down, and date filters.
- TanStack Query reduces redundant API calls and supports stale-while-revalidate patterns.
- MUI accelerates enterprise UI delivery with WCAG-oriented components (NFR-ACC-001).
- Recharts integrates naturally with React for usage trend widgets.
- Static SPA deployment scales independently via CDN.

### Negative

- Initial bundle size must be managed (code splitting by route recommended).
- SEO not a priority for authenticated enterprise app; acceptable trade-off.
- API contract changes require coordinated frontend/backend releases.

### Neutral

- Server-side rendering (Next.js) not required for authenticated dashboard use case.
- Responsive web design in scope; native mobile apps deferred to Phase 2.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **Next.js (SSR/SSG)** | Adds complexity without SEO benefit for login-gated enterprise app. |
| **Vue/Angular** | Project specifies React stack. |
| **Server-rendered templates (Jinja/HTMX)** | Poor fit for interactive dashboards and client-side filtering/export UX. |
| **BFF layer (Node)** | Extra service to maintain; single API consumer in Phase 1 does not justify BFF. |
| **Micro-frontends** | Over-engineered for Phase 1 module count and team size. |

**Supersedes:** None  
**Related:** ADR-002, ADR-012
