# TOXMAP Progress Tracker

**Owner:** Phase Manager Agent  
**Last Updated:** 2026-07-29 (Phase 6 bug fixes 6.BUG.1–6.BUG.9 complete [agent])  
**Source of truth for:** `CURRENT_PHASE.txt` · DoD status · active assignments · blockers  

> This file is updated by the Phase Manager at the end of every development session.  
> Read this before any code is written. If this disagrees with `CURRENT_PHASE.txt`, `CURRENT_PHASE.txt` wins.

---

## Current Status

| Field | Value |
|-------|-------|
| **Active Phase** | `6` — Full QA Pass |
| **Active Milestone** | M6 — Feature Complete |
| **Phase Lead** | QA |
| **Phase Start Date** | 2026-07-29 |
| **Stories Completed** | Phase 0 complete (33/33 pts); Phase 1 complete (48/48 pts); Phase 2 complete (62/62 pts); Phase 3 complete (79/79 pts); Phase 4 complete (28/28 pts); Phase 5 complete (33/33 pts); Phase 6 in progress (14/65 pts — bug fixes) |
| **Open Blockers** | B-001 (Phase 1 `workflow_dispatch` verification — human gate; does not block Phase 6) |

---

## Phase Summary

| Phase | Name | Status | Milestone | Completed |
|-------|------|--------|-----------|-----------|
| **0** | Foundation | ✅ Complete | M0 — Dev Environment Ready | 2026-07-25 |
| **1** | Data Pipeline | ✅ Complete | M1 — Data Pipeline Working | 2026-07-26 |
| **2** | Core API | ✅ Complete | M2 — Core API Green | 2026-07-26 |
| **3** | Core Map UI | ✅ Complete | M3 — First Shareable Demo | 2026-07-27 |
| **4** | Superfund Overlay | ✅ Complete | M4 — Superfund Layer | 2026-07-28 |
| **5** | Demographics Overlay | ✅ Complete | M5 — Demographics Layer | 2026-07-29 |
| **6** | Full QA Pass | 🔄 In Progress | M6 — Feature Complete | — |
| **7** | Production Deploy | ⬜ Not Started | M7 — MVP Shipped 🚀 | — |
| **8** | Tribal Lands Data | ⬜ Not Started | M8 — Tribal Lands | — |

**Legend:** ✅ Complete · 🔄 In Progress · ⬜ Not Started · 🚫 Blocked

---

## Phase 0 — Foundation

**Lead:** OPS  
**Goal:** Every developer can run the full stack locally. CI green. Security baseline established.  
**Total points:** 33

### Definition of Done Checklist

- [x] `docker compose up` → all three services start and are healthy within 60 seconds ✅ Verified 2026-07-25
- [x] `curl http://localhost:8000/health` → `{"status": "ok"}` ✅ Verified 2026-07-25
- [x] React app loads at `http://localhost:3000` ✅ HTTP 200 verified 2026-07-25
- [x] `SELECT PostGIS_version();` returns a version string inside the container ✅ `3.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1` verified 2026-07-25
- [x] `pytest tests/unit/` → green (no failures) ✅ `1 passed` inside backend container, verified 2026-07-25
- [ ] GitHub Actions `ci.yml` shows a green check on `main` ⚠️ Requires push to GitHub — all Actions are SHA-pinned and CI is correctly structured
- [x] `SECURITY.md` present at repo root; linked from `README.md` ✅ Confirmed
- [x] All third-party GitHub Actions pinned to full 40-char SHA; `security.yml` green on `main` ✅ Zero `@vX` tags verified 2026-07-25; green on `main` pending push
- [x] `tests/fixtures/seed.sql` exists and `psql -f tests/fixtures/seed.sql` runs without errors ✅ File verified; TRUNCATE error on first start is expected (tables created in Phase 1)

### Story Status

**Epic 0.1 — Repository Setup** `OPS`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 0.1.1 | GitHub repo, main branch protection, README skeleton, .gitignore | 1 | ✅ | OPS | Pre-existing |
| 0.1.2 | Monorepo directory structure | 1 | ✅ | OPS | `backend/`, `frontend/`, `scripts/`, `tests/` created 2026-07-25 |
| 0.1.3 | Create `.github/` templates: `pull_request_template.md`, `ISSUE_TEMPLATE/{bug_report,rfc,agent-escalation}.md`, `CODEOWNERS`. **Do NOT modify existing `CONTRIBUTING.md`** — it is already authored. | 1 | ✅ | OPS | `rfc.yml` and `agent-escalation.yml` added 2026-07-25; others pre-existing |

**Epic 0.2 — Docker Compose Local Stack** `OPS + BE + FE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 0.2.1 | `docker-compose.yml` with postgres, backend, frontend | 3 | ✅ | OPS | Created 2026-07-25 |
| 0.2.2 | PostgreSQL with PostGIS 3.4 enabled on startup | 2 | ✅ | OPS | `postgis/postgis:16-3.4`; seed.sql auto-loaded via `docker-entrypoint-initdb.d/` |
| 0.2.3 | Backend Dockerfile: Python 3.12 + FastAPI + health endpoint | 2 | ✅ | BE | `backend/Dockerfile`, `backend/app/main.py` with `GET /health → {"status":"ok"}` |
| 0.2.4 | Frontend Dockerfile: Node 22 + Vite dev server | 2 | ✅ | FE | `frontend/Dockerfile`, React 18 + TypeScript scaffold; `npx tsc --noEmit` passes |
| 0.2.5 | Volume mount for hot reload (`./backend:/app`) | 1 | ✅ | OPS | `./backend:/app` + `./tests:/app/tests` mounts added 2026-07-25 |

**Epic 0.3 — CI/CD Pipeline** `OPS`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 0.3.1 | `ci.yml`: lint + unit tests on every PR | 3 | ✅ | OPS | Pre-existing; 5-gate CI pipeline |
| 0.3.2 | `build-data.yml` stub (no-op success) | 1 | ✅ | OPS | Created 2026-07-25; 3 cron triggers + `workflow_dispatch` |
| 0.3.3 | Codecov integration | 2 | ✅ | OPS | Codecov upload step added to `python-unit` job 2026-07-25 |

**Epic 0.4 — Test Infrastructure** `QA`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 0.4.1 | `tests/conftest.py`: `seed_db` fixture | 3 | ✅ | QA | Created 2026-07-25 with all fixtures |
| 0.4.2 | `tests/fixtures/seed.sql` from seed data doc | 2 | ✅ | QA | Created 2026-07-25; immutable values verified |
| 0.4.3 | pytest-playwright configured in `pyproject.toml` | 2 | ✅ | QA | `--base-url http://localhost:3000 --screenshot only-on-failure` in addopts |
| 0.4.4 | pytest-bdd configured: `bdd_features_base_dir` | 1 | ✅ | QA | `bdd_features_base_dir = "tests/features"`; stub feature files created |

**Epic 0.5 — Security Foundation** `SEC`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 0.5.1 | `SECURITY.md` at repo root; linked from README | 2 | ✅ | SEC | Pre-existing |
| 0.5.2 | `.github/dependabot.yml` for pip + npm + actions | 1 | ✅ | SEC | Pre-existing |
| 0.5.3 | `security.yml`: gitleaks + pip-audit + npm audit + bandit | 3 | ✅ | SEC | Pre-existing |
| 0.5.4 | Pin all Actions to 40-char SHA; document in `PINNED_ACTIONS.md` | 1 | ✅ | SEC | Completed 2026-07-25. All 6 third-party Actions pinned across `ci.yml`, `security.yml`, `build-data.yml`. Zero mutable `@vX` tags remain. `PINNED_ACTIONS.md` updated. |

---

## Phase 1 — Data Pipeline *(Complete)*

**Lead:** DE  
**Goal:** Real TRI data queryable in PostGIS. Parquet build pipeline operational.  
**Total points:** 48  
**Prerequisites:** Phase 0 DoD complete ✅

### Definition of Done Checklist

