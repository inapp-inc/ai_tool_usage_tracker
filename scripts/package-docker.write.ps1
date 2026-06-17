param(

    [Parameter(Mandatory = $true)]

    [string]$RootDir

)



$dockerignore = @'

.git

.env

*.env

!*.env.example

!deploy/.env.example

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

'@



$deployNotes = @'

AI Tool Usage Tracker - Docker Deployment Package

=================================================



Stack:

  - PostgreSQL 15 (postgres, host port 5433)

  - FastAPI API (internal in prod — proxied at /aitool/api/ via frontend nginx)

  - React frontend gateway (APP_PORT / FRONTEND_PORT, default 4501, profile prod)

  - Host nginx: single location /aitool/ → port 4501 (deploy/nginx.example.conf)



Quick start (Linux):

  1. ./scripts/deploy-docker.sh ai-tools-token-tracker.zip



Manual start:

  1. Copy deploy/.env.example to .env and update secrets/passwords

  2. Set APP_PORT=4501, VITE_API_BASE_URL=/aitool/api/v1

  3. docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile prod up --build -d

  4. curl http://127.0.0.1:4501/aitool/api/v1/health



Default admin (seeded on first startup if auth tables empty):

  See DEV_SUPER_ADMIN_EMAIL / DEV_SUPER_ADMIN_PASSWORD in .env



Services:

  postgres   - database

  api        - FastAPI (internal; /aitool/api/ via frontend nginx)

  frontend   - React SPA + API gateway (FRONTEND_PORT -> 4501, requires --profile prod)



Production env (deploy/.env.example):

  ENVIRONMENT=production

  API_PORT=4500

  FRONTEND_PORT=4501

  VITE_BASE_PATH=/aitool/

  CORS_ORIGINS=https://foundry.inapp.com



Host nginx (production):

  deploy/nginx.example.conf



Useful commands:

  docker compose --profile prod logs -f api frontend

  docker compose --profile prod down

  docker compose --profile prod down -v   (reset database)

'@



[IO.File]::WriteAllText((Join-Path $RootDir '.dockerignore'), $dockerignore)

[IO.File]::WriteAllText((Join-Path $RootDir 'DEPLOY.txt'), $deployNotes)



# Remove obsolete single-container Dockerfile from older packaging scripts

$legacyDockerfile = Join-Path $RootDir 'Dockerfile'

if (Test-Path $legacyDockerfile) {

    Remove-Item -Force $legacyDockerfile

}
