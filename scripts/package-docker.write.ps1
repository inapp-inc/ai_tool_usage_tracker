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

  - FastAPI API (API_PORT, default 4500 -> container 8000)

  - React frontend (FRONTEND_PORT, default 4501 -> container 4501, profile prod)

  - Host nginx on server routes /aitool/ (see deploy/nginx.example.conf)



Quick start (Linux):

  1. ./scripts/deploy-docker.sh ai-tools-token-tracker.zip



Manual start:

  1. Copy deploy/.env.example to .env and update secrets/passwords

  2. Set ENVIRONMENT=production, API_PORT and FRONTEND_PORT

  3. docker compose --profile prod up --build -d

  4. Open http://localhost:4501/aitool/ (frontend) and http://localhost:4500/api/v1/health (api)



Default admin (seeded on first startup if auth tables empty):

  See DEV_SUPER_ADMIN_EMAIL / DEV_SUPER_ADMIN_PASSWORD in .env



Services:

  postgres   - database

  api        - FastAPI (API_PORT -> container 8000)

  frontend   - React SPA (FRONTEND_PORT -> container 4501, requires --profile prod)



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
