#!/usr/bin/env bash
set -euo pipefail

# Deploy AI Tool Usage Tracker on Linux using docker compose.
# Host nginx is configured separately on the server (see deploy/nginx.example.conf).
#
# Usage:
#   ./scripts/deploy-docker.sh [archive-path]
#
# Environment overrides:
#   DEPLOY_ROOT=/var/www/ai-tool-tracker
#   APP_NAME=ai-tool-tracker
#   PUBLIC_ORIGIN=https://foundry.inapp.com
#   ENV_FILE=/path/to/.env
#   SKIP_BUILD=1              Skip image rebuild (env-only / restart)
#   BUILD_PARALLEL=0          Build api then frontend (default; safer on small VMs)
#   BUILD_PARALLEL=1          Build api + frontend at the same time (needs 4GB+ RAM)

ARCHIVE_PATH="${1:-ai-tools-token-tracker.zip}"
DEPLOY_ROOT="${DEPLOY_ROOT:-/var/www/ai-tool-tracker}"
APP_NAME="${APP_NAME:-ai-tool-tracker}"
PUBLIC_ORIGIN="${PUBLIC_ORIGIN:-https://foundry.inapp.com}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-$APP_NAME}"

POSTGRES_USER="${POSTGRES_USER:-aitracker}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
POSTGRES_DB="${POSTGRES_DB:-aitracker}"

PORT_RANGE_START="${PORT_RANGE_START:-4500}"
PORT_RANGE_END="${PORT_RANGE_END:-4599}"

command -v docker >/dev/null 2>&1 || {
  echo "docker is required on the destination host." >&2
  exit 1
}
command -v unzip >/dev/null 2>&1 || {
  echo "unzip is required on the destination host." >&2
  exit 1
}

COMPOSE_CMD=()
if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "docker compose (plugin) or docker-compose is required." >&2
  exit 1
fi

env_value() {
  local file="$1"
  local key="$2"
  [[ -f "$file" ]] || return 0
  awk -F= -v key="$key" '
    $0 !~ /^[[:space:]]*#/ && $1 == key {
      sub(/^[^=]*=/, "", $0)
      gsub(/^["'\'']|["'\'']$/, "", $0)
      print $0
      exit
    }
  ' "$file"
}

ensure_env_value() {
  local file="$1"
  local key="$2"
  local value="$3"
  if [[ -z "$(env_value "$file" "$key" || true)" ]]; then
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}

set_env_value() {
  local file="$1"
  local key="$2"
  local value="$3"
  local tmp="${file}.tmp"
  if [[ -f "$file" ]] && grep -qE "^${key}=" "$file"; then
    awk -v key="$key" -v value="$value" '
      BEGIN { replaced = 0 }
      $0 ~ "^" key "=" {
        print key "=" value
        replaced = 1
        next
      }
      { print }
      END {
        if (!replaced) print key "=" value
      }
    ' "$file" > "$tmp"
    mv "$tmp" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}

is_port_free() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ! ss -ltn "( sport = :$port )" | grep -q ":$port"
  elif command -v lsof >/dev/null 2>&1; then
    ! lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
  elif command -v netstat >/dev/null 2>&1; then
    ! netstat -ltn | grep -q ":$port "
  else
    ! (echo >/dev/tcp/127.0.0.1/"$port") >/dev/null 2>&1
  fi
}

choose_port() {
  local preferred="${1:-}"
  local start="${2:-4500}"
  local end="${3:-4599}"
  if [[ -n "$preferred" ]] && is_port_free "$preferred"; then
    echo "$preferred"
    return 0
  fi
  for port in $(seq "$start" "$end"); do
    if is_port_free "$port"; then
      echo "$port"
      return 0
    fi
  done
  echo "No free port found in ${start}-${end}." >&2
  return 1
}

choose_distinct_port() {
  local preferred="${1:-}"
  local start="${2:-4500}"
  local end="${3:-4599}"
  local exclude="${4:-}"
  if [[ -n "$preferred" && "$preferred" != "$exclude" ]] && is_port_free "$preferred"; then
    echo "$preferred"
    return 0
  fi
  for port in $(seq "$start" "$end"); do
    if [[ "$port" == "$exclude" ]]; then
      continue
    fi
    if is_port_free "$port"; then
      echo "$port"
      return 0
    fi
  done
  echo "No free port found in ${start}-${end} (excluding ${exclude})." >&2
  return 1
}