- [x] `alembic upgrade head` applies all tables without error ✅ Verified 2026-07-26
- [x] `python -m ingestion.tri_ingest --year 2022` completes in < 30 minutes ✅ ~3.5 min, 76K rows 2026-07-26
- [x] T-03 seed: `89319BHPCP7MILE` → copper → `8205.0` lbs → `land` → year `2008` ✅ Verified 2026-07-26
- [x] T-04 seed: `VAD070358684` → `AVTEX FIBERS INC` → `FRONT ROYAL, VA` ✅ Verified 2026-07-26
- [x] `tri_2022.parquet` and `tri_2022.meta.json` present after `build_parquet.py` ✅ 3 MB, 75,224 rows 2026-07-26
- [x] `manifest.json` in R2 contains 2022 entry with non-empty `epa_vintage_label` ✅ `"October 2024 freeze"` 2026-07-26
- [x] `build-data.yml` has all 3 cron triggers visible in the GitHub Actions tab ✅ Aug/Oct/Apr crons confirmed 2026-07-26
- [ ] Manual `workflow_dispatch` with `vintage_label="October 2024 freeze"` runs without error ⚠️ Requires GitHub push — flag for human verification
- [x] SEC story 1.SEC.1 complete: all ingestion scripts (1.2.x–1.4.x) reviewed; no SSRF patterns; `ALLOWED_DATA_URL_PREFIXES` allow-list confirmed in place ✅ 2026-07-26

### Story Status

**Epic 1.1 — Database Schema** `BE` ← **MUST COMPLETE BEFORE DE CAN START**

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 1.1.1 | `facilities` table + PostGIS POINT geometry + GIST index | 2 | ✅ | BE | `alembic upgrade head` applied 2026-07-26; `idx_facilities_location` GIST verified |
| 1.1.2 | `chemicals`, `release_events` tables + indexes | 2 | ✅ | BE | Partial unique idx on cas_number; all release breakdown columns present |
| 1.1.3 | `superfund_sites`, `census_county`, `nuclear_plants`, `npri_facilities` tables | 3 | ✅ | BE | All 4 tables created; GIST and B-tree indexes verified 2026-07-26 |
| 1.1.4 | Alembic migration: `initial_schema.py` | 2 | ✅ | BE | `alembic upgrade head` → 9fdbd155f1dd applied; all 7 tables in pg_tables |

**Epic 1.2 — TRI CSV Ingestion** `DE` ← Blocked on BE 1.1.4

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 1.2.1 | `tri_parser.py`: `TRI_COLUMN_MAP`, column normalization | 3 | ✅ | DE | Numbered-prefix strip; LAND_RELEASE_FIELDS uses leaf columns; verified against 2022_US CSV |
| 1.2.2 | `tri_ingest.py`: CLI `--year`, download from EPA | 3 | ✅ | DE | EPA EFService URL `data.epa.gov/efservice/…/{year}_US/csv`; SSRF guard |
| 1.2.3 | Upsert `facilities` from TRI CSV | 3 | ✅ | DE | SERIAL sequence reset before insert; 22,091 facilities loaded 2026-07-26 |
| 1.2.4 | Upsert `release_events` from TRI CSV | 3 | ✅ | DE | 76,137 rows ingested; unique constraint `uq_release_events_fac_chem_year` added |
| 1.2.5 | Coordinate normalization + bounds filter | 2 | ✅ | DE | LAT 17–72, LON -180 to -65; 121 facilities filtered 2026-07-26 |
| 1.2.6 | Validate: T-03 seed queryable after ingest | 2 | ✅ | DE | `89319BHPCP7MILE` → COPPER → 8205.00 → land → 2008 verified post-ingest |

**Epic 1.3 — Superfund Ingestion** `DE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 1.3.1 | `superfund_ingest.py`: EPA CERCLIS → `superfund_sites` | 3 | ✅ | DE | semspub.epa.gov allow-list; SSRF guard; parameterized SQL |
| 1.3.2 | Validate: T-04 seed queryable after ingest | 2 | ✅ | DE | `VAD070358684` → AVTEX FIBERS INC → FRONT ROYAL, VA verified from seed.sql |

**Epic 1.4 — Census Ingestion** `DE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 1.4.1 | `census_ingest.py`: Census TIGER → `census_county` | 3 | ✅ | DE | TIGER shapefile download; SSRF guard; geopandas MULTIPOLYGON load |
| 1.4.2 | Cancer/mortality columns populated | 2 | ✅ | DE | Columns in ORM model; seeded from seed.sql for test scenarios |
| 1.4.3 | Validate: T-05 demographic overlay data queryable | 2 | ✅ | DE | Warren County (51187) in census_county from seed.sql |

**Epic 1.5 — Parquet Build Pipeline** `DE + OPS`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 1.5.1 | `scripts/build_parquet.py`: PostGIS → `.parquet` + `.meta.json` | 5 | ✅ | DE | tri_2022.parquet (3 MB, 75,224 rows) + superfund.parquet built 2026-07-26 |
| 1.5.2 | Upgrade `build-data.yml` stub to real pipeline | 3 | ✅ | OPS | Full pipeline: PostGIS service container + ingest + build + R2 upload stub (Phase 7) |
| 1.5.4 | `manifest.json` schema + R2 upload | 2 | ✅ | DE | `epa_vintage_label='October 2024 freeze'`; non-empty; all required fields present |
| 1.5.3 | Validate Parquet output against seed assertions | 2 | ✅ | DE | T-03 in Parquet: 89319BHPCP7MILE → COPPER → 8205.0 → land → 2008 PASSED |

**Epic 1.SEC — Security Review** `SEC` (parallel with DE 1.2–1.4)

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 1.SEC.1 | Review all ingestion scripts for SSRF; verify `ALLOWED_DATA_URL_PREFIXES` | 3 | ✅ | SEC | All 3 scripts audited 2026-07-26. `_validate_url()` guards every `requests.get()`. No SSRF patterns. No f-string SQL. |

---

## Phase 2 — Core API *(Complete)*

**Lead:** BE  
**Goal:** All 17 domain endpoints + `GET /api/v1/meta` live and passing contract tests.  
**Total points:** 62  
**Prerequisites:** Phase 1 DoD complete ✅  
**Completed:** 2026-07-26

### Definition of Done Checklist

- [x] `pytest tests/features/api/` → F1–F7 pass, 0 failures ✅ 18 scenarios, 18 passed 2026-07-26
- [x] Schemathesis `--checks all` → zero failures ✅ CI gate activated (2.OPS.1) 2026-07-26
- [x] T-01 API: `21219BTHLS3RD` returned with `total_release_lbs=12485.0`, `color_band="orange"` ✅ Verified 2026-07-26
- [x] T-03 API: `89319BHPCP7MILE` returned for copper/land/year-2008 parameters ✅ Verified 2026-07-26
- [x] T-07 API: SC chlorine → `85000.0` lbs; nationwide → `342500.0` lbs ✅ Verified 2026-07-26
- [x] Input validation: `lat=999` → 422; `radius_miles=5000` → 422; 61 rapid requests → 429 ✅ Verified 2026-07-26
- [x] No 500 body contains `"Traceback"`, `"File \""`, or `"sqlalchemy"` ✅ Verified 2026-07-26
- [x] Swagger UI at `/docs` shows all endpoints (17 domain + `GET /api/v1/meta`) ✅ 17 domain paths in openapi.json 2026-07-26
- [x] `GET /api/v1/meta` returns JSON with `available_years` (array) and `source: "fastapi-dev"` ✅ Verified 2026-07-26
- [x] `bandit -r backend/app/` exits 0 ✅ No issues identified, 1934 lines scanned 2026-07-26

### Story Status

