# TOXMAP Docker Troubleshooting Guide

Quick reference for diagnosing and recovering from common Docker issues in the local development stack.

---

## Contents

- [Quick-Start Checklist](#quick-start-checklist)
- [Container Reference](#container-reference)
- [FAQ & Common Issues](#faq--common-issues)
  - [1. App is stuck on "loading…" / data never appears](#1-app-is-stuck-on-loading--data-never-appears)
  - [2. Backend shows `(unhealthy)` but is `Up`](#2-backend-shows-unhealthy-but-is-up)
  - [3. Backend container exits immediately / won't stay up](#3-backend-container-exits-immediately--wont-stay-up)
  - [4. Postgres container is `(unhealthy)`](#4-postgres-container-is-unhealthy)
  - [5. Migrations haven't run / database tables are missing](#5-migrations-havent-run--database-tables-are-missing)
  - [6. Seed data is missing (T-01/T-03/T-04 tests fail)](#6-seed-data-is-missing-t-01t-03t-04-tests-fail)
  - [7. Port conflicts](#7-port-conflicts)
  - [8. Frontend can't reach the backend (API calls fail in browser)](#8-frontend-cant-reach-the-backend-api-calls-fail-in-browser)
  - [9. Hot-reload isn't picking up file changes](#9-hot-reload-isnt-picking-up-file-changes)
  - [10. Full stack restart (nuclear option)](#10-full-stack-restart-nuclear-option)
- [Useful One-Liners](#useful-one-liners)
- [Health Check Summary](#health-check-summary)

---

## Quick-Start Checklist

```bash
# 1. Check all containers are running and healthy
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. Verify the backend responds
curl -s http://localhost:8000/health

# 3. Check the frontend is reachable
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

All three containers should show `Up ... (healthy)` and the backend should return `{"status":"ok"}`.

---

## Container Reference

| Container | Internal port | Host port | Health check |
|---|---|---|---|
| `toxmap-postgres` | 5432 | **5433** | `pg_isready -U postgres -d toxmap` |
| `toxmap-backend` | 8000 | 8000 | `GET /health` |
| `toxmap-frontend` | 3000 | 3000 | *(none — Vite dev server)* |

> PostgreSQL is intentionally mapped to **5433** to avoid conflicts with a local Postgres on 5432.

---

## FAQ & Common Issues

---

### 1. App is stuck on "loading…" / data never appears

**Symptom:** The map loads but the TRI or Superfund layer shows "loading…" indefinitely. Browser DevTools shows requests hanging or returning 500.

**Cause:** The backend container is alive (listed by `docker ps`) but not actually serving requests — typically because uvicorn's WatchFiles hot-reload detected a file change and is hung on *"Waiting for connections to close."*

**Fix:**
```bash
docker restart toxmap-backend

# Confirm it's back up (should return {"status":"ok"})
curl -s http://localhost:8000/health
```

Then reload the browser tab.

---

### 2. Backend shows `(unhealthy)` but is `Up`

**Symptom:** `docker ps` shows `toxmap-backend` as `Up ... (unhealthy)`.

**Cause:** The healthcheck (`curl -f http://localhost:8000/health`) is failing. Most common cause is the uvicorn reload hang described above, or a Python startup error.

**Diagnosis:**
```bash
# Check recent logs for exceptions or reload messages
docker logs toxmap-backend --tail 50

# Look specifically for startup errors
docker logs toxmap-backend 2>&1 | grep -E "ERROR|Exception|Traceback"
```

**Fix:**
```bash
docker restart toxmap-backend
```

If it immediately goes unhealthy again, there is a Python error at startup — check the full logs:
```bash
docker logs toxmap-backend 2>&1 | tail -80
```

---

### 3. Backend container exits immediately / won't stay up

**Symptom:** `docker ps` shows the container as `Exited` or it keeps restarting.

**Diagnosis:**
```bash
docker logs toxmap-backend
```

**Common causes:**

| Log message | Fix |
|---|---|
| `could not connect to server` / `Connection refused` | Postgres isn't healthy yet; wait 10s and retry, or run `docker restart toxmap-backend` |
| `No module named '...'` | Dependency missing from image; rebuild: `docker compose build backend` |
| `SyntaxError` or `ImportError` | Python file has a syntax error; fix the file |
| `address already in use` (port 8000) | Something else is using port 8000; see [FAQ #7](#7-port-conflicts) |

---

### 4. Postgres container is `(unhealthy)`

**Symptom:** `docker ps` shows `toxmap-postgres` as unhealthy; backend won't start.

**Diagnosis:**
```bash
docker logs toxmap-postgres --tail 30
```

**Fix — restart postgres:**
```bash
docker restart toxmap-postgres
# Wait for it to become healthy (~15s), then restart the backend
docker restart toxmap-backend
```

**Fix — if the data volume is corrupted:**
```bash
# ⚠️ Destroys all local data — only use if the volume is truly broken
docker compose down -v
docker compose up -d
```

**Verify postgres is accepting connections:**
```bash
docker exec toxmap-postgres pg_isready -U postgres -d toxmap
```

---

### 5. Migrations haven't run / database tables are missing

**Symptom:** Backend logs show `relation "facilities" does not exist` or similar.

**Fix:**
```bash
docker compose exec backend alembic upgrade head
```

To check current migration state:
```bash
docker compose exec backend alembic current
docker compose exec backend alembic history --verbose
```

---

### 6. Seed data is missing (T-01/T-03/T-04 tests fail)

**Symptom:** Tests that rely on the `89319BHPCP7MILE` fixture facility fail; the facility doesn't exist in the database.

**Cause:** The seed file only runs automatically on the *first* Postgres start. If the volume already exists it won't rerun.

**Fix — reload seed data manually:**
```bash
docker compose exec postgres psql -U postgres -d toxmap \
  -f /docker-entrypoint-initdb.d/seed.sql
```

> Expected: the `TRUNCATE` at the top of `seed.sql` will print a notice on a fresh schema — this is safe to ignore.

---

### 7. Port conflicts

**Symptom:** A container fails to start with `address already in use` or `bind: address already in use`.

**Diagnosis:**
```bash
# Find what's using the conflicting port (replace 8000 with the relevant port)
lsof -i :8000
lsof -i :3000
lsof -i :5433
```

**Fix — kill the conflicting process:**
```bash
# Example: kill the process on port 8000
kill -9 $(lsof -ti :8000)
```

**Fix — if it's another Docker container:**
```bash
docker ps -a   # find the container
docker stop <container_id>
```

---

### 8. Frontend can't reach the backend (API calls fail in browser)

**Symptom:** Browser DevTools shows requests to `/api/v1/...` failing with `net::ERR_CONNECTION_REFUSED` or CORS errors.

**Note:** The frontend uses a **Vite proxy** (`/api → http://backend:8000`) rather than calling the backend directly from the browser. This is intentional — it routes through Node.js inside the container to bypass any corporate proxy (e.g. Netskope) that intercepts browser traffic.

**Fix — restart the frontend:**
```bash
docker restart toxmap-frontend
```

**Verify the Vite proxy is working:**
```bash
# Should return the same {"status":"ok"} as the direct health check
curl -s http://localhost:3000/api/health
```

---

### 9. Hot-reload isn't picking up file changes

**Symptom:** Editing a `.py` file in `backend/` or a `.tsx` file in `frontend/src/` doesn't trigger a rebuild.

**Backend (uvicorn):**
```bash
docker logs toxmap-backend --tail 10
# Should show: "WatchFiles detected changes in '...' Reloading..."
# If the reload hangs, restart the container:
docker restart toxmap-backend
```

**Frontend (Vite HMR):**
```bash
docker logs toxmap-frontend --tail 10
# If HMR is broken, restart the container:
docker restart toxmap-frontend
```

---

### 10. Full stack restart (nuclear option)

Stops everything, removes containers (but keeps the postgres data volume), and brings it back up fresh:

```bash
docker compose down
docker compose up -d

# Watch all services come up
docker compose logs -f
```

To also wipe the database volume (**destroys all local data**):
```bash
docker compose down -v
docker compose up -d
```

---

## Useful One-Liners

```bash
# Tail all service logs at once
docker compose logs -f

# Tail a single service
docker compose logs -f backend

# Open a psql shell
docker compose exec postgres psql -U postgres -d toxmap

# Run a one-off backend command (e.g. a migration)
docker compose exec backend alembic upgrade head

# Check container resource usage
docker stats toxmap-backend toxmap-postgres toxmap-frontend

# Force-rebuild the backend image (after Dockerfile or requirements changes)
docker compose build --no-cache backend && docker compose up -d backend

# Force-rebuild all images
docker compose build --no-cache && docker compose up -d
```

---

## Health Check Summary

```bash
# Full health sweep — run this when something feels wrong
echo "=== Container status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== Backend health ==="
curl -s http://localhost:8000/health

echo ""
echo "=== Postgres connectivity ==="
docker exec toxmap-postgres pg_isready -U postgres -d toxmap

echo ""
echo "=== Frontend proxy ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:3000/api/health
```
