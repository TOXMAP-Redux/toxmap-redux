# TOXMAP Deployment Guide

**Last Updated:** 2026-07-23 (audited and corrected)  
**Audience:** Anyone deploying TOXMAP — no prior ops experience assumed  
**Related:** [ADR-004 (Hosting Strategy)](../adr/ADR-004-zero-budget-hosting.md) · [ADR-001 (Stack)](../adr/ADR-001-fastapi-postgis-react.md)

---

## Quick Decision: Which Guide Do You Need?

```
What are you trying to do?
│
├─ Run it on my laptop (develop / test)
│    └─► Part 1: Local Development (Docker Compose)
│
├─ Deploy the live public site (zero cost, no server)
│    └─► Part 2: Production — Cloudflare Pages + R2 + DuckDB WASM  ← DEFAULT
│
└─ Deploy with a live API backend (Fly.io + Supabase, 20-year data limit)
     └─► Part 3: Option B — Fly.io + Supabase  ← Only if you need server-side features
```

> **TL;DR for most people:** Do Part 1 to develop locally, then Part 2 to go live. Part 3 is optional.

---

## Ownership Key

| Badge | Meaning |
|-------|---------|
| 🤖 **Agent** | Artifact is written and committed to the repo by the DevOps agent — the file already exists; no human needs to create it |
| 👤 **Human** | A human must perform this action — requires a browser session, an authenticated CLI, account creation, or injecting secrets into a live service |
| ⚡ **Auto** | Runs automatically via agent-written GitHub Actions workflows after one-time setup — no human needed on repeat runs |

Many steps are **🤖 + 👤**: the agent pre-builds the file or config; a human runs it once or provides credentials.  
Steps marked **👤 (one-time)** only need to be done once per deployment environment and are never repeated.

---

## Part 1: Local Development (Docker Compose)

This gets the full stack — FastAPI backend, PostgreSQL + PostGIS, and the React frontend — running on your machine in
one command. Use this for development and running acceptance tests.

**Time to complete:** ~20 minutes (most of that is waiting for Docker images to download)

---

### Step 1.1 — Install Prerequisites — 👤 Human

You need these tools on your machine:

| Tool | Minimum Version | Check if installed | Install |
|------|-----------------|--------------------|---------|
| **Docker Desktop** | 4.24+ (bundles Docker Engine 24+) | `docker --version` | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| **Git** | 2.x+ | `git --version` | Comes with macOS Xcode Command Line Tools (`xcode-select --install`); [git-scm.com](https://git-scm.com) on Windows |
| **Python** | 3.12+ | `python3 --version` | [python.org/downloads](https://www.python.org/downloads/) — macOS does **not** bundle Python 3.12; install separately |
| **Node.js + npm** | Node 20+ | `node --version && npm --version` | [nodejs.org](https://nodejs.org/en/download) — required for Wrangler CLI in Part 2 |

> ⚠️ **Docker Desktop must be running** before any `docker` commands work. Open it from your Applications folder and
> wait for the whale icon in your menu bar to stop animating.

---

### Step 1.2 — Clone the Repository — 👤 Human

> **Who does what:** The DevOps agent creates the repo structure and branch protection rules in Phase 0 (story 0.1.1). The developer runs `git clone`.

```bash
git clone https://github.com/TOXMAP-Redux/toxmap-redux.git
cd toxmap-redux
```

---

### Step 1.3 — Create Environment Files — 🤖 Agent artifact · 👤 Human copies

> **Who does what:** The DevOps agent writes `.env.example` files with correct defaults. The developer copies them and fills in any environment-specific values (none required for local dev — defaults work as-is).

```bash
# Backend configuration
cp backend/.env.example backend/.env

# Frontend configuration
cp frontend/.env.example frontend/.env
```

**Edit `backend/.env`** — the defaults work for local dev, nothing to change unless you want a custom DB password:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/toxmap
DATABASE_URL_SYNC=postgresql+psycopg2://postgres:postgres@localhost:5432/toxmap
DATABASE_URL_TEST=postgresql+psycopg2://postgres:postgres@localhost:5432/toxmap_test
ALLOWED_ORIGINS=http://localhost:3000
```

> **Note on `DATABASE_URL_TEST`:** The `toxmap_test` database is **not** created automatically by Docker Compose.
> Run `docker compose exec db createdb -U postgres toxmap_test` once after first boot to create it before running
> the test suite.

**Edit `frontend/.env`** — the defaults work for local dev:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_DATA_SOURCE=api
VITE_MAPLIBRE_STYLE=https://tiles.openfreemap.org/styles/liberty
VITE_NOMINATIM_UA=toxmap-clone/0.1 (github.com/TOXMAP-Redux/toxmap-redux)
```

> ⚠️ **Never put secrets in `VITE_`-prefixed variables.** Everything prefixed `VITE_` is bundled into the public
> JavaScript and visible to anyone who views source. It's fine for URLs; never use it for passwords or API keys.

---

### Step 1.4 — Start All Services — 🤖 Agent artifact · 👤 Human executes

> **Who does what:** The DevOps agent writes `docker-compose.yml` (story 0.2.1), the `backend/Dockerfile` skeleton (story 0.2.3), and the `frontend/Dockerfile` skeleton (story 0.2.4). The developer runs `docker compose up`.

```bash
docker compose up
```

This starts three containers:
- `db` — PostgreSQL 16 + PostGIS 3.4 on port 5432
- `backend` — FastAPI on port 8000
- `frontend` — React (Vite dev server) on port 3000

**What you'll see in the terminal:**

```
[db]       database system is ready to accept connections
[backend]  INFO:     Application startup complete.
[backend]  INFO:     Uvicorn running on http://0.0.0.0:8000
[frontend] VITE v5.x.x  ready in 800 ms
[frontend] ➜  Local:   http://localhost:3000/
```

Wait until all three lines above appear. The database takes ~10 seconds to be ready on first boot.

> ⚠️ **If port 5432 is already in use:** Another PostgreSQL is running on your machine. Either stop it
> (`brew services stop postgresql`) or change the host port in `docker-compose.yml` from `"5432:5432"` to
> `"5433:5432"` and update your `DATABASE_URL` accordingly.

---

### Step 1.5 — Apply Database Migrations — 🤖 Agent artifact · 👤 Human executes

> **Who does what:** The Backend and Data Engineering agents write Alembic migration files. The developer runs `alembic upgrade head` to apply them. Must be re-run whenever new migrations are added by agents.

```bash
docker compose exec backend alembic upgrade head
```

You should see:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial schema
INFO  [alembic.runtime.migration] Running upgrade 0001 -> 0002, add superfund
...
```

> **Why this step exists:** Docker starts the database container, but the schema (tables, indexes, PostGIS extensions)
> is applied separately via Alembic migrations. You only need to do this once — and again whenever migrations are added.

---

### Step 1.6 — Ingest TRI Data — 🤖 Agent artifact · 👤 Human executes

> **Who does what:** The Data Engineering agent writes `ingestion/tri_ingest.py` and all ingestion scripts. The developer downloads the EPA CSV and runs the ingestion command. In production this step is replaced by the automated Parquet build pipeline (Part 2).

```bash
# Download the 2024 TRI dataset from EPA (about 200 MB)
# Go to: https://www.epa.gov/toxics-release-inventory-tri-program/tri-basic-data-files-calendar-years-1987-present
# Download "TRI_2024_US.zip" → unzip it → you'll have a file named something like "tri_2024_us.csv"

# Then ingest it
docker compose exec backend python -m ingestion.tri_ingest --year 2024 --file /path/to/tri_2024_us.csv
```

> **Shortcut for testing:** Load just the seed data that powers the acceptance tests. These are the minimal records
> needed to verify the app works:
> ```bash
> docker compose exec backend python -m ingestion.seed --fixtures tests/fixtures/seed.sql
> ```

---

### Step 1.7 — Verify It Works — 👤 Human

Open these URLs in your browser:

| URL | What you should see |
|-----|---------------------|
| `http://localhost:3000` | Interactive map centered on the US |
| `http://localhost:8000/docs` | FastAPI auto-generated API docs (Swagger UI) |
| `http://localhost:8000/api/v1/facilities?lat=39.22&lon=-76.48&radius_miles=25` | JSON array of facilities |

**Smoke test from the command line:**

```bash
curl http://localhost:8000/api/v1/facilities?lat=39.22&lon=-76.48&radius_miles=25 | python3 -m json.tool
```

If you get a JSON response with a `features` array, you're done. The app is running.

---

### Step 1.8 — Stopping and Restarting — 👤 Human

```bash
# Stop all containers (keeps your data)
docker compose down

# Stop and DELETE all data (fresh start)
docker compose down -v

# Start again
docker compose up
```

> After a clean `docker compose up` (without `-v`), your ingested TRI data persists in the Docker volume. You do
> **not** need to re-run migrations or re-ingest data after a normal restart.

---

### Step 1.9 — Run the Test Suite — 🤖 Agent artifact · 👤 Human (locally) · ⚡ Auto (CI)

> **Who does what:** The QA agent writes pytest tests; the DevOps agent writes `.github/workflows/ci.yml` (story 0.3.1) which runs them automatically on every PR. The developer runs tests manually via the commands below. On CI, tests run automatically — no human needed.

```bash
# Run unit + integration tests against the local stack
docker compose exec backend pytest

# Run E2E Playwright tests (requires the app to be running on localhost:3000)
docker compose exec backend pytest tests/e2e/
```

---

## Part 2: Production Deployment — Cloudflare Pages + R2 + DuckDB WASM

This is the primary zero-cost public deployment. There is **no server** in production — TRI data is pre-built into
Parquet files, hosted on Cloudflare R2 (static storage), and queried directly in the browser using DuckDB WebAssembly.

**Time to complete:** ~60 minutes (first time), ~15 minutes thereafter

**Monthly cost: $0.00**

---

### Overview of What You're Setting Up

```
GitHub Actions (runs 3x/year)
  └─► Python script: EPA CSV → Parquet files
        └─► Uploads Parquet to Cloudflare R2 (free static storage)

Cloudflare Pages (free CDN)
  └─► Hosts the React app bundle (~2 MB)
        └─► Browser runs DuckDB WASM
              └─► Queries Parquet files on R2 via HTTP range requests
```

No server. No database. No cold starts. No credit card required.

---

### Step 2.1 — Create a Cloudflare Account — 👤 Human (one-time)

> **Who does what:** Human only. Requires email verification and browser interaction. Done once per deployment environment; never repeated.

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) and click **Sign Up**
2. Enter your email and choose a password
3. Verify your email address
4. You're now on the Cloudflare free plan

> ⚠️ **Cloudflare R2 requires a credit card on file for identity verification**, even on the free tier. Pages alone
> does not require one. Have a card ready before proceeding to Step 2.3.

---

### Step 2.2 — Install the Wrangler CLI — 👤 Human (one-time)

> **Who does what:** Human only. `wrangler login` opens an OAuth browser pop-up that requires a logged-in Cloudflare session — an agent cannot authenticate against a live account.

Wrangler is Cloudflare's command-line tool. You'll use it to configure R2 and deploy.

> **Prerequisite:** Node.js 20+ and npm must be installed (see Step 1.1). Verify with `node --version`.

```bash
npm install -g wrangler
```

Verify it installed:

```bash
wrangler --version
# Should print: ⛅️ wrangler X.x.x  (version number will vary — any 3.x or later is fine)
```

Now log in:

```bash
wrangler login
```

This opens a browser window. Click **Allow** to grant Wrangler access to your Cloudflare account.

---

### Step 2.3 — Create the R2 Bucket — 👤 Human (one-time)

> **Who does what:** Human runs this CLI command against their authenticated Cloudflare account. Done once; the bucket persists indefinitely on the free tier.

```bash
wrangler r2 bucket create toxmap-data
```

You should see:

```
✅ Created bucket 'toxmap-data'
```

---

### Step 2.4 — Configure CORS on the R2 Bucket — 👤 Human (one-time)

> **Who does what:** The CORS rules themselves are specified by the DevOps agent in ADR-004 and the deployment workflow. The human pastes and runs the `wrangler` command to apply them to the live bucket. Repeated once more in Step 2.11 after the real Pages URL is known.

```bash
wrangler r2 bucket cors put toxmap-data --rules '[
  {
    "AllowedOrigins": ["https://toxmap.pages.dev", "http://localhost:3000"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["Range", "Content-Type"],
    "ExposeHeaders": ["Content-Length", "Content-Range", "Accept-Ranges"],
    "MaxAgeSeconds": 86400
  }
]'
```

> ⚠️ **Replace `toxmap.pages.dev` with your actual Cloudflare Pages URL** once you know it (you'll get it in
> Step 2.10, after the first deploy). You can re-run this exact command in Step 2.11 to update it. Until then,
> `toxmap.pages.dev` is the default domain Cloudflare assigns and serves as a safe placeholder.

---

### Step 2.5 — Get Your R2 Public URL — 👤 Human (one-time)

> **Who does what:** Human only — requires navigating the Cloudflare dashboard to enable public access and copy the generated URL. The URL is then used as the `VITE_R2_BASE_URL` secret value.

Enable public access on the bucket:

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com)
2. In the left sidebar, click **R2 Object Storage**
3. Click on **toxmap-data**
4. Click **Settings** → scroll to **Public Access**
5. Click **Allow Access** → confirm

Your public URL will look like: `https://pub-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX.r2.dev`

Copy this URL — you'll need it in Step 2.8.

---

### Step 2.6 — Add GitHub Secrets for Automated Deployment — 👤 Human (one-time)

> **Who does what:** Human only. Creating the Cloudflare API token requires a logged-in Cloudflare browser session. Injecting secrets into GitHub requires a GitHub account with repo write access. These are identity-gated operations an agent cannot perform.

**Create a Cloudflare API token:**

1. Go to [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Click **Create Token**
3. Click **Use template** next to **Edit Cloudflare Workers**
4. Under **Permissions**, verify or add: `Account > R2 Storage > Edit`
5. Under **Permissions**, also add: `Account > Cloudflare Pages > Edit`
6. Click **Continue to summary** → **Create Token**
7. Copy the token (you won't see it again)

**Add the token to GitHub:**

1. Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `CF_API_TOKEN`
4. Value: paste the token you just copied
5. Click **Add secret**

---

### Step 2.7 — Set Up the GitHub Actions Data Pipeline — 🤖 Agent writes workflow · 👤 Human triggers first run · ⚡ Auto (3×/year cron)

> **Who does what:**
> - **Agent:** The DevOps agent writes `.github/workflows/build-data.yml` with all three cron triggers and the R2 upload logic (story 1.5.2). The file is already in the repo.
> - **Human:** Triggers the *first* manual run via the GitHub Actions UI to seed R2 with initial data.
> - **Automated:** From then on, the workflow fires automatically on the three EPA data checkpoints (Aug, Oct, Apr) — no human needed for routine data updates.

The data build workflow is already defined in the repository. Trigger it manually to do your first build:

1. Go to your GitHub repository
2. Click the **Actions** tab
3. In the left sidebar, click **Build TRI Data**
4. Click **Run workflow** (top right)
5. Fill in the inputs:
   - **TRI years to rebuild:** `2024` (or `latest`)
   - **Human-readable vintage label:** `October 2025 freeze`
6. Click **Run workflow**

The workflow will:
1. Download Python dependencies (pandas, geopandas, pyarrow)
2. Download TRI CSV from EPA
3. Convert CSV → Parquet files with vintage metadata
4. Upload Parquet files to your R2 bucket

**Watch it run:** Click on the running workflow to see live logs. It takes ~10 minutes.

When it finishes, verify the files are in R2:

```bash
wrangler r2 object list toxmap-data
```

You should see files like `tri_2024.parquet` and `tri_2024.meta.json`.

> ⚠️ **TRI data is NOT read-only and is NOT updated just once a year.** The EPA updates the public database at three
> checkpoints: a **preliminary release in August**, an **authoritative data freeze in October**, and a **spring data
> refresh in April**. The GitHub Actions workflow is pre-configured to run automatically at all three checkpoints via
> scheduled cron triggers. You can also trigger it manually at any time. Never skip the October freeze — it is the
> authoritative dataset used in EPA's National Analysis.

---

### Step 2.8 — Configure Frontend Environment Variables for Production — 🤖 Agent writes template · 👤 Human fills values

> **Who does what:** The DevOps agent writes `frontend/.env.example` with the correct variable names and placeholder values. The human copies it to `.env.production` and substitutes the real R2 public URL from Step 2.5. For fully automated deploys (Step 2.12), these values are stored as GitHub Secrets instead of a local file.

Create a production environment file for the frontend:

```bash
cp frontend/.env.example frontend/.env.production
```

Edit `frontend/.env.production`:

```bash
VITE_DATA_SOURCE=duckdb
VITE_R2_BASE_URL=https://pub-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX.r2.dev
VITE_MAPLIBRE_STYLE=https://tiles.openfreemap.org/styles/liberty
VITE_NOMINATIM_UA=toxmap-clone/0.1 (github.com/TOXMAP-Redux/toxmap-redux)
```

Replace the `VITE_R2_BASE_URL` value with the public URL you copied in Step 2.5.

> **Note:** `VITE_DATA_SOURCE=duckdb` tells the frontend to use DuckDB WASM (the in-browser SQL engine) instead of
> the FastAPI backend. This is the production mode — no server required.

---

### Step 2.9 — Build the Frontend — 🤖 Agent writes build config · 👤 Human (locally) · ⚡ Auto (in deploy workflow)

> **Who does what:** The DevOps agent writes `frontend/Dockerfile`, `vite.config.ts` skeleton, and the build step in `deploy-frontend.yml`. Running `npm run build` manually here is only needed for an initial smoke test — once Step 2.12 is configured, the deploy workflow runs the build automatically on every push to `main`.

```bash
cd frontend
npm install
npm run build
```

This produces a `frontend/dist/` directory with the compiled React app. It should complete in ~30 seconds.

**Verify the build succeeded:**

```bash
ls frontend/dist/
# You should see: index.html  assets/  ...
```

---

### Step 2.10 — Deploy to Cloudflare Pages — 👤 Human (first deploy) · ⚡ Auto (every push to `main` after Step 2.12)

> **Who does what:** The first deploy must be triggered manually via `wrangler pages deploy` — this is what creates the Pages project and assigns the `toxmap.pages.dev` URL. All subsequent deploys are automated by the `deploy-frontend.yml` workflow the agent writes in Step 2.12.

```bash
wrangler pages deploy frontend/dist --project-name toxmap
```

The first time you run this, Wrangler will:
1. Ask you to create a new Pages project — say **yes**
2. Choose your branch (usually `main`)
3. Upload and deploy your app

When it finishes, you'll see:

```
✅ Successfully deployed!
🌎 https://toxmap.pages.dev
```

Open that URL in your browser. You should see the TOXMAP map interface. 🎉

---

### Step 2.11 — Update CORS with Your Real URL — 👤 Human (one-time)

> **Who does what:** Human only — requires the Pages URL from Step 2.10 (not known until the first deploy runs) and an authenticated `wrangler` session. Done once; never repeated unless the domain changes.

Now that you know your Pages URL, update the R2 CORS config to use it:

```bash
wrangler r2 bucket cors put toxmap-data --rules '[
  {
    "AllowedOrigins": ["https://toxmap.pages.dev"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["Range", "Content-Type"],
    "ExposeHeaders": ["Content-Length", "Content-Range", "Accept-Ranges"],
    "MaxAgeSeconds": 86400
  }
]'
```

> **If you have a custom domain** (e.g., `toxmap.yourdomain.com`), add it to `AllowedOrigins` alongside
> `toxmap.pages.dev`.

---

### Step 2.12 — Automate Future Deployments via GitHub Actions — 🤖 Agent writes `deploy-frontend.yml` · 👤 Human adds `CF_ACCOUNT_ID` and `VITE_R2_BASE_URL` secrets

> **Who does what:**
> - **Agent:** The DevOps agent writes `.github/workflows/deploy-frontend.yml` (story 7.2.1). This file is already committed to the repo.
> - **Human:** Adds two secrets to GitHub (`CF_ACCOUNT_ID` and `VITE_R2_BASE_URL`) — these require dashboard access. Once added, no further human action is needed for deploys.
> - **Automated:** Every push to `main` → CI passes → Cloudflare Pages deploys automatically.

**Add these secrets to GitHub** (same place as Step 2.6):

| Secret name | Value |
|-------------|-------|
| `CF_API_TOKEN` | Already added in Step 2.6 |
| `CF_ACCOUNT_ID` | Your Cloudflare account ID — find it in the Cloudflare dashboard URL: `dash.cloudflare.com/{this-is-your-account-id}/` |
| `VITE_R2_BASE_URL` | Your R2 public URL from Step 2.5 |

**The `deploy-frontend.yml` workflow (already in the repo):**

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install dependencies
        run: npm ci
        working-directory: frontend
        # npm ci requires a committed package-lock.json — make sure it is checked into the repo

      - name: Build
        run: npm run build
        working-directory: frontend
        env:
          VITE_DATA_SOURCE: duckdb
          VITE_R2_BASE_URL: ${{ secrets.VITE_R2_BASE_URL }}
          VITE_MAPLIBRE_STYLE: https://tiles.openfreemap.org/styles/liberty
          VITE_NOMINATIM_UA: toxmap-clone/0.1 (github.com/${{ github.repository }})

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CF_API_TOKEN }}
          accountId: ${{ secrets.CF_ACCOUNT_ID }}
          command: pages deploy frontend/dist --project-name toxmap
```

> ⚠️ **Security note:** The `cloudflare/wrangler-action@v3` tag is mutable — it can change without notice.
> Pin to a specific commit SHA for production use. **The SHA below is an example only and may be outdated** — always
> look up the current release SHA before using:
> `uses: cloudflare/wrangler-action@<SHA-from-releases-page>`
> Check [github.com/cloudflare/wrangler-action/releases](https://github.com/cloudflare/wrangler-action/releases)
> for the latest verified SHA.

---

### Step 2.13 — Verify Production is Working — 👤 Human

Run these checks:

1. **Open the app** → `https://toxmap.pages.dev` → map loads, centered on the US ✅
2. **Search for facilities** → type a chemical name → results appear on the map ✅
3. **Check browser console** → no CORS errors in DevTools (F12 → Console) ✅
4. **Test on Safari mobile** → app either uses DuckDB WASM (Safari 16.4+) or automatically falls back to a
   message explaining limited browser support ✅

**Check data vintage in the UI:** The app should display a label like _"Data: October 2025 freeze"_ sourced from the
`.meta.json` sidecar file. If this is missing, re-run the data build with a `vintage_label` input.

---

## Part 3: Option B — Fly.io + Supabase (Server-Side API)

Use this **only** if you need features that require a live server:
- Real-time data that changes faster than the EPA update schedule
- Multi-user state or user accounts
- Server-side query validation beyond what the React layer provides
- The last 20 years of TRI data (2005–present) in a queryable SQL database

> ⚠️ **Data limitation:** Supabase's free tier is 500 MB. This holds approximately 20 years of TRI data
> (2005–present, ~300 MB). Full 1987–present history requires Option A (Part 2) Parquet files.

**Time to complete:** ~45 minutes

---

### Step 3.1 — Create a Supabase Project — 👤 Human (one-time)

> **Who does what:** Human only. Requires browser-based account creation, project naming, and password selection. The project takes ~2 minutes to provision.

1. Go to [supabase.com](https://supabase.com) → **Start your project** → **Sign up** (free)
2. Click **New project**
3. Fill in:
   - **Name:** `toxmap`
   - **Database Password:** choose a strong password, save it in a password manager — you'll need it
   - **Region:** pick the region closest to your users (e.g., **East US (North Virginia)** for East Coast US — Supabase uses full region names, not AWS-style identifiers like `us-east-1`)
4. Click **Create new project** — takes ~2 minutes to provision

When ready, go to **Settings** → **Database** and copy:
- **Host:** `db.xxxxxxxxxxxx.supabase.co`
- **Port:** `5432`
- **Database name:** `postgres`
- **User:** `postgres`
- **Password:** the one you chose above

Build your `DATABASE_URL`:
```
postgresql+asyncpg://postgres:<password>@db.xxxxxxxxxxxx.supabase.co:5432/postgres
```

---

### Step 3.2 — Verify PostGIS is Enabled on Supabase — 👤 Human (one-time)

> **Who does what:** Human only — requires the Supabase SQL Editor in a logged-in browser session.

In the Supabase dashboard:
1. Go to **SQL Editor**
2. Run: `SELECT postgis_version();`
3. If you get a version number (e.g., `3.4 USE_GEOS=1 USE_PROJ=1`), PostGIS is enabled ✅
4. If you get an error, run: `CREATE EXTENSION IF NOT EXISTS postgis;` — then retry

---

### Step 3.3 — Apply Migrations to Supabase — 👤 Human (one-time)

> **Who does what:** Human runs Alembic against the live Supabase DB using credentials from Step 3.1. The migration files themselves are written by the Backend agent — the human only provides the live `DATABASE_URL` and runs the command.

```bash
# From your local machine, inside the repo
cd backend

# Ensure alembic and psycopg2-binary are installed locally (not just inside Docker)
pip install alembic psycopg2-binary

# Set the production DB URL temporarily
# Use single quotes to prevent the shell from interpreting special characters in the URL
export DATABASE_URL='postgresql+psycopg2://postgres:<password>@db.xxxxxxxxxxxx.supabase.co:5432/postgres'

# Run migrations
alembic upgrade head
```

You should see migration steps running. When done, verify in Supabase SQL Editor:

```sql
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
```

You should see: `facilities`, `chemicals`, `release_events`, `superfund_sites`, `census_county`, etc.

---

### Step 3.4 — Ingest TRI Data into Supabase — 👤 Human (one-time, ~30–40 min)

> **Who does what:** Human runs the loop. The ingestion scripts are written by the Data Engineering agent. This is the most time-consuming one-time step — it can be left running unattended.

> **Note:** Unlike local dev (Step 1.6), this ingestion script **automatically downloads** each year's TRI CSV
> from the EPA at runtime — you do not need to manually download files beforehand. Ensure you have a stable
> internet connection and ~5 GB of free disk space for the temporary downloads.

```bash
cd backend

for year in 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025; do
  echo "Ingesting $year..."
  DATABASE_URL='postgresql+psycopg2://postgres:<password>@db.xxxxxxxxxxxx.supabase.co:5432/postgres' \
    python -m ingestion.tri_ingest --year $year
done
```

This will take 20–40 minutes. Monitor progress in the terminal.

---

### Step 3.5 — Create a Fly.io Account — 👤 Human (one-time)

> **Who does what:** Human only. Account creation and `fly auth login` require browser interaction and identity verification.

1. Go to [fly.io](https://fly.io) → **Sign up** (free, no credit card for the free tier)
2. Install the Fly CLI:
   ```bash
   brew install flyctl          # macOS
   # or
   curl -L https://fly.io/install.sh | sh   # Linux/macOS
   ```
3. Log in:
   ```bash
   fly auth login
   ```

---

### Step 3.6 — Deploy FastAPI to Fly.io — 🤖 Agent writes `fly.toml` · 👤 Human runs `fly launch` / `fly deploy`

> **Who does what:** The DevOps agent writes `fly.toml` with the correct VM sizing, health check, and auto-stop settings (specified in ADR-004). The human runs `fly launch`, injects secrets via `fly secrets set`, and runs `fly deploy` against their authenticated Fly.io account.

**`fly.toml` (already in the repo, written by the agent):**

```toml
app = "toxmap-api"
primary_region = "iad"   # Washington DC — change to match your target geography
                          # See https://fly.io/docs/reference/regions/ for all region codes

[build]
  dockerfile = "backend/Dockerfile"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[vm]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1
```

Deploy:

```bash
fly launch --no-deploy    # creates the app on Fly.io without deploying yet
fly secrets set DATABASE_URL="postgresql+asyncpg://postgres:<password>@db.xxxxxxxxxxxx.supabase.co:5432/postgres"
fly secrets set ALLOWED_ORIGINS="https://toxmap.pages.dev"
fly deploy
```

When the deploy completes, you'll see:

```
✅ v1 deployed successfully
🌎 https://toxmap-api.fly.dev
```

Verify the API is responding:

```bash
curl https://toxmap-api.fly.dev/api/v1/facilities?lat=39.22&lon=-76.48&radius_miles=25
```

---

### Step 3.7 — Point the Frontend at the Fly.io API — 👤 Human

> **Who does what:** Human updates env vars and triggers a redeploy. The deploy workflow that executes it is agent-written — the human only changes the variable values.

Update `frontend/.env.production` (or GitHub Actions env vars):

```bash
VITE_DATA_SOURCE=api
VITE_API_BASE_URL=https://toxmap-api.fly.dev
```

Rebuild and redeploy the frontend (follow Part 2, Steps 2.9–2.10).

---

### Step 3.8 — Prevent Supabase Free Tier Pausing — 🤖 Agent writes `keep-alive.yml` · ⚡ Auto (weekly cron)

> **Who does what:** The DevOps agent writes `.github/workflows/keep-alive.yml` with the weekly cron. The human merges the PR that adds it. After merge, it runs automatically every Monday — no further human action needed.

**`keep-alive.yml` (already in the repo, written by the agent):**

```yaml
# .github/workflows/keep-alive.yml
name: Keep Supabase Alive

on:
  schedule:
    - cron: "0 12 * * 1"   # Every Monday at noon UTC

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping API
        run: curl -s https://toxmap-api.fly.dev/health > /dev/null
```

This pings the Fly.io API once a week, which in turn keeps a Supabase connection alive.

> ⚠️ **The `/health` endpoint must exist in the FastAPI application.** This workflow will fail silently if the
> endpoint returns a non-2xx status or doesn't exist. Verify it is defined in the backend (e.g.,
> `@app.get("/health") async def health(): return {"status": "ok"}`) before relying on this keep-alive.

---

## Updating TRI Data (All Options)

TRI data has **three update checkpoints per year**. Missing the October freeze means your data is incomplete.

| When | What | Who | Action required |
|------|------|-----|-----------------|
| ~August 15 | EPA releases preliminary dataset | ⚡ Auto (cron) or 👤 Human (manual) | Cron fires automatically; or trigger manually with label `"August YYYY preliminary"` |
| ~October 20 | **EPA data freeze — authoritative** | ⚡ Auto (cron) — **do not disable** | Cron fires on Oct 20; verify it ran in the Actions tab |
| ~April 1 | EPA spring data refresh | ⚡ Auto (cron) or 👤 Human (manual) | Cron fires automatically; or trigger manually with label `"April YYYY spring refresh"` |

> **The three cron triggers in `build-data.yml` are written by the DevOps agent and run without any human action.** A human only needs to intervene to trigger an *out-of-schedule* rebuild (e.g., EPA releases a correction mid-year) or to verify the run completed successfully.

**To trigger a manual build:**

1. Go to GitHub repository → **Actions** → **Build TRI Data**
2. Click **Run workflow**
3. Enter years and vintage label
4. Click **Run workflow**

The workflow uploads new Parquet files to R2 and the live site automatically picks them up — no frontend redeployment needed.

---

## Troubleshooting

### "CORS error" in the browser console

**Symptom:** Browser console shows `Access to fetch at '...' from origin '...' has been blocked by CORS policy`

**Fix:** Your R2 CORS config is missing your Pages domain. Re-run Step 2.4/2.11 with the correct `AllowedOrigins`.

---

### DuckDB WASM fails to load in Safari

**Symptom:** Map loads but no data appears; browser console shows a WASM error

**Cause:** Safari versions before 16.4 do not support WebAssembly SIMD, which DuckDB requires.

**Fix:** The app should automatically detect this and display a "browser not supported" message. If it doesn't,
check that `duckdbCompat.ts` is correctly imported in `App.tsx`.

**Workaround for users:** Tell them to upgrade Safari, or use Chrome/Firefox.

---

### Fly.io cold start — API takes ~2 seconds to respond

**Symptom:** First request to the API after a period of inactivity is slow

**Cause:** `min_machines_running = 0` in `fly.toml` means the VM shuts down when idle. First request wakes it up.

**Fix (if acceptable cost):** Set `min_machines_running = 1` in `fly.toml` and redeploy. This keeps one VM always
running, using more of your free quota but eliminating cold starts.

---

### `alembic upgrade head` fails with "PostGIS extension not found"

**Symptom:** Migration fails with `could not open extension control file ... postgis.control`

**Fix (Docker):** The `postgis/postgis:16-3.4` Docker image has PostGIS pre-installed. If you're using a plain
`postgres:16` image, switch to `postgis/postgis:16-3.4` in `docker-compose.yml`.

**Fix (Supabase):** Follow Step 3.2 — PostGIS must be enabled via the Supabase SQL Editor.

---

### Parquet files not appearing in R2

**Symptom:** GitHub Actions workflow succeeded but `wrangler r2 object list toxmap-data` shows no files

**Check 1:** Did the `CF_API_TOKEN` secret have R2 write permissions? Re-create the token with `R2 Storage > Edit`
permission (Step 2.6).

**Check 2:** Check the Actions log for the `Upload to Cloudflare R2` step for error messages.

---

### "Database is paused" error from Supabase

**Symptom:** API returns 500 errors; Fly.io logs show a database connection error mentioning "paused"

**Fix:** Log into [supabase.com](https://supabase.com), open your project, and click **Restore project**. Takes ~60
seconds. Then set up the keep-alive workflow (Step 3.8) to prevent this happening again.

---

### Docker Compose: frontend container restarts in a loop

**Symptom:** `docker compose ps` shows the `frontend` container restarting repeatedly

**Fix:**
```bash
docker compose logs frontend
```
Look for the error. Most common cause: a syntax error in `.env` file (e.g., unquoted `=` in a value). Fix the `.env`
file, then:
```bash
docker compose up --force-recreate frontend
```

---

## Reference: What Each File Controls

| File | What it does |
|------|-------------|
| `docker-compose.yml` | Local dev: defines db, backend, frontend services |
| `backend/.env` | Local backend config (DB URL, CORS origins) |
| `frontend/.env` | Local frontend config (API URL, data source) |
| `frontend/.env.production` | Production frontend config (R2 URL, DuckDB mode) |
| `fly.toml` | Fly.io deployment config for FastAPI (Option B only) |
| `.github/workflows/build-data.yml` | Automated TRI data pipeline (3x/year + manual) |
| `.github/workflows/deploy-frontend.yml` | Auto-deploy frontend on push to `main` |
| `.github/workflows/keep-alive.yml` | Weekly Supabase ping to prevent pausing (Option B only) |
| `backend/alembic/` | Database schema migrations — run with `alembic upgrade head` |
| `scripts/build_data.py` | Converts EPA TRI CSV → Parquet files for DuckDB WASM |

---

## Deployment Checklist

### Before Going Live (Production — Part 2)

- [ ] Cloudflare account created, Wrangler installed and logged in
- [ ] R2 bucket `toxmap-data` created
- [ ] R2 CORS configured with your actual Pages domain
- [ ] R2 public access enabled; public URL copied to `VITE_R2_BASE_URL`
- [ ] `CF_API_TOKEN` secret added to GitHub
- [ ] `CF_ACCOUNT_ID` secret added to GitHub
- [ ] GitHub Actions data build ran successfully; Parquet files visible in R2
- [ ] `frontend/.env.production` has `VITE_DATA_SOURCE=duckdb` and correct R2 URL
- [ ] `npm run build` succeeds locally
- [ ] `wrangler pages deploy` successful; Pages URL is live
- [ ] Map loads in browser; DuckDB queries return facility data
- [ ] No CORS errors in browser DevTools console
- [ ] Vintage label visible in the UI (from `.meta.json` sidecar)
- [ ] Automated deploy workflow (`deploy-frontend.yml`) committed to repo

### Data Update Checklist (3x/year)

- [ ] EPA checkpoint reached (Aug preliminary / **Oct freeze** / Apr refresh)
- [ ] GitHub Actions "Build TRI Data" triggered with correct vintage label
- [ ] Build completed successfully in Actions tab
- [ ] New `.parquet` and `.meta.json` files visible in R2
- [ ] Live site shows updated vintage label in the UI
- [ ] Spot-check: query a known facility to verify data accuracy

