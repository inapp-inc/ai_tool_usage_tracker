# ADR-0018: Dynamic Demo URLs (No localhost Dependency)

## Status
**Accepted**

## Date
2026-02-01

## Context

Presales demos (ShowSync, Virtue, Ariel, Twiin, etc.) are run on shared demo hosts (e.g. `vm-eng-te-10.inapp.com`) as well as on localhost. Hardcoding `localhost` in backends, frontends, and configs causes CORS failures, wrong API links, and Vite "invalid host" errors when the app is opened via the demo host URL.

## Decision

All demos **MUST** use dynamic URLs so the same codebase works on localhost and on any demo host without code changes.

### 1. Environment variables (convention)

| Variable | Used by | Meaning | Example |
|----------|--------|--------|---------|
| **PUBLIC_API_URL** | Backend | Public base URL of the API (no trailing slash). Used for CORS derivation, Swagger "Try it out", and startup logs. | `http://vm-eng-te-10.inapp.com:8003` |
| **VITE_API_URL** | Frontend (Vite) | Full API base URL. Injected at build time; use for axios baseURL and for Vite dev proxy target. | Same as PUBLIC_API_URL; frontend may append `/api` if needed |
| **CORS_ORIGIN** | Backend | Comma-separated list of extra allowed origins (e.g. frontend URLs). | `http://vm-eng-te-10.inapp.com:3003,http://vm-eng-te-10.inapp.com:3004` |

When unset, backends may default to a known demo host (e.g. `vm-eng-te-10.inapp.com`) plus their port, **or** to localhost for local-only use. Prefer defaulting to the demo host so "run and open on VM" works without env.

### 2. Backend

- **CORS**
  - Allow origins from `CORS_ORIGIN` (split by comma).
  - Also allow the host (and optional port) derived from `PUBLIC_API_URL` for same-host frontends (e.g. same host with ports 3000, 3003, 5173).
  - Optionally allow `localhost` and `127.0.0.1` when `PUBLIC_API_URL` is unset or contains localhost, so local dev works.
- **Swagger / OpenAPI**
  - Set `servers[].url` from `PUBLIC_API_URL` so "Try it out" hits the correct host.
- **Startup logs**
  - Log the API and docs URLs using `PUBLIC_API_URL` (or `http://localhost:PORT` only when explicitly local).

### 3. Frontend (Vite)

- **API client (axios/fetch)**
  - Base URL from `import.meta.env.VITE_API_URL` with a single fallback (e.g. demo host URL or empty string for proxy).
- **Vite dev server**
  - **Proxy:** `proxy['/api'].target` = `process.env.VITE_API_URL` or same default (derive origin if needed).
  - **Host:** `server.host: true` when the app is opened from a different host (e.g. VM).
  - **Allowed hosts:** `server.allowedHosts: ['vm-eng-te-10.inapp.com']` (and any other demo hosts) to avoid "Invalid host header" when accessing via VM hostname.

### 4. Run scripts

- **All demos with a run script** must export `PUBLIC_API_URL` and `VITE_API_URL` (and `PORT` where applicable) at the start of the script, defaulting to the deployed host (e.g. `http://vm-eng-te-10.inapp.com:PORT`), so that the person deploying can run `./run.sh` (or `run.bat`) with no manual steps. Backend and frontend processes inherit these env vars. Optionally support `DEPLOYED_ORIGIN` to override the host in one place. Document in README.

### 5. Browser extensions (e.g. Virtue Chrome extension)

- Extensions cannot read Vite env at runtime. Either:
  - Document editing a single constant (e.g. `API_BASE_URL` in background script) and list required host permissions for both localhost and the demo host in `manifest.json`, or
  - Use an options page / chrome.storage to set the API URL at runtime.
- Prefer documenting the constant and adding demo-host permissions so one build works for both local and VM.

### 6. demo-ports.json and viewers

- Document that all demos support dynamic URLs via `PUBLIC_API_URL` and `VITE_API_URL`. Viewer or run scripts can pass these when opening links (e.g. from a shared base URL).

## Consequences

- Demos run on any host without code changes; CORS, Swagger, and Vite all use the same base URL.
- Local dev: set env to localhost or rely on documented localhost defaults where applicable.
- One-time setup per demo host: set `PUBLIC_API_URL` / `VITE_API_URL` (and optionally `CORS_ORIGIN`) in the environment or run script.