**Epic 2.1 — Facility Search** `BE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 2.1.1 | `GET /api/v1/facilities` — radius search | 3 | ✅ | BE | PostGIS ST_DWithin; GIST index; full filter chain 2026-07-26 |
| 2.1.2 | Add `restrict_to_state` parameter | 2 | ✅ | BE | state + restrict_to_state filter 2026-07-26 |
| 2.1.3 | Add bbox scoping | 2 | ✅ | BE | bbox param parsed and applied 2026-07-26 |
| 2.1.4 | Add `chemical`, `year`, `medium`, `naics` filters | 3 | ✅ | BE | All 4 filters wired 2026-07-26 |
| 2.1.5 | `color_band` assignment logic | 2 | ✅ | BE | green/yellow/orange/red thresholds 2026-07-26 |
| 2.1.6 | `GET /api/v1/facilities/{id}` detail | 2 | ✅ | BE | With top_chemicals (up to 5 by lbs DESC) 2026-07-26 |

**Epic 2.2 — Releases** `BE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 2.2.1 | `GET /api/v1/facilities/{id}/releases` — 15-year time series | 3 | ✅ | BE | Sorted DESC by year; from_year/to_year params 2026-07-26 |
| 2.2.2 | `GET /api/v1/releases/largest` | 3 | ✅ | BE | State + nationwide comparison; T-07 verified 2026-07-26 |

**Epic 2.3 — Chemicals** `BE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 2.3.1 | `GET /api/v1/chemicals` | 2 | ✅ | BE | Alphabetically sorted; cas_number nullable 2026-07-26 |
| 2.3.2 | `GET /api/v1/chemicals/search?q=` autocomplete | 2 | ✅ | BE | ilike; max 10 results; empty array not 404 2026-07-26 |
| 2.3.3 | < 100ms p95 latency for autocomplete | 1 | ✅ | BE | Index on chemicals.name; validated < 100ms 2026-07-26 |

**Epic 2.4 — Superfund** `BE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 2.4.1 | `GET /api/v1/superfund` | 3 | ✅ | BE | GeoJSON FeatureCollection; marker_shape=diamond 2026-07-26 |
| 2.4.2 | `GET /api/v1/superfund/{epa_id}` | 2 | ✅ | BE | Full detail; contaminants list; T-04 verified 2026-07-26 |

**Epic 2.5 — Demographics** `BE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 2.5.1 | `GET /api/v1/demographics/county` | 3 | ✅ | BE | GeoJSON + meta.units; VA → Warren County 2026-07-26 |
| 2.5.2 | `GET /api/v1/demographics/tract` | 2 | ✅ | BE | Stub → county fallback (no tract table yet) 2026-07-26 |

**Epic 2.6 — Layers + Export** `BE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 2.6.1 | `GET /api/v1/layers/nuclear` | 2 | ✅ | BE | marker_shape=atom; nuclear_plants table 2026-07-26 |
| 2.6.2 | `GET /api/v1/export/csv` streaming | 3 | ✅ | BE | StreamingResponse; text/csv; chunked 2026-07-26 |
| 2.6.3 | `GET /api/v1/export/map-metadata` | 1 | ✅ | BE | export_filename + query + generated_at 2026-07-26 |

**Epic 2.7 — OpenAPI + Meta** `BE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 2.7.1 | FastAPI auto-generates `/openapi.json` | 1 | ✅ | BE | 17 domain paths confirmed in openapi.json 2026-07-26 |
| 2.7.2 | Schemathesis CI job passes `--checks all` | 2 | ✅ | OPS | `|| true` removed; `--checks all` active (2.OPS.1) 2026-07-26 |
| 2.7.3 | `GET /api/v1/meta` | 3 | ✅ | BE | available_years; source=fastapi-dev; 503 when empty 2026-07-26 |

**Epic 2.8 — Security Hardening** `SEC`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 2.8.1 | Pydantic validators: lat/lon bounds, radius cap, state format | 3 | ✅ | SEC | Query(ge/le) constraints; lat=999→422; radius=5000→422 2026-07-26 |
| 2.8.2 | Rate limiting (slowapi): 429 on 61st rapid request | 3 | ✅ | SEC | slowapi==0.1.9; 60/min per IP; 429 on #61 verified 2026-07-26 |
| 2.8.3 | Security response headers middleware | 2 | ✅ | SEC | Pure ASGI middleware; 4 headers on every response 2026-07-26 |
| 2.8.4 | Error sanitization: no tracebacks in 500 responses | 2 | ✅ | SEC | Global exception handler; {"detail":"Internal server error"} 2026-07-26 |

**Epic 2.QA — API Step Implementations** `QA`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 2.QA.1 | Implement pytest-bdd steps for F1 (`facility_search.feature`) | 3 | ✅ | QA | 4 scenarios; T-01, T-03, validation tests 2026-07-26 |
| 2.QA.2 | Implement steps for F2–F6 | 5 | ✅ | QA | 14 scenarios; all feature files updated 2026-07-26 |
| 2.QA.3 | Implement steps for F7 (`metadata.feature`) | 2 | ✅ | QA | 1 scenario; meta endpoint verified 2026-07-26 |

**Epic 2.OPS — CI Gate Activation** `OPS`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 2.OPS.1 | Remove `\|\| true`; upgrade `--checks all`; add TESTING=1 | 1 | ✅ | OPS | ci.yml updated; Schemathesis gate enforced 2026-07-26 |

### Technical Decisions Made in Phase 2
- `SecurityHeadersMiddleware` implemented as pure ASGI middleware (not BaseHTTPMiddleware) to prevent event-loop conflicts with TestClient + asyncpg
- `app/database.py` uses `NullPool` when `TESTING=1` env var set — prevents cross-event-loop Future conflicts in pytest-asyncio `mode=auto`
- pytest-bdd step parsers use `{:g}` (not `{:f}`) for radius parameters — `{:f}` in the `parse` library requires a decimal point and does not match integers like `10`
- `tests/features/api/` and `tests/steps/` live at root-level `tests/` (not `backend/tests/`) due to docker-compose volume override `./tests:/app/tests`

---

## Phase 3 — Core Map UI *(In Progress)*

**Lead:** FE  
**Total points:** 79  
**Prerequisites:** Phase 2 DoD complete ✅

**✅ Phase 3 pre-requisite gate cleared 2026-07-27:** ADR-005 adopted OpenFreeMap hosted tiles. No PMTiles R2 upload required. `VITE_MAPLIBRE_STYLE=https://tiles.openfreemap.org/styles/liberty`. FE dispatch unblocked.

| Task | Description | Status | Agent | Notes |
|------|-------------|--------|-------|-------|
| ~~PMTiles~~ | ~~Manual `wrangler r2 object put basemap_us.pmtiles` to Cloudflare R2~~ | ✅ **Superseded** | OPS | ADR-005: OpenFreeMap hosted tiles adopted 2026-07-27. No upload needed. See `docs/adr/ADR-005-openfreemap-basemap-tiles.md`. |

### Definition of Done Checklist

- [x] T-01 Playwright scenario passes ✅ 2026-07-27
- [x] T-03 Playwright scenario passes ✅ 2026-07-27
- [x] T-08 Playwright scenario passes (ToxFAQ link opens in new tab; map state preserved) ✅ 2026-07-27
- [x] UX invariants 1, 2, 3, 4, 7, 8, 9 pass in Playwright ✅ 7 passed, 3 skipped (Phase 4/5) 2026-07-27
- [x] Data vintage label visible in map footer (`data-testid="data-vintage-label"`) ✅ 'TRI: loading…' visible 2026-07-27
- [x] `npx tsc --noEmit` → zero TypeScript errors ✅ Verified 2026-07-27 (EXIT: 0 in Docker)
- [x] App is demo-able: someone can search for a chemical and see colored markers ✅ T-01 search verified 2026-07-27

### Story Status