check_deploy_resources() {
  if command -v free >/dev/null 2>&1; then
    local avail_mb
    avail_mb="$(free -m | awk '/^Mem:/ {print $7}')"
    if [[ "${avail_mb:-0}" -lt 1200 ]]; then
      echo "WARNING: Low available memory (${avail_mb}MB)." >&2
      echo "  Frontend npm build often needs 1.5–2GB. Add swap or the build may hang/OOM and take the server offline." >&2
    fi
  fi
  if command -v df >/dev/null 2>&1; then
    local avail_disk_mb
    avail_disk_mb="$(df -m "$DEPLOY_ROOT" 2>/dev/null | awk 'NR==2 {print $4}' || true)"
    if [[ -n "$avail_disk_mb" && "$avail_disk_mb" -lt 2048 ]]; then
      echo "WARNING: Low disk space (${avail_disk_mb}MB free under $DEPLOY_ROOT)." >&2
    fi
  fi
}

compose_prod() {
  "${COMPOSE_CMD[@]}" --profile prod "$@"
}

build_images() {
  if [[ "${BUILD_PARALLEL:-0}" == "1" ]]; then
    echo "Building api + frontend in parallel (requires 4GB+ RAM)..."
    compose_prod build --parallel
    return
  fi

  echo "Building api image..."
  compose_prod build api
  echo "Building frontend image (npm run build — slowest step, ~2–5 min)..."
  compose_prod build frontend
}

POSTGRES_VOLUME_NAME="${POSTGRES_VOLUME_NAME:-ai-tracker-postgres-data}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-ai-tracker-postgres}"

postgres_volume_exists() {
  docker volume inspect "$POSTGRES_VOLUME_NAME" >/dev/null 2>&1
}

postgres_psql_ok() {
  local user="$1"
  local pass="$2"
  local db="$3"
  PGPASSWORD="$pass" docker exec "$POSTGRES_CONTAINER" \
    psql -U "$user" -d "$db" -tAc "SELECT 1" >/dev/null 2>&1
}

wait_for_postgres_container() {
  local status
  echo "Waiting for postgres container to become healthy..."
  for _ in $(seq 1 45); do
    if docker inspect "$POSTGRES_CONTAINER" >/dev/null 2>&1; then
      status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$POSTGRES_CONTAINER" 2>/dev/null || echo missing)"
      if [[ "$status" == "healthy" || "$status" == "running" ]]; then
        return 0
      fi
    fi
    sleep 2
  done
  echo "Postgres container did not become ready in time." >&2
  return 1
}

detect_postgres_credentials() {
  local file="$1"
  local pass user db

  pass="$(env_value "$file" POSTGRES_PASSWORD || true)"
  user="$(env_value "$file" POSTGRES_USER || true)"
  db="$(env_value "$file" POSTGRES_DB || true)"
  user="${user:-aitracker}"
  db="${db:-aitracker}"

  if [[ -n "$pass" ]] && postgres_psql_ok "$user" "$pass" "$db"; then
    echo "Postgres credentials verified ($user / $db)"
    return 0
  fi

  # Older deployment packages initialized postgres as tokentracker/tokentracker
  if postgres_psql_ok tokentracker tokentracker tokentracker; then
    set_env_value "$file" POSTGRES_USER tokentracker
    set_env_value "$file" POSTGRES_PASSWORD tokentracker
    set_env_value "$file" POSTGRES_DB tokentracker
    echo "Aligned .env with existing postgres volume (legacy user tokentracker)"
    return 0
  fi

  if [[ -n "$pass" ]]; then
    for try_user in tokentracker aitracker; do
      for try_db in tokentracker aitracker "$db"; do
        if postgres_psql_ok "$try_user" "$pass" "$try_db"; then
          set_env_value "$file" POSTGRES_USER "$try_user"
          set_env_value "$file" POSTGRES_DB "$try_db"
          echo "Aligned postgres credentials ($try_user / $try_db)"
          return 0
        fi
      done
    done
  fi

  cat >&2 <<EOF
ERROR: Cannot connect to postgres with credentials in $file

Logs show "role aitracker does not exist" when the volume was created with another user (often tokentracker).

Fix .env manually, then restart:
  POSTGRES_USER=tokentracker
  POSTGRES_PASSWORD=tokentracker
  POSTGRES_DB=tokentracker

Or reset the database (deletes all data):
  docker compose --profile prod down
  docker volume rm $POSTGRES_VOLUME_NAME
  ./scripts/deploy-docker.sh ...
EOF
  exit 1
}

