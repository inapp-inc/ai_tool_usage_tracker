# Deployment Checklist — MVP Go-Live

Operational checklist for **Docker Compose deployment with local volumes**. Derived from [deployment.md](./deployment.md).

---

## Pre-release (staging)

### Docker host

- [ ] Docker Engine 24+ and Compose v2 installed on staging host
- [ ] Dedicated disk or partition for Docker volumes (Postgres, storage, backups)
- [ ] Host disk encryption enabled (recommended)
- [ ] Firewall: only proxy ports 80/443 public; DB/Redis **not** exposed

### Docker stack

- [ ] `docker compose -f docker-compose.yml -f docker-compose.prod.yml config` validates
- [ ] All services start healthy: postgres, redis, api, worker, beat
- [ ] Storage volume mounted — `uploads/` and `reports/` writable from api/worker
- [ ] Backend image builds; Trivy/scout scan shows no critical CVEs
- [ ] Frontend + nginx/proxy containers serve SPA and API routes
- [ ] `STORAGE_BACKEND=local` and `LOCAL_STORAGE_ROOT` configured

### Configuration & secrets

- [ ] Production `.env` on host (`chmod 600`) — not in Git
- [ ] All [environment variables](./deployment.md#3-environment-variables) set
- [ ] Redis AUTH enabled in production override
- [ ] CORS origins match frontend URL

### CI/CD

- [ ] PR pipeline green (lint, unit, integration, security, OpenAPI)
- [ ] Staging deploy workflow runs `compose up` successfully
- [ ] Alembic migration container completes before app recreate
- [ ] Rollback tested: redeploy previous image tag

### Monitoring & alerting

- [ ] Observability Compose profile starts (Prometheus, Grafana, OTel)
- [ ] Grafana dashboards show API latency, queue depth, disk usage
- [ ] Alert rules ALT-001 – ALT-007 tested on staging
- [ ] Container healthchecks fail correctly when Postgres stopped

### Backup & DR

- [ ] Daily `pg_dump` job writes to `backups_data` volume
- [ ] 30-day retention script verified
- [ ] Weekly storage tarball job configured
- [ ] Off-host rsync of `/backups` to NAS or second server (recommended)
- [ ] Restore drill completed on staging; RTO recorded (NFR-BKP-001)
- [ ] DR runbook draft reviewed (NFR-BKP-005)

### Testing gates

- [ ] Contract tests pass against staging API (TASK-OPS-004)
- [ ] E2E-001 – E2E-005 pass on staging Compose stack (TASK-OPS-007)
- [ ] Performance smoke PERF-001, PERF-006 pass

---

## Production release

### Deploy

- [ ] Release tag `v*` from validated staging commit
- [ ] Manual approval granted
- [ ] `docker compose pull` / build on production host
- [ ] Alembic migration one-shot container succeeds
- [ ] `docker compose up -d` — all containers healthy
- [ ] Post-deploy smoke: health, login, one dashboard widget, file upload to local storage

### Post-release (24h)

- [ ] No ALT-001 / ALT-002 / ALT-004 alerts
- [ ] Backup job succeeded overnight
- [ ] Storage and Postgres volume disk usage within limits
- [ ] Deploy recorded (git sha, image tag, approver)

---

## Rollback readiness

- [ ] Previous 3 image tags available on registry or host
- [ ] Last migration backward-compatible with previous app version
- [ ] Latest `pg_dump` verified restorable
- [ ] Rollback runbook shared with on-call

---

## Sign-off

| Role | Name | Date |
|------|------|------|
| Platform lead | | |
| QA | | |
| Security | | |
| Product owner | | |