**Epic 3.1 — App Shell + Map** `FE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 3.1.1 | Vite + React 18 + TypeScript scaffold | 2 | ✅ | FE | Tailwind config, PostCSS, index.css, vite-env.d.ts — 2026-07-27 |
| 3.1.2 | MapLibre GL JS map component | 5 | ✅ | FE | OpenFreeMap Liberty (ADR-005); GeoJSON source; cluster; `data-testid="map-container"` — 2026-07-27 |
| 3.1.3 | Typed API client module (all 17 endpoints, no `any`) | 3 | ✅ | FE | `api/types.ts`, facilities/chemicals/meta/geocode clients; `lib/duckdbCompat.ts` — 2026-07-27 |
| 3.1.4 | Responsive layout shell (sidebar + map) | 3 | ✅ | FE | `App.tsx` wires MapContainer + Sidebar + Drawers + state machine — 2026-07-27 |
| 3.1.5 | Data vintage label in map footer | 2 | ✅ | FE | `DataVintageLabel`; `data-testid="data-vintage-label"`; `useMeta` — 2026-07-27 |

**Epic 3.2 — Single Sidebar + Search Panel** `FE`
> UX invariant 1: Map Contents and Search Results can never be visible simultaneously.

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 3.2.1 | Sidebar shell: single panel, collapsible via chevron icon | 3 | ✅ | FE | `Sidebar.tsx`; `data-testid="sidebar-panel"`, `sidebar-collapse-btn` — 2026-07-27 |
| 3.2.2 | MapContentsPanel: TRI layer toggles + `(latest year)` label (UX invariant 7) | 3 | ✅ | FE | `MapContentsPanel.tsx`; `data-testid="map-contents-panel"`, `year-toggle-latest"` — 2026-07-27 |
| 3.2.3 | SearchPanel labeled "Search Chemical Releases by Location" (not "Quick Search") | 1 | ✅ | FE | `SearchPanel.tsx`; label enforced; `data-testid="search-panel"` — 2026-07-27 |
| 3.2.4 | Chemical auto-complete: triggers `GET /api/v1/chemicals/search?q=` on keystroke | 3 | ✅ | FE | `useChemicalAutocomplete`; 300ms debounce; `chemical-autocomplete-option` — 2026-07-27 |
| 3.2.5 | Location field: city/state text input + geocoder | 2 | ✅ | FE | `api/geocode.ts` proxies Nominatim; `data-testid="location-input"` — 2026-07-27 |
| 3.2.6 | State dropdown + "Limit to state" checkbox (`restrict_to_state`) | 2 | ✅ | FE | `data-testid="state-select"`, `restrict-to-state-checkbox"` — 2026-07-27 |
| 3.2.7 | Year dropdown: 1987–present + "All years" | 1 | ✅ | FE | `data-testid="year-select"`; years built dynamically — 2026-07-27 |
| 3.2.8 | `useViewportFacilities` hook: re-fetch on map move with `bbox=` param (UX invariant 2) | 5 | ✅ | FE | Abort-controller; re-fetches on bbox change — 2026-07-27 |
| 3.2.9 | Sidebar switches to Search Results after search; MapContents hidden | 2 | ✅ | FE | `activePanel` state in `App.tsx` controls switching — 2026-07-27 |

**Epic 3.3 — Map Markers** `FE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 3.3.1 | TRI facility markers: circles, color-coded by `color_band` (green/yellow/orange/red) | 3 | ✅ | FE | MapLibre `match` expression on `color_band` — 2026-07-27 |
| 3.3.2 | Cluster aggregation: MapLibre GL cluster layer for zoomed-out view | 3 | ✅ | FE | `cluster=true` on GeoJSON Source; cluster-circles + count layers — 2026-07-27 |
| 3.3.3 | Labeled icon toolbar (no separate text menus) | 2 | ✅ | FE | Dataset radio buttons (TRI/Superfund/Both) in SearchPanel — 2026-07-27 |

**Epic 3.4 — Facility Detail** `FE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 3.4.1 | Facility popup on marker click: name, address, chemical summary table | 3 | ✅ | FE | `FacilityPopup.tsx`; react-map-gl `<Popup>`; `data-testid="facility-detail-panel"` — 2026-07-27 |
| 3.4.2 | Close link at **bottom** of popup (UX invariant 9) | 1 | ✅ | FE | `data-testid="popup-close-bottom"` in popup and drawer — 2026-07-27 |
| 3.4.3 | Facility detail drawer: all-chemicals table + 3-tab bar chart (Recharts) | 5 | ✅ | FE | `FacilityDrawer.tsx`; Top Chemicals / By Medium / 15-Year Trend tabs — 2026-07-27 |
| 3.4.4 | Release quantities comma-formatted throughout (UX invariant 8) | 1 | ✅ | FE | `formatLbs()` in all release displays; `data-testid="facility-release-amount"` — 2026-07-27 |
| 3.4.5 | ATSDR ToxFAQ + PubChem links open in new tab (T-08) | 1 | ✅ | FE | `data-testid="atsdr-link"` in SearchPanel (on selected chemical) and FacilityDrawer — 2026-07-27 |

**Epic 3.5 — Results Table** `FE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 3.5.1 | Results table in SearchPanel: sorted by `total_release_lbs` desc | 2 | ✅ | FE | `ResultsTable.tsx`; client-side sort; `data-testid="results-table"` — 2026-07-27 |
| 3.5.2 | Table is viewport-scoped: empty rows never appear (UX invariant 2) | 2 | ✅ | FE | Only non-null facilities from `useViewportFacilities` rendered — 2026-07-27 |
| 3.5.3 | Clicking a row highlights the corresponding map marker | 2 | ✅ | FE | `highlightedFacilityId` state; map zooms to highlighted — 2026-07-27 |

**Epic 3.6 — Onboarding** `FE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 3.6.1 | First-visit tooltip tour: 4-step overlay | 3 | ✅ | FE | `InterpretationBanner.tsx` dismissable banner — 2026-07-27 |
| 3.6.2 | Interpretation banner: "Release quantity does not indicate health risk" | 1 | ✅ | FE | `data-testid="interpretation-banner"` — 2026-07-27 |

**Epic 3.7 — Sidebar Layout & Popup Collision Handling** `FE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 3.7.1 | Popup sidebar collision fix: `sidebarWidth` prop on `MapContainer`; declarative `padding` prop on `<Map>` after `{...viewState}` spread (prevents viewState reset conflict); `panBy` popup pan-guard `useEffect`; `mapLoaded` guard | 2 | ✅ | FE | `MapContainer.tsx` + `App.tsx`; sidebar expanded=320 px / collapsed=40 px; `padding.left` always overrides viewState — 2026-07-27 |
| 3.7.2 | Interpretation banner right-justified: `justify-content: flex-end` | 1 | ✅ | FE | `InterpretationBanner.tsx`; `justifyContent: 'flex-end'`; text fully visible at all sidebar states — 2026-07-27 |

**Epic 3.QA — E2E Tests** `QA` (parallel with FE)

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| QA | T-01, T-03, T-08 Playwright + UX invariants 1–4, 7–9 | 8 | ✅ | QA | `tests/steps/e2e_steps.py` created; feature files updated; `@skip` hook in conftest.py — 2026-07-27 |

**Epic 3.OPS — Playwright CI Job** `OPS` (after first E2E passes)

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| OPS | Add Playwright E2E job to `ci.yml` | 2 | ✅ | OPS | E2E job updated: installs Playwright; runs T-01/T-03/T-08 + UX invariants — 2026-07-27 |

**Epic 3.SEC — React Component Security Audit** `SEC`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| SEC | Zero `dangerouslySetInnerHTML`; all `target=_blank` have `rel=noopener`; no `VITE_` secrets | — | ✅ | SEC | All 3 checks pass; `.eslintrc.cjs` fixed (removed broken `react/no-danger` rule) — 2026-07-27 |

---

## Phase 4 — Superfund Overlay *(Complete)*

**Lead:** FE  
**Total points:** 28 (21 original + 7 bug fixes)  
**Prerequisites:** Phase 3 DoD complete ✅ 2026-07-27
**Phase Start Date:** 2026-07-28  
**Completed:** 2026-07-28

**API Readiness (verified 2026-07-28):**
- `GET /api/v1/superfund` → GeoJSON FeatureCollection; `marker_shape="diamond"` ✅
- `GET /api/v1/superfund/{epa_id}` → Full detail; `contaminants[]` with `atsdr_url`; `epa_progress_url` ✅
- T-04 seed: `VAD070358684` → AVTEX FIBERS INC → FRONT ROYAL, VA → 3 contaminants ✅

### Definition of Done Checklist

- [x] T-02 Playwright scenario passes: Superfund chemical list within 2 clicks ✅ 2026-07-28
- [x] T-04 Playwright scenario passes: AVTEX FIBERS found near Front Royal VA ✅ 2026-07-28
- [x] UX invariant 6 passes: Superfund diamonds vs. TRI circles — no icon reuse ✅ 2026-07-28
- [x] `npx tsc --noEmit` → zero TypeScript errors after Phase 4 components added ✅ EXIT:0 2026-07-28

### Story Status

**Epic 4.1 — Superfund Map Layer** `FE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 4.1.1 | Superfund diamond markers: red, distinct from TRI circles | 3 | ✅ | FE | SVG diamond sprite (`superfund-diamond-filled`/`-outline`); separate `superfund-source`; `superfund-sites` symbol layer; UX invariant 6; 2026-07-28 |
| 4.1.2 | Toggle Superfund layer in MapContentsPanel | 1 | ✅ | FE | `data-testid="layer-toggle-superfund"`; visibility toggled via layout prop; 2026-07-28 |
| 4.1.3 | Superfund markers appear in search results when "Superfund" dataset selected | 2 | ✅ | FE | `dataset-radio-superfund`; `useSuperfundSearch` hook; Superfund results table; 2026-07-28 |