urlencode() {
  python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$1"
}

sync_database_url() {
  local file="$1"
  local user db pass encoded url
  user="$(env_value "$file" POSTGRES_USER)"
  db="$(env_value "$file" POSTGRES_DB)"
  pass="$(env_value "$file" POSTGRES_PASSWORD)"
  user="${user:-aitracker}"
  db="${db:-aitracker}"
  if [[ -z "$pass" ]]; then
    echo "POSTGRES_PASSWORD is required to build DATABASE_URL." >&2
    return 1
  fi
  encoded="$(urlencode "$pass")"
  url="postgresql+asyncpg://${user}:${encoded}@postgres:5432/${db}"
  set_env_value "$file" "DATABASE_URL" "$url"
}

resolve_postgres_password() {
  local file="$1"
  local existing
  existing="$(env_value "$file" POSTGRES_PASSWORD || true)"

  if [[ -n "$POSTGRES_PASSWORD" ]]; then
    set_env_value "$file" "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD"
    existing="$POSTGRES_PASSWORD"
  fi

  existing="$(env_value "$file" POSTGRES_PASSWORD || true)"

  if postgres_volume_exists; then
    if [[ -z "$existing" || "$existing" == change_me* ]]; then
      cat >&2 <<EOF
ERROR: Postgres data volume "$POSTGRES_VOLUME_NAME" already exists, but .env has no valid POSTGRES_PASSWORD.

The database password is fixed when the volume is first created. Either:
  1. Set POSTGRES_PASSWORD in .env to the original password (e.g. from first deploy), or
  2. Reset the database (deletes all data):
     docker compose --profile prod down
     docker volume rm $POSTGRES_VOLUME_NAME
     ./scripts/deploy-docker.sh ...

If an older deploy used user "tokentracker", the deploy script will auto-detect after postgres starts, or set manually:
  POSTGRES_USER=tokentracker
  POSTGRES_PASSWORD=tokentracker
  POSTGRES_DB=tokentracker
EOF
      exit 1
    fi
    echo "Existing postgres volume detected — keeping POSTGRES_PASSWORD from .env"
    return
  fi

  if [[ -z "$existing" || "$existing" == change_me* ]]; then
    existing="$(openssl rand -hex 16 2>/dev/null || date +%s%N)"
    set_env_value "$file" "POSTGRES_PASSWORD" "$existing"
    echo "Generated POSTGRES_PASSWORD for new database volume"
  fi
}

if [[ ! -f "$ARCHIVE_PATH" ]]; then
  echo "Archive not found: $ARCHIVE_PATH" >&2
  exit 1
fi
ARCHIVE_PATH="$(cd "$(dirname "$ARCHIVE_PATH")" && pwd)/$(basename "$ARCHIVE_PATH")"

mkdir -p "$DEPLOY_ROOT"
unzip -oq "$ARCHIVE_PATH" -d "$DEPLOY_ROOT"

if [[ ! -f "$DEPLOY_ROOT/docker-compose.yml" ]]; then
  echo "Invalid archive: docker-compose.yml not found in $DEPLOY_ROOT" >&2
  exit 1
fi

DEST_ENV_FILE="${ENV_FILE:-}"
if [[ -z "$DEST_ENV_FILE" ]]; then
  for candidate in \
    "$DEPLOY_ROOT/.env" \
    "/etc/${APP_NAME}.env"; do
    if [[ -f "$candidate" ]]; then
      DEST_ENV_FILE="$candidate"
      break
    fi
  done
fi

if [[ -z "$DEST_ENV_FILE" ]]; then
  DEST_ENV_FILE="$DEPLOY_ROOT/.env"
fi

