# AI Tool Usage Tracker

Centralized platform for monitoring AI tool consumption, costs, and adoption across organizations.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2)
- Git
- Node.js 20+ (frontend local dev without Docker)

## Local development stack (minimal — token collector MVP)

| Service | Image / build | Purpose |
|---------|---------------|---------|
| `postgres` | `postgres:15-alpine` | PostgreSQL 15 |
| `api` | `backend/Dockerfile` | FastAPI + Alembic migrations on startup + **in-process token collector scheduler** |
| `frontend` | `node:20-alpine` | Vite dev server (profile `dev` only) |

The API container runs scheduled token pulls (APScheduler). Configure pull interval from the frontend via `POST/PATCH /api/v1/collectors` (`pull_interval_minutes`).

OpenSpec: [openspec/changes/token-collector-mvp](openspec/changes/token-collector-mvp/proposal.md)

### Quick start

1. Copy environment template and set a local password:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and replace placeholder values. At minimum, set `POSTGRES_PASSWORD`.

2. Start the stack (runs migrations automatically before the API starts):

   ```bash
   docker compose up --build postgres api
   ```

   **If you see migration errors** such as `Can't locate revision identified by '007_role_permissions'`, your database volume is from an older branch. Reset it:

   ```bash
   docker compose down -v
   docker compose up --build postgres api
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

5. Sign in (dev seed user):

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

**Local (recommended):**

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173 — API requests proxy to `http://localhost:8000/api/v1`.

**Docker (optional):**

```bash
docker compose --profile dev up --build frontend api postgres
```

### Apply order for OpenSpec changes

1. `foundation` (this stack)
2. `authentication-backend`
3. Other backend modules (user management, collector, dashboards, etc.)

### Common commands

```bash
docker compose down
docker compose down -v          # destructive — removes volumes
docker compose logs -f api worker beat
docker compose up --build api worker beat
```

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