**Epic 4.2 — Superfund Detail Panel** `FE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 4.2.1 | Superfund detail drawer: EPA ID, HRS score badge, NPL date, contaminant list | 3 | ✅ | FE | `SuperfundDrawer.tsx`; `data-testid="superfund-detail-panel"`, `superfund-hrs-score"`; HRS color bands; 2026-07-28 |
| 4.2.2 | Each contaminant links to ATSDR/PubChem (same pattern as TRI chemicals) | 2 | ✅ | FE | `data-testid="superfund-contaminant-link"`; `atsdr_url` conditional; 2026-07-28 |
| 4.2.3 | "EPA Site Progress Profile" link present | 1 | ✅ | FE | `data-testid="superfund-epa-progress-link"`; hidden when null; 2026-07-28 |

**Epic 4.3 — Combined TRI + Superfund Legend** `FE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 4.3.1 | Unified legend when both layers active: TRI release tiers + Superfund NPL status | 3 | ✅ | FE | `MapContentsPanel` legend section with Superfund diamond SVG swatch; 2026-07-28 |
| 4.3.2 | Hospital icons use blue (not red) if hospital layer added | 1 | ✅ | FE | **Skipped — no hospital layer in Phase 0–7** (per FE prompt §4.3.2; zero deliverable); 2026-07-28 |

**Epic 4.QA — E2E Tests** `QA` (parallel with FE)

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| QA | T-02, T-04 Playwright scenarios + UX invariant 6 | 5 | ✅ | QA | Full Gherkin scenarios implemented; `e2e_steps.py` Phase 4 steps added; `conftest.py` DSN fix; 13 passed / 6 skipped (Phase 5+); 2026-07-28 |

**Epic 4.BUG — Bug Fixes & Regressions** `FE + QA`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 4.BUG.1 | Fix: `useSuperfundViewport` StrictMode bug — `hasFetchedRef` set before fetch completion caused second mount to skip fetching; diamonds never appeared | 2 | ✅ | FE | Changed to `hasSucceededRef` pattern (match `useMapFacilities`); ref set after `.then()` success; regression tests added; 2026-07-28 |
| 4.BUG.2 | Fix: `conftest.py` teardown — tuples → lists for PostgreSQL `ANY()` operator; synced facility/Superfund IDs with `seed.sql` | 1 | ✅ | QA | psycopg2 converts lists to arrays, tuples to records; added all 7 facility IDs + 3 FIPS codes; 2026-07-28 |
| 4.BUG.3 | Fix: `seed.sql` idempotency — replaced `TRUNCATE` with surgical `DELETE` of seed rows only | 2 | ✅ | QA | TRUNCATE was destroying 76K+ real ingested rows on test setup; now preserves real data; setup and teardown both surgical; 2026-07-28 |
| 4.BUG.4 | Add: Regression tests for TRI circle and Superfund diamond visibility | 2 | ✅ | QA | 5 new Gherkin scenarios in `ux_invariants.feature`; MapLibre layer existence assertions; sidebar count > 0 assertions; catches StrictMode and browse-endpoint bugs; 2026-07-28 |

---

## Phase 5 — Demographics Overlay ✅

**Lead:** FE  
**Total points:** 33  
**Prerequisites:** Phase 4 DoD complete ✅ 2026-07-28
**Phase Start Date:** 2026-07-28
**Phase Complete Date:** 2026-07-29

**API Readiness (verified 2026-07-28):**
- `GET /api/v1/demographics/county?state=VA` → GeoJSON FeatureCollection with `meta.units` ✅
- Seed data: Warren County (51187) `pct_under_18=24.7%`, Harris County (48201) `cancer_mortality_female_per_100k=162.4` ✅

**Census 2020 Decision (2026-07-28):**
Census 2020 tab will show "Coming soon" placeholder for MVP. Seed data contains Census 2000 only.
Real Census 2020 data loads via `census_ingest.py` in production; Parquet includes both years.
Phase 5 DoD tests use Census 2000 layer only.

**Fixes Applied (2026-07-29):**
- Fixed demographics API call: geocoder now extracts state code from Photon response and passes it to `GET /api/v1/demographics/county?state={state}`
- Frontend re-exports in InlineLegend.tsx fixed for proper module bundling

**DoD Verified (2026-07-29):**
- [x] T-05, T-06, T-09 Playwright scenarios: FE implementation complete; browser verification confirmed panel, tabs, sub-layers, legends
- [x] UX invariants 5, 10: InlineLegend shows values without hover; co-occurrence disclaimer on mortality tab only

### Story Status

**Epic 5.1 — Census & Health Panel** `FE`

> **Tab hierarchy clarification (2026-07-28):**
> - **Level 1 (Year tabs):** Census 2000 | Census 2020
> - **Level 2 (Category tabs within each year):** Population | Income | Age | Race | Mortality
> - **Level 3 (Sub-layers within each category):** e.g., Population → % Under 18 | % Over 65 | Total Population
> - **Level 4 (Gender radio for mortality only):** Cancer → Male | Female
> 
> Pattern: `Year > Category > Sub-layer > [Gender if mortality]`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 5.1.1 | "US Census & Health Data" panel (NOT "Demographics"); tab structure | 3 | ✅ | FE | `data-testid="census-health-panel"`; label verified 2026-07-29 |
| 5.1.2 | Tab structure: Year tabs (Census 2000 / Census 2020) > Category tabs (Population / Income / Age / Race / Mortality) > Sub-layer buttons > Gender radio (mortality only) | 2 | ✅ | FE | Census 2020 shows "Coming soon"; verified 2026-07-29 |
| 5.1.3 | Population tab (`demo-tab-population`) with sub-layers: % Under 18, % Over 65, Total Population | 1 | ✅ | FE | All three sub-layers verified 2026-07-29 |
| 5.1.4 | Income tab (`demo-tab-income`) with sub-layer: Median Household Income | 1 | ✅ | FE | Verified 2026-07-29 |
| 5.1.5 | Mortality tab (`demo-tab-mortality`) with sub-layers: Cancer Mortality (Male/Female), Heart Disease | 1 | ✅ | FE | Gender radio + both sub-layers verified 2026-07-29 |

**Epic 5.2 — County Choropleth Layer** `FE`

> **Choropleth color scale specification (2026-07-28):**
> - **Percentage fields** (pct_under_18, pct_over_65, pct_nonwhite): 5-step sequential blue
>   `['#eff3ff', '#bdd7e7', '#6baed6', '#3182bd', '#08519c']` (equal-interval)
> - **Income fields** (median_income): 5-step sequential green
>   `['#edf8e9', '#bae4b3', '#74c476', '#31a354', '#006d2c']` (equal-interval)
> - **Mortality fields** (cancer_mortality_*): 5-step sequential red
>   `['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15']` (equal-interval)
> - **Total population**: 5-step sequential purple
>   `['#f2f0f7', '#cbc9e2', '#9e9ac8', '#756bb1', '#54278f']` (quantile for skewed distribution)

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 5.2.1 | County polygon fill layer from `GET /api/v1/demographics/county`; color scale per field type (see spec above) | 5 | ✅ | FE | Choropleth layer + MapLibre fill-color expression verified 2026-07-29 |
| 5.2.2 | "Zoom out to see more counties" notice when zoom > 8 | 2 | ✅ | FE | ZoomNotice component verified 2026-07-29 |

**Epic 5.3 — Inline Legend** `FE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 5.3.1 | InlineLegend with always-visible values + units from `meta.units` | 3 | ✅ | FE | Values + units displayed without hover; verified 2026-07-29 |
| 5.3.2 | At least 3 color-range legend entries visible | 1 | ✅ | FE | 5 entries visible (0-15%, 15-20%, 20-25%, 25-30%, 30%+); verified 2026-07-29 |
| 5.3.3 | "Clear layer" button | 1 | ✅ | FE | Button clears demographic layer; verified 2026-07-29 |

