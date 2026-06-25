# AI Tool Usage Tracker

Centralized platform for monitoring AI tool consumption, costs, and adoption across organizations.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2)
- Git
- Node.js 20+ (frontend local dev without Docker)

## Local development stack (minimal — token collector MVP)

| Service | Image / build | Purpose |
|---------|---------------|---------|
| `postgres` | `postgres:15-alpine` | PostgreSQL 15 (host port **5433** → container 5432) |
| `api` | `backend/Dockerfile` | FastAPI + Alembic migrations on startup + **in-process token collector scheduler** |
| `frontend-dev` | `node:20-alpine` | Vite dev server on **5173** (profile **`dev`** only) |
| `frontend` | `frontend/Dockerfile` | Production SPA gateway (profile **`prod`** only — `/aitool/` on **4501**) |

The API container runs scheduled token pulls (APScheduler). Configure pull interval from the frontend via `POST/PATCH /api/v1/collectors` (`pull_interval_minutes`).

OpenSpec: [openspec/changes/token-collector-mvp](openspec/changes/token-collector-mvp/proposal.md)

### Quick start

1. Copy environment template and set a local password:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and replace placeholder values. At minimum, set `POSTGRES_PASSWORD`.

2. Start the local stack (postgres + api + Vite dev server):

   ```bash
   docker compose --profile dev up --build -d
   ```

   Open **http://localhost:5173** (Vite dev server).

   API-only without frontend:

   ```bash
   docker compose up --build -d postgres api
   ```

   Or run the frontend on the host instead of Docker:

   ```bash
   cd frontend && npm ci && npm run dev
   ```

   **If you see migration errors** such as `Can't locate revision identified by '007_role_permissions'`, reset the database volume:

   ```bash
   docker compose --profile dev down -v
   docker compose --profile dev up --build -d
   ```

3. Verify services:

   ```bash
   docker compose exec postgres pg_isready -U aitracker -d aitracker
   curl http://localhost:8000/api/v1/health
   ```

   Expected API response:

   ```json
   {"status": "ok", "database": "ok"}
   ```

5. Sign in (bootstrap super admin — created on first API startup when `auth.users` is empty):

   | Variable | Local default |
   |----------|----------------|
   | `SUPER_ADMIN_EMAIL` | `admin@example.com` |
   | `SUPER_ADMIN_PASSWORD` | `change_me_dev_only` |

   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d "{\"email\":\"admin@example.com\",\"password\":\"change_me_dev_only\"}"

   curl http://localhost:8000/api/v1/auth/me \
     -H "Authorization: Bearer <access_token>"
   ```

6. Create a collector and run a manual pull:

   ```bash
   curl -X POST http://localhost:8000/api/v1/collectors \
     -H "Content-Type: application/json" \
     -d "{\"name\":\"OpenAI Dev\",\"provider\":\"openai\",\"api_token\":\"sk-test\",\"pull_interval_minutes\":60}"

   curl -X POST http://localhost:8000/api/v1/collectors/{id}/run
   curl http://localhost:8000/api/v1/usage/summary
   ```

### Frontend development

**Docker (profile `dev`):**

```bash
docker compose --profile dev up --build -d
```

Open http://localhost:5173 — API at http://localhost:8000/api/v1.

**On your host (faster hot reload, optional):**

```bash
cd frontend
npm ci
npm run dev
```

### Apply order for OpenSpec changes

1. `foundation` (this stack)
2. `authentication-backend`
3. Other backend modules (user management, collector, dashboards, etc.)

### Common commands

```bash
docker compose down
docker compose down -v          # destructive — removes volumes
docker compose --profile dev logs -f api frontend-dev
docker compose --profile dev up --build -d
```

## Server deployment

Production defaults in `.env.example`:

| Setting | Value |
|---------|--------|
| `POSTGRES_PORT` | `5433` (host) |
| `APP_PORT` / `FRONTEND_PORT` | `4501` (single gateway — SPA + API) |
| `VITE_BASE_PATH` | `/aitool/` |
| `VITE_API_BASE_URL` | `/aitool/api/v1` |
| `SUPER_ADMIN_EMAIL` | set in `deploy/.env.example` |
| `SEED_SUPER_ADMIN_ON_STARTUP` | `true` (production) |

1. Copy `deploy/.env.example` to `.env`, set strong secrets, `SUPER_ADMIN_EMAIL`, and `SUPER_ADMIN_PASSWORD`.
2. Set `CORS_ORIGINS` to your public frontend origin (e.g. `https://foundry.inapp.com`).
3. Start the stack:

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile prod up --build -d
   ```

4. App URL: `https://foundry.inapp.com/aitool/` (via server nginx)  
   API health: `curl http://127.0.0.1:4501/aitool/api/v1/health`

Host nginx proxies **only** `/aitool/` to port **4501**. The frontend container proxies `/aitool/api/` to the API internally.

## Project structure

```
backend/           # FastAPI + Celery + Alembic
frontend/          # React SPA (Vite, MUI, TanStack Query)
docker/            # Docker init scripts
openspec/          # Requirements, architecture, API specs, tasks
.github/workflows/ # CI pipeline (TASK-INF-005)
docker-compose.yml
```

## Tests

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
pytest ../tests -v -m "not integration"

cd ../frontend
npm ci
npm test
```

Integration tests (Postgres required):

```bash
export DATABASE_URL=postgresql+asyncpg://aitracker:PASSWORD@localhost:5432/aitracker
pytest tests -v -m integration
```

## License

Proprietary — InApp / Foundry project.
