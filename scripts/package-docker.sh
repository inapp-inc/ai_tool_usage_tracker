#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE_PATH="${1:-"$ROOT_DIR/ai-tools-token-tracker-docker.zip"}"

command -v zip >/dev/null 2>&1 || {
  echo "zip is required to create the deployment archive." >&2
  exit 1
}

cat > "$ROOT_DIR/.dockerignore" <<'DOCKERIGNORE'
.git
.env
*.env
!*.env.example
**/.env
**/*.env
.DS_Store
**/.DS_Store
node_modules
**/node_modules
frontend/dist
frontend/node_modules
backend/data
backend/__pycache__
backend/**/__pycache__
backend/.pytest_cache
**/*.pyc
**/*.pyo
**/*.log
*.zip
presales.pem
agent-transcripts
.cursor
DOCKERIGNORE

cat > "$ROOT_DIR/.env.example" <<'ENVEXAMPLE'
POSTGRES_USER=tokentracker
POSTGRES_PASSWORD=tokentracker
POSTGRES_DB=tokentracker
APP_SECRET_KEY=change-me-in-production
APP_ENV=production
APP_LOG_LEVEL=INFO
FRONTEND_URL=https://foundry.inapp.com/aitool
VITE_BASE_PATH=/aitool
BACKEND_PORT=4500
APP_PORT=4501
ENVEXAMPLE

cat > "$ROOT_DIR/DEPLOY.txt" <<'DEPLOY'
AI Tools Token Tracker - Docker Deployment Package
==================================================

Stack:
  - PostgreSQL 16 (postgres)
  - Python FastAPI backend (BACKEND_PORT, default 4500)
  - React Vite frontend (APP_PORT, default 4501)
  - Host nginx on server routes /aitool/ (deploy/nginx.example.conf)

Quick start (Linux):
  1. ./scripts/deploy-docker.sh ai-tools-token-tracker-docker.zip

Manual start:
  1. Copy .env.example to .env and update secrets/passwords
  2. Set APP_ENV=production, BACKEND_PORT and APP_PORT (4500+ range)
  3. docker compose up --build -d
  4. Open http://localhost:4501/aitool (frontend) and http://localhost:4500/health (backend)

Default demo login (after seed):
  admin@demo.com / demo1234

Services:
  postgres   - database
  bootstrap  - one-shot DB init + seed
  backend    - FastAPI API (BACKEND_PORT -> container 8000)
  frontend   - React app (APP_PORT -> container 80)

Production env (.env):
  APP_ENV=production
  BACKEND_PORT=4500
  APP_PORT=4501
  VITE_BASE_PATH=/aitool

Host nginx (production):
  deploy/nginx.example.conf

Useful commands:
  docker compose logs -f backend
  docker compose down
  docker compose down -v   (reset database)
DEPLOY

rm -f "$ROOT_DIR/Dockerfile"
rm -f "$ARCHIVE_PATH"
(
  cd "$ROOT_DIR"
  zip -r "$ARCHIVE_PATH" . \
    -x ".git/*" \
    -x ".env" \
    -x "*.env" \
    -x "*/.env" \
    -x "*/*/.env" \
    -x ".DS_Store" \
    -x "*/.DS_Store" \
    -x "node_modules/*" \
    -x "frontend/node_modules/*" \
    -x "frontend/dist/*" \
    -x "backend/data/*" \
    -x "backend/__pycache__/*" \
    -x "backend/**/__pycache__/*" \
    -x "*.zip" \
    -x "presales.pem" \
    -x "agent-transcripts/*" \
    -x ".cursor/*"
)

echo "Created $ARCHIVE_PATH"
echo "Package: docker-compose (postgres + backend:${BACKEND_PORT:-4500} + frontend:${APP_PORT:-4501})"
echo "Deploy picks free ports from 4500+ and sets APP_ENV=production"
echo "Host nginx example: deploy/nginx.example.conf"
