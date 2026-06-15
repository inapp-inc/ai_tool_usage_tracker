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
| `frontend` | `frontend/Dockerfile` | nginx SPA + API proxy at `/aitool/` on port **4501** |
| `frontend-dev` | `node:20-alpine` | Vite dev server (profile `dev` only) |

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

**Local (recommended for UI work):**

```bash
cd frontend
npm ci
cp .env.example .env.local   # VITE_API_BASE_URL=http://localhost:8000/api/v1
npm run dev
```

Open http://localhost:5173 — API requests go to `http://localhost:8000/api/v1`.

**Docker production-like stack (port 4501):**

```bash
docker compose up --build
```

Open http://localhost:4501/aitool/ — nginx serves the SPA and proxies `/aitool/api/v1` to the API container.

**Docker Vite hot reload (optional):**

```bash
docker compose --profile dev up --build frontend-dev api postgres redis migrate
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

Integration tests (Postgres + Redis required):

```bash
export DATABASE_URL=postgresql+asyncpg://aitracker:PASSWORD@localhost:5432/aitracker
export REDIS_URL=redis://localhost:6379/0
pytest tests -v -m integration
```

### Authentication (TASK-PLT-001)

After migrate and seed:

```bash
docker compose run --rm migrate
docker compose run --rm api python -m app.scripts.seed_dev_admin

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@acme.example","password":"SecurePass123!"}'

curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

Default dev credentials: `admin@acme.example` / `SecurePass123!` (see `.env.example`).

### Tools and credentials (TASK-ADM-001 / TASK-ADM-003)

Protected with JWT. Tool writes and all credential operations require `super_admin`.

```bash
# After login, use Bearer token:
curl http://localhost:8000/api/v1/tools -H "Authorization: Bearer <access_token>"

curl -X POST http://localhost:8000/api/v1/tools \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Production OpenAI","vendor":"OpenAI","pricing_model":"flat_token","token_price":0.005}'

curl -X POST http://localhost:8000/api/v1/credentials \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"tool_id":"<uuid>","environment":"production","secret_value":"sk-live-..."}'
```

Set `CREDENTIAL_ENCRYPTION_KEY` in `.env` for AES-256 credential storage.

## Production deployment (foundry.inapp.com)

Single public port **4501** — nginx in the `frontend` container serves the app and proxies the API:

| URL | Purpose |
|-----|---------|
| `https://foundry.inapp.com/aitool/` | React SPA |
| `https://foundry.inapp.com/aitool/api/v1/` | FastAPI backend |

On the server:

```bash
cp .env.example .env
# Set POSTGRES_PASSWORD, JWT secrets, CREDENTIAL_ENCRYPTION_KEY, CORS_ORIGINS, etc.

docker compose run --rm migrate
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Ensure `.env` includes:

```env
APP_PORT=4501
VITE_API_BASE_URL=/aitool/api/v1
VITE_BASE_PATH=/aitool
CORS_ORIGINS=https://foundry.inapp.com
ENVIRONMENT=production
```

Point your external reverse proxy (TLS at `foundry.inapp.com`) to host port **4501**.

Verify:

```bash
curl http://localhost:4501/aitool/api/v1/health
curl -I http://localhost:4501/aitool/
```

## License

Proprietary — InApp / Foundry project.