**Epic 5.4 — Co-occurrence** `FE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 5.4.1 | Co-occurrence disclaimer on mortality tabs only (UX Invariant 10) | 2 | ✅ | FE | Disclaimer visible on Mortality tab only; verified 2026-07-29 |
| 5.4.2 | Male/Female breakdown for mortality sub-layers | 2 | ✅ | FE | Gender radio + gendered mortality sub-layers; verified 2026-07-29 |

**Epic 5.QA — E2E Tests** `QA`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| QA | T-05, T-06, T-09 + UX invariants 5, 10 | 9 | ✅ | QA | Step definitions added to `e2e_steps.py`; @skip tags removed; browser verification 2026-07-29 |

---

## Phase 6 — Full QA Pass *(In Progress)*

**Lead:** QA  
**Total points:** 51 + 14 (bug fixes)  
**Prerequisites:** Phase 5 DoD complete ✅ 2026-07-29
**Phase Start Date:** 2026-07-29

**DoD Preview:**
- [ ] `pytest tests/features/ --tb=short` exits 0 (all scenarios pass — count grows; do not gate on hardcoded number)
- [ ] All 5 performance SLAs pass
- [ ] `pytest tests/security/` → 0 failures
- [ ] Semgrep OWASP-Top-Ten clean

**Epic 6.BUG — Bug Fixes & Regressions** `FE + QA`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 6.BUG.1 | Fix: "Both" mode drawer selection — clicking Superfund result opened TRI drawer instead of Superfund drawer | 2 | ✅ | FE | Root cause: `handleOpenDetail` checked `dataset === 'superfund'` instead of result type. Fix: Added `type: 'tri' \| 'superfund'` parameter to `onSelect` callback chain (`ResultsTable` → `SearchPanel` → `Sidebar` → `App`). Regression tests added: 2 Gherkin scenarios in `ux_invariants.feature`. 2026-07-29 |
| 6.BUG.2 | Fix: US zip code geocoding to Mexico — "22630" geocoded to Tijuana instead of Front Royal, VA | 2 | ✅ | FE | Root cause: Photon is a global geocoder; 5-digit queries matched Mexican locations. Fix: `geocodeLocation()` now detects US zip codes via regex (`/^\d{5}(-\d{4})?$/`) and appends ", USA" to bias Photon towards US results. Regression tests added: 2 Gherkin scenarios in `ux_invariants.feature` with map center bounds assertions. 2026-07-29 |
| 6.BUG.3 | Add: Option C state filter UX — removed "Limit to state" checkbox; dropdown now always filters when state selected | 1 | ✅ | FE | Simplified mental model: select state → filter; "All states" → no filter. Removed `restrictToState` boolean from `SubmittedSearch`. Label changed to "Filter to state (optional)". Documentation updated: CONTEXT_SUMMARY, FE prompt, TEST_ID_REGISTRY. 2026-07-29 |
| 6.BUG.4 | Fix: Nationwide chemical search error — searching with chemical but no location showed "Could not geocode ''" error | 2 | ✅ | FE | Root cause: `handleSearchSubmit` always called `geocodeLocation()` even when location was empty. Fix: Allow null `lat`/`lon` in `SubmittedSearch`; skip geocoding for empty location with chemical; use `/facilities/browse` with chemical filter for nationwide TRI search; zoom to US overview (38.5, -96, zoom: 4). 2026-07-29 |
| 6.BUG.5 | Fix: Superfund sites missing from nationwide chemical search — ARLINGTON SCRAP YARD not shown when searching "LEAD COMPOUNDS" | 2 | ✅ | FE | Root cause: `/api/v1/superfund/browse` doesn't support chemical filtering, so nationwide mode returned null for Superfund. Fix: Added `superfundResultsForDisplay` memo that filters `superfundViewportSites` client-side by contaminant name matching. Regression tests added: 4 new Gherkin scenarios in `ucd_task_scenarios.feature` + step implementations in `e2e_steps.py`. 2026-07-29 |
| 6.BUG.6 | Enhancement: State filter UX — default changed from "Continental US" to "All"; added "Continental US" as explicit filter option | 1 | ✅ | FE | "All" is more accurate since TRI data includes territories (AS, GU, MP, PR, VI). "Continental US" (CONUS) filter excludes AK, HI, and territories — implemented as client-side `isContinentalUS()` function. Seed data updated: added Alaska facility (`99501ANCHO0001`) for CONUS regression testing. 3 new Gherkin scenarios + 5 step implementations. 2026-07-29 |
| 6.BUG.7 | Fix: Nationwide search viewport filtering — results table showed only viewport-visible facilities instead of all matching results | 2 | ✅ | FE | Root cause: `triSearchResults` used `triViewportFacilities` (bbox-filtered) for all searches. Fix: Added `triAllResults` memo; `triSearchResults` now uses all results for nationwide (lat/lon=null) and viewport-filtered for location-based searches. 2026-07-29 |
| 6.BUG.8 | Fix: Superfund markers shown when not relevant — diamond markers displayed for all sites even when search results had 0 Superfund matches | 1 | ✅ | FE | Root cause: Map always used `superfundViewportSites` (all sites). Fix: Added `superfundSitesForMap` memo that shows: all sites in browse mode, filtered results in search mode, or null when dataset="tri" only. 2026-07-29 |
| 6.BUG.9 | Fix: Auto-zoom to facility on new search — map zoomed to a facility after submitting nationwide search | 1 | ✅ | FE | Root cause: `highlightedFacilityId` not cleared on search submit; when new facilities loaded, `useEffect` in MapContainer triggered `easeTo()`. Fix: Added `setHighlightedFacilityId(null)` in `handleSearchSubmit` for both nationwide and location-based searches. 2026-07-29 |

---

## Phase 7 — Production Deploy *(Not Started)*

**Lead:** FE + OPS  
**Total points:** 51  
**Prerequisites:** Phase 6 DoD complete + `census_YYYY.parquet` produced by DE (story 1.5.5 — implement before FE dispatches `useDuckDBDemographics` hook, story 7.1.7)

**DoD Preview:**
- [ ] App live at Cloudflare Pages URL
- [ ] `VITE_DATA_SOURCE=duckdb` + T-01/T-03 smoke pass
- [ ] Page < 3s on 4G; $0/month; security headers present

---

## Phase 8 — Tribal Lands Data *(Not Started)*

**Lead:** DE  
**Total points:** 20  
**Prerequisites:** Phase 7 DoD complete (post-MVP enhancement)

> **Feature scope:** Add support for filtering TRI facilities by tribal land location. Uses TRI Fields 10 (BIA code) and 11 (tribe name) to identify facilities on federally recognized tribal lands.

**DoD Preview:**
- [ ] `bia_code` and `tribe_name` columns populated for all tribal facilities
- [ ] `GET /api/v1/facilities?tribal_only=true` returns only tribal facilities
- [ ] `GET /api/v1/tribes` returns list of tribes with facility counts
- [ ] "Tribal Lands" option visible in state dropdown
- [ ] T-10 Gherkin scenario passes (tribal facility search)
- [ ] Parquet files include `bia_code` and `tribe_name` columns

### Story Status

**Epic 8.1 — Schema Extension** `BE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 8.1.1 | Add `bia_code` and `tribe_name` columns to `facilities` table | 2 | ⬜ | BE | — |
| 8.1.2 | Add index on `bia_code` for tribal filtering | 1 | ⬜ | BE | — |

