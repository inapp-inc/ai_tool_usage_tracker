# ADR-019: Frontend Architecture Standards

**Status:** Accepted  
**Date:** 2026-06-11

---

## Context

The platform is building a React SPA for a multi-role B2B dashboard covering usage analytics, administration, file uploads, alerts, and reporting. Multiple personas (Super Admin, Team Admin, Finance Viewer, Team Member, Auditor) share a single codebase with role-gated navigation. The frontend must be maintainable at scale, type-safe against API contracts, and secure against common SPA vulnerabilities (notably XSS token theft).

The stack is React 18, TypeScript, Vite, MUI v6, TanStack Query v5, Zustand, React Hook Form, Zod, Recharts, and Tabler Icons (ADR-006).

---

## Decision

Establish the following frontend architecture standards:

1. **Zustand over Redux** for client-side global state (auth session, notifications). Zustand is lighter with minimal boilerplate; server state remains in TanStack Query exclusively.

2. **TanStack Query as the sole data layer** — components and pages never call `fetch` directly. All HTTP access flows through typed domain modules under `src/api/`.

3. **Named exports everywhere except pages** — enables tree-shaking and consistent import patterns. Default exports are permitted only in `src/pages/` and `src/routes/` for React.lazy code splitting.

4. **Strict TypeScript** — `strict`, `noUnusedLocals`, `noUnusedParameters`, `noImplicitReturns`, `exactOptionalPropertyTypes`, and path alias `@/*` → `src/*`.

5. **Zod for runtime validation at API boundaries** — request/response payloads validated before entering application logic (implemented per feature).

6. **No localStorage or sessionStorage for tokens** — access and refresh tokens live in memory only (XSS risk mitigation). Session restore attempts in-memory refresh on mount; full page reload requires re-authentication unless httpOnly cookies are introduced server-side later.

7. **ESLint enforcement** — no explicit `any`, no unused vars, React hooks rules, import/no-default-export (with page exceptions), no-console (warn/error only).

8. **Centralised formatting and i18n** — token/cost/date formatting via `src/utils/formatters.ts`; UI strings via `src/i18n/`.

---

## Consequences

### Positive

- Predictable folder structure accelerates onboarding and code review.
- Strict typing catches contract drift at compile time; Zod adds runtime safety at boundaries.
- In-memory token storage reduces XSS exfiltration surface compared to localStorage.
- Lazy-loaded routes keep initial bundle size manageable (NFR-PER-001).
- Named exports improve tree-shaking and IDE refactor support.
- Domain-scoped API modules map cleanly to backend OpenAPI tags.

### Negative

- Page reload loses in-memory session unless backend adopts httpOnly refresh cookies.
- Strict TypeScript and ESLint may slow initial development until patterns are internalised.
- Zod schemas require maintenance alongside OpenAPI contract changes.
- Flat ESLint v9 config and import plugin rules add CI lint step overhead.

### Neutral

- Zustand coexists with TanStack Query — clear separation: Zustand for UI/session state, Query for server state.
- Placeholder page folders under `src/pages/` scaffold future migration from `src/routes/`.
- ADR-006 remains the stack decision; this ADR defines implementation conventions.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **Redux Toolkit** | Heavier boilerplate for two small global stores (auth, notifications). |
| **fetch in components** | Duplicates error handling, auth headers, and correlation IDs. |
| **localStorage JWT** | XSS can exfiltrate tokens; rejected per NFR-SEC requirements. |
| **Default exports everywhere** | Worse tree-shaking; inconsistent with hook/util naming conventions. |
| **Relaxed TypeScript** | API contract alignment requires strict mode per ADR-012. |

**Supersedes:** None  
**Related:** ADR-006, ADR-005, ADR-012