if [[ ! -f "$DEST_ENV_FILE" ]]; then
  if [[ -f "$DEPLOY_ROOT/deploy/.env.example" ]]; then
    cp "$DEPLOY_ROOT/deploy/.env.example" "$DEST_ENV_FILE"
    echo "Created $DEST_ENV_FILE from deploy/.env.example"
  elif [[ -f "$DEPLOY_ROOT/.env.example" ]]; then
    cp "$DEPLOY_ROOT/.env.example" "$DEST_ENV_FILE"
    echo "Created $DEST_ENV_FILE from .env.example"
  else
    touch "$DEST_ENV_FILE"
    echo "Created empty $DEST_ENV_FILE"
  fi
else
  echo "Using env file: $DEST_ENV_FILE"
fi

ensure_env_value "$DEST_ENV_FILE" "POSTGRES_USER" "$POSTGRES_USER"
ensure_env_value "$DEST_ENV_FILE" "POSTGRES_DB" "$POSTGRES_DB"
set_env_value "$DEST_ENV_FILE" "POSTGRES_PORT" "5433"
set_env_value "$DEST_ENV_FILE" "ENVIRONMENT" "production"

if [[ -n "$POSTGRES_PASSWORD" ]]; then
  set_env_value "$DEST_ENV_FILE" "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD"
fi

resolve_postgres_password "$DEST_ENV_FILE"
sync_database_url "$DEST_ENV_FILE"

JWT_VALUE="$(env_value "$DEST_ENV_FILE" JWT_SECRET_KEY || env_value "$DEST_ENV_FILE" APP_SECRET_KEY || true)"
if [[ -z "$JWT_VALUE" || "$JWT_VALUE" == change_me* || "$JWT_VALUE" == "change-me-in-production" ]]; then
  JWT_VALUE="$(openssl rand -hex 32 2>/dev/null || date +%s%N)"
  set_env_value "$DEST_ENV_FILE" "JWT_SECRET_KEY" "$JWT_VALUE"
  echo "Generated JWT_SECRET_KEY"
fi

COLLECTOR_KEY="$(env_value "$DEST_ENV_FILE" COLLECTOR_ENCRYPTION_KEY || true)"
if [[ -z "$COLLECTOR_KEY" || "$COLLECTOR_KEY" == change_me* ]]; then
  COLLECTOR_KEY="$(openssl rand -hex 32 2>/dev/null || date +%s%N)"
  set_env_value "$DEST_ENV_FILE" "COLLECTOR_ENCRYPTION_KEY" "$COLLECTOR_KEY"
  echo "Generated COLLECTOR_ENCRYPTION_KEY"
fi

PREFERRED_API_PORT="$(env_value "$DEST_ENV_FILE" API_PORT || env_value "$DEST_ENV_FILE" BACKEND_PORT || true)"
API_PORT="$(choose_port "$PREFERRED_API_PORT" "$PORT_RANGE_START" "$PORT_RANGE_END")"
set_env_value "$DEST_ENV_FILE" "API_PORT" "$API_PORT"

PREFERRED_FRONTEND_PORT="$(env_value "$DEST_ENV_FILE" FRONTEND_PORT || env_value "$DEST_ENV_FILE" APP_PORT || true)"
FRONTEND_PORT="$(choose_distinct_port "$PREFERRED_FRONTEND_PORT" "$PORT_RANGE_START" "$PORT_RANGE_END" "$API_PORT")"
set_env_value "$DEST_ENV_FILE" "FRONTEND_PORT" "$FRONTEND_PORT"

BASE_PATH="$(env_value "$DEST_ENV_FILE" VITE_BASE_PATH || true)"
BASE_PATH="${BASE_PATH:-/aitool/}"
BASE_PATH="${BASE_PATH%/}"
set_env_value "$DEST_ENV_FILE" "VITE_BASE_PATH" "${BASE_PATH}/"
set_env_value "$DEST_ENV_FILE" "VITE_API_BASE_URL" "${BASE_PATH}/api/v1"

CORS_VALUE="$(env_value "$DEST_ENV_FILE" CORS_ORIGINS || true)"
if [[ -z "$CORS_VALUE" ]]; then
  set_env_value "$DEST_ENV_FILE" "CORS_ORIGINS" "${PUBLIC_ORIGIN%/},${PUBLIC_ORIGIN%/}:${FRONTEND_PORT}"
