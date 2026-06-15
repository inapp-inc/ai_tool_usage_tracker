# Frontend Standards

**Status:** Active  
**Date:** 2026-06-11  
**Related:** ADR-006, ADR-019

This document defines implementation standards for the React SPA under `frontend/`.

---

## Folder Structure

| Path | Purpose |
|------|---------|
| `src/theme/` | MUI theme: palette tokens, typography scale, component overrides |
| `src/components/layout/` | App shell, sidebar, top bar, page header |
| `src/components/data-display/` | Stat cards, tables, badges, token/cost display, empty states |
| `src/components/charts/` | Recharts wrappers (trends, donuts, bars, progress) |
| `src/components/feedback/` | Skeletons, toasts, error panels |
| `src/components/forms/` | Slide-over panels, period selector, confirm dialog, file dropzone |
| `src/components/navigation/` | Notification bell, role guard, breadcrumbs |
| `src/pages/` | Route-level page components (lazy-loaded, default export allowed) |
| `src/routes/` | Legacy/placeholder route components (lazy-loaded, default export allowed) |
| `src/hooks/` | Reusable React hooks |
| `src/stores/` | Zustand client-state stores |
| `src/api/` | HTTP client and domain API modules |
| `src/types/` | Shared TypeScript interfaces and enums |
| `src/utils/` | Pure formatting and helper functions |
| `src/i18n/` | Locale string resources and `t()` helper |
| `src/auth/` | Auth provider and context |

---

## Naming Conventions

| Artifact | Convention | Example |
|----------|------------|---------|
| React components | PascalCase | `StatCard.tsx` |
| Hooks | camelCase, `use` prefix | `useFilters.ts` |
| Utils / stores | camelCase | `formatters.ts`, `authStore.ts` |
| Non-component modules | kebab-case (preferred for multi-word files) | `date-helpers.ts` |
| Types / enums | PascalCase | `Role`, `ApiError` |
| i18n keys | dot-separated lowercase | `auth.login.title` |

---

## Export Rules

- **Named exports** are required for components, hooks, utils, stores, API modules, and types.
- **Default exports** are permitted **only** in `src/pages/` and `src/routes/` to support `React.lazy()` dynamic imports.
- ESLint rule `import/no-default-export` enforces this (with the page/route exception).

---

## TypeScript

- `strict: true` and `exactOptionalPropertyTypes: true` are mandatory.
- **`any` is forbidden** — use `unknown` and narrow with type guards or Zod schemas.
- Path alias **`@/`** maps to `src/` — use for all internal imports (e.g. `@/api/client`, `@/types`).

---

## API Access

- All HTTP calls go through **`src/api/` domain files** (`auth.ts`, `usage.ts`, etc.).
- Components and pages **must not** call `fetch` directly.
- Shared client behaviour (correlation ID, auth header, 401 refresh, error parsing) lives in `src/api/client.ts`.
- Runtime validation with **Zod** at API boundaries is required when implementing domain methods.

---

## Forms

- All forms use **react-hook-form** with **Zod** resolvers (`@hookform/resolvers`).
- Validation schemas live alongside the form component or in a co-located `schema.ts` file.

---

## Security

- **Access and refresh tokens** are stored in **`sessionStorage`** for tab-scoped session restore; access token is also held in memory during active use — never `localStorage` or logs.
- **Never log** request or response bodies. The API client logs only method, URL, and status code at warn level.
- Sensitive credentials (API keys) follow the same in-memory-only rule in UI state.

## Production base path

- Set `VITE_BASE_PATH` (e.g. `/aitool`) for subpath hosting; `BrowserRouter` basename must match nginx SPA location.
- Set `VITE_API_BASE_URL` to the proxied API path (e.g. `/aitool/api/v1`).

## API integration status (2026-06-15)

Core modules call live `/api/v1` endpoints: `auth`, `tools`, `teams`, `members`, `credentials`, `alerts`, `uploads`, `dashboard`, `usage`. See `openspec/changes/frontend-ux-deployment-alignment/design.md` for UI/API terminology.

---

## Formatting

- Token counts, currency, percentages, and dates **must** use `src/utils/formatters.ts`.
- Do not inline `toLocaleString`, manual K/M suffixes, or ad-hoc date formatting in components.

---

## Internationalisation

- All user-visible strings **must** go through `src/i18n/` via the `t()` helper.
- No hardcoded UI strings in components except developer-only debug output (which should not ship).

---

## State Management

| Concern | Tool |
|---------|------|
| Server/async data | TanStack Query |
| Auth session, notifications | Zustand (`src/stores/`) |
| Form state | react-hook-form |
| URL filters | `useSearchParams` via `useFilters` hook |

---

## Linting and CI

Run `npm run lint` before commit. Key rules:

- `@typescript-eslint/no-explicit-any`: error
- `@typescript-eslint/no-unused-vars`: error
- `react-hooks/rules-of-hooks`: error
- `react-hooks/exhaustive-deps`: warn
- `no-console`: warn (allow `console.warn`, `console.error` only)
- `import/no-default-export`: error (except pages/routes)

---

## Testing

- Unit tests co-located with source (`*.test.ts`, `*.test.tsx`).
- Lazy routes wrapped in `<Suspense>` in tests.
- API client tested with mocked `fetch`.
