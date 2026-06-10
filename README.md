# AI Tool Usage Tracker

Centralized platform for monitoring AI tool consumption, costs, and adoption across organizations.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2)
- Git
- Node.js 20+ (frontend local dev without Docker)

## Deployment model

**All environments** run on **Docker Compose** with **local persistent volumes** (PostgreSQL, Redis, file storage, backups). See [openspec/specifications/deployment.md](openspec/specifications/deployment.md) and [ADR-013](openspec/decisions/ADR-013-docker-compose-local-storage.md).

| Volume | Purpose |
|--------|---------|
| `ai-tracker-postgres-data` | Database |
| `ai-tracker-redis-data` | Redis AOF |
| `ai-tracker-storage-data` | Uploads, reports (`/var/lib/ai-tracker/storage`) |
| `ai-tracker-backups-data` | pg_dump and storage tarballs |

## Local development stack (TASK-INF-001 – INF-006)

| Service | Image / build | Purpose |
|---------|---------------|---------|
| `postgres` | `postgres:15-alpine` | PostgreSQL 15 |
| `redis` | `redis:7-alpine` | Cache/broker |
| `migrate` | `backend/Dockerfile` | One-shot Alembic `upgrade head` |
| `api` | `backend/Dockerfile` | FastAPI at `/api/v1` |
| `worker` | `backend/Dockerfile` | Celery worker (5 queues) |
| `beat` | `backend/Dockerfile` | Celery Beat |
| `frontend` | `node:20-alpine` | Vite dev server (profile `dev` only) |

### Quick start

1. Copy environment template and set a local password:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and replace placeholder values. At minimum, set `POSTGRES_PASSWORD`.

2. Run database migrations (first time or after schema changes):

   ```bash
   docker compose run --rm migrate
   ```

3. Start the stack:

   ```bash
   docker compose up --build
   ```

4. Verify services:

   ```bash
   docker compose exec postgres pg_isready -U aitracker -d aitracker
   curl http://localhost:8000/api/v1/health
   ```

   Expected API response:

   ```json
   {"status": "ok", "database": "ok", "redis": "ok"}
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
docker compose --profile dev up --build frontend api postgres redis migrate
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