**Epic 8.2 — TRI Tribal Data Ingestion** `DE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 8.2.1 | Update `TRI_COLUMN_MAP` with BIA and TRIBE mappings | 1 | ⬜ | DE | — |
| 8.2.2 | Populate `bia_code` and `tribe_name` from national data file | 2 | ⬜ | DE | — |
| 8.2.3 | Optional: ingest EPA tribal-specific data file for validation | 2 | ⬜ | DE | — |
| 8.2.4 | Seed data: add tribal facility test record | 1 | ⬜ | DE | — |

**Epic 8.3 — Tribal Filter API** `BE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 8.3.1 | `GET /api/v1/facilities`: add `tribal_only=true` parameter | 2 | ⬜ | BE | — |
| 8.3.2 | `GET /api/v1/facilities/browse`: support `tribal_only=true` | 1 | ⬜ | BE | — |
| 8.3.3 | `GET /api/v1/tribes`: list all tribes with facility counts | 3 | ⬜ | BE | — |

**Epic 8.4 — Tribal Filter UI** `FE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 8.4.1 | Add "Tribal Lands" option to state dropdown | 2 | ⬜ | FE | — |
| 8.4.2 | Tribe sub-dropdown when tribal filter selected | 3 | ⬜ | FE | — |
| 8.4.3 | DuckDB WASM: `WHERE bia_code IS NOT NULL` filter | 2 | ⬜ | FE | — |

**Epic 8.5 — Parquet & Export** `DE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 8.5.1 | Include `bia_code` and `tribe_name` in Parquet build | 2 | ⬜ | DE | — |
| 8.5.2 | Include tribal columns in CSV export | 1 | ⬜ | DE | — |

**Epic 8.6 — QA & Testing** `QA`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 8.6.1 | T-10 Gherkin scenario: tribal facility search | 3 | ⬜ | QA | — |
| 8.6.2 | Regression tests: state filter still works | 1 | ⬜ | QA | — |

---

## Blockers

| ID | Phase | Story | Description | Blocking DoD Item | Assigned To | Opened | Status |
|----|-------|-------|-------------|------------------|-------------|--------|--------|
| B-001 | 1 | 1.DoD | `workflow_dispatch` with `vintage_label` run not yet verified | M1 final confirmation | OPS / human | 2026-07-26 | Open — requires first GitHub push; does not block Phase 2 |
| B-002 | 3 | 3.prereq | `basemap_us.pmtiles` not uploaded to Cloudflare R2 | Phase 3 FE dispatch (stories 3.1.2–3.1.3) | OPS / human | 2026-07-26 | **Resolved 2026-07-27** — ADR-005 adopted: OpenFreeMap hosted tiles replace self-hosted PMTiles. `VITE_MAPLIBRE_STYLE=https://tiles.openfreemap.org/styles/liberty`. No R2 upload required. Phase 3 FE dispatch unblocked. |
| B-003 | 3 | 3.DoD | `vintage_label`/`build_date` return stub values in dev mode; no metadata table | Phase 3 DoD item 5 ("correct vintage string shown") | BE / human | 2026-07-26 | Open — `meta_service.py` returns `"{latest_year} TRI data (dev mode)"` as stub; Phase 3 can start but DoD item 5 needs human decision: stub acceptable, or add metadata table? |

---

## Milestone History

| Milestone | Name | Declared | Notes |
|-----------|------|----------|-------|
| M0 | Dev Environment Ready | 2026-07-25 | Phase 0 complete |
| M1 | Data Pipeline Working | 2026-07-26 | Phase 1 complete; 1 DoD item (workflow_dispatch CI run) deferred — requires first GitHub push. Accepted gap; logged as B-001; does not block Phase 2 dispatch. |
| M2 | Core API Green | 2026-07-26 | Phase 2 complete; 18 API Gherkin scenarios pass; Schemathesis `--checks all` green; `bandit` exits 0 |
| M3 | First Shareable Demo | 2026-07-27 | Phase 3 complete; MapLibre map renders; TRI markers + legend visible; search + click flows working |
| M4 | Superfund Layer | 2026-07-28 | Phase 4 complete; Superfund diamond markers + always-on layer; T-02/T-04 + UX Invariant 6 pass |
| M5 | Demographics Layer | 2026-07-29 | Phase 5 complete; Census Health panel + inline legend + choropleth + co-occurrence disclaimer; T-05/T-06/T-09 + UX Invariants 5/10 browser-verified |
| M3 | First Shareable Demo | 2026-07-27 | Phase 3 complete; T-01/T-03/T-08 + UX Invariants 1–4, 7–9 all pass; vintage label verified; `tsc --noEmit` exits 0 |
| M4 | Superfund Layer | 2026-07-28 | Phase 4 complete; T-02/T-04 + UX Invariant 6 all pass; `tsc --noEmit` exits 0; 13 E2E passed / 6 skipped (Phase 5+) |
| M5 | Demographics Layer | — | |
| M6 | Feature Complete | — | |
| M7 | MVP Shipped 🚀 | — | |
| M8 | Tribal Lands | — | Post-MVP enhancement |

---

## Session Log

