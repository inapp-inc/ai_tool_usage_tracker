# Server deployment notes

## Why deploy can hang or take the server offline

The **frontend Docker build** runs `npm run build` (Vite). After `8219 modules transformed`, it enters **rendering/minifying chunks** — this step often needs **1.5–2GB RAM**. On a small VM:

- **OOM killer** may stop `node`, `dockerd`, or SSH — the server looks “down”
- **Parallel builds** (`api` + `frontend` together) double memory use

The log line `#28 [api] exporting to image` is normal; it is not the failure. The build usually fails or the host freezes during **frontend** `#24 npm run build`.

## Minimum server resources

| Resource | Recommended |
|----------|-------------|
| RAM | **2GB+** (4GB safer) |
| Swap | **2GB** if RAM ≤ 2GB |
| Disk | **5GB+** free for Docker layers |

### Add swap (Linux, one-time)

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

## Safer deploy commands

Default (`deploy-docker.sh`) builds **api first, then frontend** and does **not** run `docker compose down` before build.

```bash
./scripts/deploy-docker.sh ai-tools-token-tracker.zip
```

API-only update (no frontend rebuild):

```bash
SKIP_BUILD=1 ./scripts/deploy-docker.sh ai-tools-token-tracker.zip
# or rebuild only api:
docker compose --profile prod build api
docker compose --profile prod up -d --no-build
```

## Recover if the server is unresponsive

1. Wait 2–3 minutes — OOM may recover after a failed build
2. SSH in and run: `free -h`, `docker ps`, `dmesg | tail -20` (look for `Out of memory`)
3. Add swap (above), then redeploy
4. Prune if disk full: `docker system prune -f` (does not remove volumes)

## Build frontend on your PC (optional, low-RAM servers)

```bat
scripts\package-docker.bat
```

Build images locally and save/load — only if server builds keep failing after adding swap.

## `role "aitracker" does not exist`

The postgres **data volume was created with a different username** (often `tokentracker` from older deploy packages). The API is connecting as `aitracker`, which was never created.

### Quick fix (keeps data)

Edit `.env` on the server:

```bash
POSTGRES_USER=tokentracker
POSTGRES_PASSWORD=tokentracker
POSTGRES_DB=tokentracker
```

Then sync and restart:

```bash
cd /var/www/ai-tool-tracker
docker compose --profile prod up -d
```

Or test connection first:

```bash
docker exec -e PGPASSWORD=tokentracker ai-tracker-postgres \
  psql -U tokentracker -d tokentracker -c "SELECT 1"
```

### Reset database (loses data)

```bash
docker compose --profile prod down
docker volume rm ai-tracker-postgres-data
./scripts/deploy-docker.sh ai-tools-token-tracker.zip
```

---

## `password authentication failed for user "aitracker"`

Postgres **only sets the password when the data volume is first created**. If `.env` gets a new `POSTGRES_PASSWORD` but the volume `ai-tracker-postgres-data` already exists, the API cannot connect.

### Fix A — use the original password (keeps data)

1. Find the password from the **first** deploy (or old `.env` backup).
2. Edit `.env` on the server:

```bash
POSTGRES_USER=aitracker
POSTGRES_PASSWORD=<original-password>
```

3. Redeploy or restart:

```bash
cd /var/www/ai-tool-tracker   # your DEPLOY_ROOT
docker compose --profile prod up -d
```

Older packages used `tokentracker` / `tokentracker` — set those if that was your first deploy.

### Fix B — reset database (loses all data)

```bash
docker compose --profile prod down
docker volume rm ai-tracker-postgres-data
./scripts/deploy-docker.sh ai-tools-token-tracker.zip
```

A new password will be generated and postgres will initialize cleanly.

### Fix C — change password inside postgres to match `.env`

```bash
# Replace NEWPASS with POSTGRES_PASSWORD from .env
docker exec -it ai-tracker-postgres psql -U aitracker -d aitracker \
  -c "ALTER USER aitracker WITH PASSWORD 'NEWPASS';"
docker compose --profile prod restart api
```