fi

if [[ "$PUBLIC_ORIGIN" == "http://localhost" || "$PUBLIC_ORIGIN" == "https://localhost" ]]; then
  PUBLIC_ORIGIN="http://127.0.0.1:${FRONTEND_PORT}${BASE_PATH}"
elif [[ "$PUBLIC_ORIGIN" != *"${BASE_PATH}" ]]; then
  PUBLIC_ORIGIN="${PUBLIC_ORIGIN%/}${BASE_PATH}"
fi
set_env_value "$DEST_ENV_FILE" "FRONTEND_URL" "$PUBLIC_ORIGIN"

if [[ "$DEST_ENV_FILE" != "$DEPLOY_ROOT/.env" ]]; then
  ln -sfn "$DEST_ENV_FILE" "$DEPLOY_ROOT/.env"
  echo "Linked $DEPLOY_ROOT/.env -> $DEST_ENV_FILE"
fi

export COMPOSE_PROJECT_NAME
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export BUILDKIT_PROGRESS=plain

cd "$DEPLOY_ROOT"
check_deploy_resources

if [[ "${SKIP_BUILD:-0}" == "1" ]]; then
  echo "Skipping image build (SKIP_BUILD=1)..."
else
  echo "Building images (services stay running until swap — no 'compose down')..."
  build_images
fi

echo "Starting postgres..."
compose_prod up -d postgres
wait_for_postgres_container
detect_postgres_credentials "$DEST_ENV_FILE"
sync_database_url "$DEST_ENV_FILE"

echo "Recreating postgres with aligned credentials..."
compose_prod up -d --force-recreate --no-build postgres
wait_for_postgres_container

echo "Starting api + frontend..."
compose_prod up -d --no-build --remove-orphans

echo "Waiting for API health on port ${API_PORT}..."
ready=0
for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${API_PORT}/api/v1/health" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done

frontend_ready=0
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${FRONTEND_PORT}${BASE_PATH}/" >/dev/null 2>&1; then
    frontend_ready=1
    break
  fi
  sleep 2
done

cat <<EOF

Deployed AI Tool Usage Tracker
==============================
Project:      $COMPOSE_PROJECT_NAME
Deploy root:  $DEPLOY_ROOT
Env file:     $DEST_ENV_FILE
Environment:  production

API:          http://127.0.0.1:${API_PORT}/api/v1/
Frontend:     http://127.0.0.1:${FRONTEND_PORT}${BASE_PATH}/
Health:       http://127.0.0.1:${API_PORT}/api/v1/health
Public URL:   $PUBLIC_ORIGIN

Configure host nginx using:
  $DEPLOY_ROOT/deploy/nginx.example.conf
  (replace BACKEND_PORT=${API_PORT} and FRONTEND_PORT=${FRONTEND_PORT})

Useful commands:
  cd $DEPLOY_ROOT
  ${COMPOSE_CMD[*]} --profile prod ps
  ${COMPOSE_CMD[*]} --profile prod logs -f api frontend
  ${COMPOSE_CMD[*]} --profile prod down
  ${COMPOSE_CMD[*]} --profile prod down -v    # reset database

Suggested host nginx routes:

  location /aitool/api/ {
    proxy_pass http://127.0.0.1:${API_PORT}/api/;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
  }

  location /aitool/ {
    proxy_pass http://127.0.0.1:${FRONTEND_PORT}/aitool/;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
  }
EOF

if [[ "$ready" -ne 1 ]]; then
  echo
  echo "Warning: API health check did not pass within 120s. Check logs:" >&2
  echo "  cd $DEPLOY_ROOT && ${COMPOSE_CMD[*]} --profile prod logs api" >&2
  exit 1
fi

if [[ "$frontend_ready" -ne 1 ]]; then
  echo
  echo "Warning: frontend did not respond at http://127.0.0.1:${FRONTEND_PORT}${BASE_PATH}/ within 60s." >&2
  echo "  cd $DEPLOY_ROOT && ${COMPOSE_CMD[*]} --profile prod logs frontend" >&2
  exit 1
fi