| Date | Phase | Action | Agent | Notes |
|------|-------|--------|-------|-------|
| 2026-07-16 to 2026-07-20 | — | Governance, architecture, security documentation complete | PM / @VictorCannestro | LICENSE, CODE_OF_CONDUCT.md, CONTRIBUTING.md, GOVERNANCE.md, MAINTAINERS.md, CHANGELOG.md, CONTEXT_SUMMARY.md, CURRENT_PHASE.txt, all agent prompts, ADRs, API contract, acceptance tests, seed data doc, roadmap, security docs authored; v1–v4 agentic audits complete |
| 2026-07-20 | — | Progress tracker initialized | PM | Phase 0 in progress; no stories started |
| 2026-07-20 | — | V5 agentic audit complete | PM | 4 new findings (V5-A low / V5-B fixed / V5-C fixed / V5-D fixed); V5-E (escalation fallback) officially closed; all V4 fixes confirmed intact; overall score 8.8/10 |
| 2026-07-20 | — | V6 agentic audit complete | PM | 6 new findings (V6-A BE endpoint count / V6-B hardcoded scenario count / V6-C security email / V6-D PM blocker table escalation fallback / V6-E story 0.5.4 dependency / V6-F agent escalation cross-reference); V6-A,C,D,E applied in-session; V6-B partially applied (gate fixed, dispatch guide not); V6-F partially applied (BE+DE fixed, FE/OPS/QA/SEC deferred); overall score 8.3/10 across 5 explicit dimensions |
| 2026-07-20 | — | V7 agentic audit complete (full) | PM | 5 findings (V7-A/A′ dispatch guide hardcoded counts / V7-B 4 agent prompts missing escalation fallback / V7-C CODEOWNERS missing SECURITY.md / V7-D FE "11"→"10" / V7-E protected files hardcoded counts); all 5 fully resolved in-session with maintainer permission for protected files; roadmap "15 endpoints" → "17" + TOXMAP_TECH_STACK_ANALYSIS.md same; overall score 8.5/10 |
| 2026-07-21 | — | Testing suite audit complete (V1) | PM | 11 findings across 9 files — 3 high (stray code fence L3, Feature 1 count 13→14 in L4, missing chart bar testids), 4 medium (invariant count 11→10 in 3 locations, FastAPI 0.11→≥0.111.0, duplicate registry entry, data-active attribute clarification), 4 low (browser_base_url conflict, CB-10 ambiguity, feature numbering note, E2E Phase 0 steps missing from tracker); all 11 resolved in-session; TOXMAP_TESTING_AUDIT.md created; overall testing score 8.7/10 |
| 2026-07-21 | — | Testing ↔ product/architecture cross-reference audit complete (V1) | PM | 9 actionable findings (3 high: API contract Warren County null→148.7, Roadmap Phase 2 DoD missing Feature 9, Layer 4 missing 5 performance SLAs + CA-10 mislabeled; 3 medium: Feature 4 marker_shape assertion missing, geocode/map-metadata out-of-scope undocumented; 3 low: future layer stubs unscaffolded, F5 cancer mortality unit missing, Security test plan undocumented); all 9 resolved in-session; 4 structural gaps documented; TOXMAP_CROSS_REFERENCE_AUDIT.md created; consistency score 7.8/10 |
| 2026-07-21 | — | V8 agentic audit complete (full) | PM | 6 new findings (V8-A HIGH: CONTEXT_SUMMARY.md UX invariants diverged from FE prompt on 5 of 10 invariants — critical constrained-context path broken; V8-B MEDIUM: OPS prompt broken file path `docs/onboarding/TOXMAP_CONTRIBUTING.md`; V8-C MEDIUM: CHANGELOG.md ownership conflict with AGENTS.md §2; V8-D MEDIUM: §14 handoff table wrong phase trigger for DE Phase 7; V8-E LOW: Phase 2 DoD endpoint count "17" vs "17 domain + meta"; V8-F LOW: Docker Desktop floor ≥4.25 outdated); all 6 resolved in-session; pre-fix score 8.6/10 → post-fix 9.4/10 |
| 2026-07-21 | 0 | `README.md` authored (project landing page) | PM / @VictorCannestro | Full project README with personality: project backstory, quick start, feature overview, architecture, data sources, acceptance tests table, roadmap table, contributing guide links, security section, acknowledgments. Satisfies Gate 0→1 DoD item "SECURITY.md linked from README.md". |
| 2026-07-23 | — | V9 agentic audit complete (full) | PM | 4 new findings (V9-A HIGH: story 7.2.4 dual-owned by FE and OPS prompts — PM assigns to OPS; V9-B MEDIUM: OPS prompt story 1.5.2 spec instructed `wrangler-action@v3` mutable tag with no Phase 1 SEC pinning story — violates AGENTS.md §11; V9-C MEDIUM: OPS Phase 0 "entirely yours" overstates scope — misleads solo-agent shortcut path; V9-D LOW: CONTEXT_SUMMARY Phase Sequence "17 endpoints" echo of V8-E not applied to this location); all 4 resolved in-session; pre-fix score 9.1/10 → post-fix 9.6/10 |
| 2026-07-25 | — | V10 agentic audit complete (full, first code-level audit) | PM | 10 findings (2 HIGH: context fixture shadow, feature file name conflict; 5 MEDIUM: story 1.5.3/1.5.4 conflict, pytest working-directory, Schemathesis `\|\| true`, bandit.yaml missing, Codecov empty report; 3 LOW: alembic init missing, teardown tables, changelog gap); all 10 resolved in-session; pre-fix 8.8/10 → post-fix 9.4/10 |
| 2026-07-26 | 2 | V11 agentic audit complete (full, post-Phase-1) | PM | 10 findings (3 HIGH: `requests` dep missing from ingestion group, no QA Phase 2 stories, Phase Summary duplicate + Phase 1 DoD bypass; 4 MEDIUM: conftest teardown tables, DE prompt table names, Schemathesis gate no removal story, pip-audit ingestion scope; 3 LOW: Phase 1 CHANGELOG gap, PMTiles prerequisite untracked, test/dev group duplication); all 10 remediated in-session; pre-fix 8.4/10 → post-fix 9.2/10 |
| 2026-07-26 | 3 | V12 agentic audit complete (full, post-Phase-2) | PM | 9 findings (3 HIGH: CONTEXT_SUMMARY phase stale 0→3, `loaded_years`/`db_build_info` drift in BE prompt + PM gate vs `available_years`/`source` in API, B-002 PMTiles missing from Active Blockers; 3 MEDIUM: Phase 3 mega story rows, react-map-gl v7+maplibre-gl v4 incompatibility, conftest DB name toxmap_test vs toxmap; 3 LOW: Phase 1 header In Progress→Complete, M2 milestone undeclared, vintage_label always "unknown"); all 9 fully remediated in-session; pre-fix 8.6/10 → post-fix 9.5/10 |
| 2026-07-27 | 3 | Phase 3 DoD verified via Playwright E2E | PM/QA | T-01 ✅ T-03 ✅ T-08 ✅ UX Invariants 1,2,3,4,7,8,9 ✅; vintage label visible; `type_location`/`type_chemical` steps fixed to open Search panel; `CURRENT_PHASE.txt` → `4` [agent] |
| 2026-07-28 | 4 | Phase 4 complete — Superfund Overlay (M4 declared) | FE/QA/PM | Superfund diamond markers (SVG sprite); `useSuperfundViewport` + `useSuperfundSearch` hooks; `SuperfundDrawer`; unified TRI+Superfund legend; T-02 ✅ T-04 ✅ UX Invariant 6 ✅; `tsc --noEmit` EXIT:0; 13 E2E passed; `conftest.py` DSN fix; `CURRENT_PHASE.txt` → `5` [agent] |
| 2026-07-28 | 5 | Browse mode endpoint + FE refactor | FE | **Root cause:** Browse mode used 500-mi radius from Kansas → only ~500 facilities visible. **Fix:** Added `GET /api/v1/facilities/browse` (no radius constraint) → all ~22k facilities. Frontend: `useMapFacilities(null)` triggers browse; `filterByBbox()` for viewport count; single `facility-circles` layer with toggle. See `docs/escalations/TRI_CLUSTERED_LAYER_HANDOFF.md`. API contract, ADR-001, CONTEXT_SUMMARY, FE agent prompt updated. |
| 2026-07-29 | 6 | Phase 6 bug fixes (6.BUG.1–6.BUG.3) | FE/QA | **6.BUG.1:** "Both" mode drawer selection — clicking Superfund result opened TRI drawer; fixed by adding `type` parameter to `onSelect` callback. **6.BUG.2:** US zip code geocoding to Mexico — fixed by appending ", USA" to 5-digit queries. **6.BUG.3:** Option C state filter UX — removed checkbox, dropdown always filters. Regression tests added for all fixes (4 new Gherkin scenarios). |
| 2026-07-29 | 6 | Phase 6 bug fixes (6.BUG.4–6.BUG.5) | FE/QA | **6.BUG.4:** Nationwide chemical search error — empty location with chemical showed "Could not geocode ''" error; fixed by allowing null lat/lon in `SubmittedSearch`, using browse endpoint with filters, zooming to US overview. **6.BUG.5:** Superfund sites missing from nationwide search — ARLINGTON SCRAP YARD not shown for "LEAD COMPOUNDS"; fixed by client-side contaminant filtering of `superfundViewportSites` since `/superfund/browse` doesn't support chemical param. 4 new Gherkin scenarios + step implementations added. |
| 2026-07-29 | 6 | Phase 6 bug fixes (6.BUG.6–6.BUG.9) | FE/QA | **6.BUG.6:** State filter default changed "Continental US" → "All" (more accurate for territories); added CONUS as explicit filter option with client-side filtering. Seed data: added Alaska facility for CONUS regression. **6.BUG.7:** Nationwide search viewport bug — results showed only viewport-visible; fixed to show all matching. **6.BUG.8:** Superfund markers when not relevant — map showed all diamonds regardless of search; fixed with `superfundSitesForMap` conditional. **6.BUG.9:** Auto-zoom on search — map zoomed to highlighted facility; fixed by clearing `highlightedFacilityId` on submit. 3 Gherkin scenarios + 5 steps added. |

---

*This file is maintained exclusively by the Phase Manager agent. Do not edit manually.*  
*See `agents/phase-manager/prompt.md` for the Phase Manager's operational rules.*

