#!/bin/sh
set -e

# Build DATABASE_URL inside the container so the host is always the Compose
# service name and special characters in POSTGRES_PASSWORD are URL-encoded.
if [ -n "${POSTGRES_PASSWORD:-}" ]; then
  export DATABASE_URL="$(python3 - <<'PY'
import os
import urllib.parse

user = os.environ.get("POSTGRES_USER", "aitracker")
password = os.environ["POSTGRES_PASSWORD"]
database = os.environ.get("POSTGRES_DB", "aitracker")
encoded = urllib.parse.quote(password, safe="")
print(f"postgresql+asyncpg://{user}:{encoded}@postgres:5432/{database}")
PY
)"
fi

exec "$@"
