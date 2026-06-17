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

cat > "$ROOT_DIR/DEPLOY.txt" <<'DEPLOY'
AI Tool Usage Tracker - Docker Deployment Package
=================================================

Stack:
  - PostgreSQL 15 (postgres, host port 5433)
  - FastAPI API (internal only in prod — api:8000 on Docker network)
  - React frontend gateway (APP_PORT / FRONTEND_PORT, default 4501, profile prod)
  - Host nginx: single location /aitool/ → port 4501 (deploy/nginx.example.conf)

Quick start (Linux):
  1. ./scripts/deploy-docker.sh ai-tools-token-tracker.zip

Manual start:
  1. Copy deploy/.env.example to .env and update secrets/passwords
  2. Set APP_PORT=4501, VITE_API_BASE_URL=/aitool/api/v1
  3. docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile prod up --build -d
  4. curl http://127.0.0.1:4501/aitool/api/v1/health

Services:
  postgres   - database
  api        - FastAPI (internal; proxied via frontend nginx at /aitool/api/)
  frontend   - React SPA + API gateway (FRONTEND_PORT -> 4501, requires --profile prod)

Production env: deploy/.env.example
Host nginx: deploy/nginx.example.conf

Useful commands:
  docker compose --profile prod logs -f api frontend
  docker compose --profile prod down
  docker compose --profile prod down -v   (reset database)
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
echo "Package: single gateway port ${FRONTEND_PORT:-4501} (profile prod + docker-compose.prod.yml)"
echo "Deploy: docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile prod up --build -d"
echo "Production env template: deploy/.env.example"
echo "Host nginx example: deploy/nginx.example.conf"
