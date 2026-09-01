# TOXMAP Clone — Development Roadmap

**Version:** 1.0  
**Date:** 2026-07-16  
**Status:** Ready for Handoff  
**Owner:** Product Management  
**Audience:** Development Team · QA/Testing Team · Engineering Lead

**Source Artifacts:**
- Stack: [ADR-001](../adr/ADR-001-fastapi-postgis-react.md) · [ADR-004](../adr/ADR-004-zero-budget-hosting.md)
- Requirements: [TOXMAP_TECH_STACK_ANALYSIS.md](../adr/TOXMAP_TECH_STACK_ANALYSIS.md)
- Tests: [TOXMAP_ACCEPTANCE_TESTS.md](../testing/TOXMAP_ACCEPTANCE_TESTS.md)
- Seed Data: [TOXMAP_TEST_SEED_DATA.md](../testing/TOXMAP_TEST_SEED_DATA.md)
- API Contract: [TOXMAP_API_CONTRACT.md](../api/TOXMAP_API_CONTRACT.md)
- UI Reference: [TOXMAP_SCREEN_CATALOG.md](TOXMAP_SCREEN_CATALOG.md)
- **Agent guardrails:** [AGENTS.md](../../AGENTS.md)
- **Governance:** [GOVERNANCE.md](../GOVERNANCE.md)

---

## 1. Product Vision

An open-source, zero-budget web application that recreates the EPA/NLM TOXMAP experience — letting citizens, researchers, and public health professionals explore EPA Toxic Release Inventory data and Superfund sites on an interactive map. Deployed statically via Cloudflare Pages + DuckDB WASM with no server costs.

**Success Criteria (MVP):**
1. All 9 UCD 2011 task scenarios (T-01 through T-09) pass in Playwright E2E tests
2. All 10 UX invariants pass
3. All Gherkin scenarios pass against seeded database (`pytest tests/features/ --tb=short` exits 0)
4. Deployed live at $0 cost on Cloudflare Pages

---

## 2. Team Roles

| Role | Responsibilities | Owns |
|------|-----------------|------|
| **Phase Manager (PM)** | Sprint orchestration, phase advancement, agent dispatch, progress tracking | `CURRENT_PHASE.txt`, `docs/product/TOXMAP_PROGRESS_TRACKER.md` |
| **Backend Dev (BE)** | FastAPI endpoints, PostGIS queries, SQLAlchemy models | `backend/app/` |
| **Data Engineer (DE)** | CSV ingestion scripts, Parquet build pipeline, seed.sql | `backend/ingestion/`, `scripts/` |
| **Frontend Dev (FE)** | React, MapLibre GL, Recharts, Tailwind CSS | `frontend/src/` |
| **QA Engineer (QA)** | pytest-bdd step implementations, Playwright E2E, Schemathesis | `tests/` |
| **DevOps / Infra (OPS)** | Docker Compose, GitHub Actions CI, Cloudflare deployment | `.github/`, `docker-compose.yml` |
| **Security Engineer (SEC)** | Security tooling, middleware, CI gates, production hardening | `SECURITY.md`, `.github/workflows/security.yml`, `docs/security/` |

> **Small team note:** On a 2-person team, BE+DE are typically one person; FE+QA are the other. OPS tasks are distributed. PM coordinates both; any agent may operate without PM in a single-agent session by reading `CURRENT_PHASE.txt` and the roadmap directly.

> **Agent entry point:** Development sessions should begin with the **Phase Manager** (`agents/phase-manager/prompt.md`). The PM reads `CURRENT_PHASE.txt`, briefs the correct agent, and gates phase advancement.

---

## 3. Architecture Constraints (Non-Negotiable)

These are locked before development starts. Any deviation requires a new ADR.

| Constraint | Value | Source |
|-----------|-------|--------|
| Backend (dev) | FastAPI + PostGIS | ADR-001 |
| Backend (prod) | DuckDB WASM (no server) | ADR-004 Option A |
| Frontend | React 18 + MapLibre GL JS | ADR-001 |
| Database (dev) | PostgreSQL 16 + PostGIS 3.4 | ADR-001 |
| Database (prod) | Parquet files on Cloudflare R2 | ADR-004 Option A |
| Tile source | Protomaps PMTiles (self-hosted) | ADR-001 |
| Hosting | Cloudflare Pages + R2 | ADR-004 |
| Production geocoding | Cloudflare Workers proxy (recommended) | ADR-009 |
| Budget | $0 | ADR-004 |
| Test framework | pytest-bdd + Playwright | TOXMAP_ACCEPTANCE_TESTS.md |

---

## 4. Milestone Summary

| # | Milestone | Deliverable | Phase Complete When |
|---|-----------|------------|---------------------|
| **M0** | Dev Environment Ready | Docker Compose up, seed loads, CI green | All devs can run tests locally |
| **M1** | Data Pipeline Working | TRI + Superfund + Census in PostGIS | `seed.sql` passes, ingestion runs on 2022 TRI |
| **M2** | Core API Green | Facility search + chemical auto-complete live | API contract tests pass for Phase 2 endpoints |
| **M3** | Map MVP | Map loads, search works, T-01 + T-03 pass E2E | First shareable demo |
| **M4** | Superfund Layer | Superfund overlay, T-02 + T-04 pass E2E | Phase 4 complete |
| **M5** | Demographics Layer | Census overlay, T-05 + T-06 + T-09 pass E2E | Phase 5 complete |
| **M6** | Full QA Green | All Gherkin scenarios + all 10 UX invariants pass (`pytest tests/features/ --tb=short` exits 0) | Feature complete |
| **M7** | Production Deploy | Live on Cloudflare Pages, $0, DuckDB WASM | **MVP Shipped** |
| **M8** | Tribal Lands Data | Tribal land facilities queryable + "Tribal" filter | Post-MVP enhancement |
| **M9** | Multi-Chemical Search | Search for multiple chemicals simultaneously (F-23) | Post-MVP enhancement |
| **M10** | EPA Monitoring Sites | EPA air quality monitoring site overlay (F-24) | Post-MVP enhancement |
| **M11** | Onboarding & UX Polish | In-app tutorial + consolidated toolbar (F-21, F-22) | Post-MVP enhancement |
| **M12** | Canadian NPRI | Canadian National Pollutant Release Inventory layer (F-25) | Post-MVP enhancement |
| **M13** | Nuclear Power Plants | US commercial nuclear facility overlay (F-26) | Post-MVP enhancement |
| **M14** | Congressional Districts | Congressional district boundary overlay (F-27) | Post-MVP enhancement |

---

## 5. Phase Breakdown

---

### Phase 0 — Foundation
**Goal:** Every developer can run the full stack locally and CI runs on every push.  
**Duration:** ~1 week  
**Team:** OPS (lead), all contribute

#### Epics & Stories

**Epic 0.1 — Repository Setup** `OPS`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 0.1.1 | Create GitHub repo with MIT license, README skeleton, `.gitignore` | 1 | Repo public, `main` branch protected |
| 0.1.2 | Define monorepo structure: `backend/`, `frontend/`, `scripts/`, `tests/`, `docs/` | 1 | Directory structure matches ADR-001 project layout |
| 0.1.3 | Add `CONTRIBUTING.md` and issue/PR templates | 1 | New contributors have a clear onboarding path |

**Epic 0.2 — Docker Compose Local Stack** `OPS + BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 0.2.1 | `docker-compose.yml`: services for `postgres`, `backend`, `frontend` | 3 | `docker compose up` starts all three services |
| 0.2.2 | PostgreSQL service: PostGIS 3.4 extension enabled on startup | 2 | `SELECT PostGIS_version();` returns a version string |
| 0.2.3 | Backend Dockerfile: Python 3.12 + FastAPI + uvicorn | 2 | `GET /health` returns `{"status": "ok"}` |
| 0.2.4 | Frontend Dockerfile: Node 22, Vite dev server | 2 | React app loads at `http://localhost:3000` |
| 0.2.5 | Volume mount: `backend/` code reloads on save (dev mode) | 1 | Edit a `.py` file → uvicorn reloads without restart |

**Epic 0.3 — CI/CD Pipeline** `OPS`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 0.3.1 | GitHub Actions: `ci.yml` — lint, unit tests on every PR | 3 | Green check on `main`, red on failing tests |
| 0.3.2 | GitHub Actions: `build-data.yml` stub — triggers manually | 1 | Workflow visible in Actions tab, runs to "no-op" success |
| 0.3.3 | Codecov or GitHub coverage report integrated | 2 | Coverage % visible on PR |

**Epic 0.4 — Test Infrastructure** `QA`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 0.4.1 | `tests/conftest.py`: `seed_db` fixture loads `seed.sql` from [TOXMAP_TEST_SEED_DATA.md](../testing/TOXMAP_TEST_SEED_DATA.md) | 3 | `pytest tests/` finds fixtures, DB is seeded and truncated per test |
| 0.4.2 | `tests/fixtures/seed.sql` file created verbatim from seed data doc | 2 | `psql -f seed.sql` runs without errors |
| 0.4.3 | pytest-playwright configured in `pyproject.toml` `[tool.pytest.ini_options]`: add `--base-url http://localhost:3000` and `--screenshot only-on-failure` to `addopts`; browser matrix set via CLI flags (`--browser chromium --browser firefox --browser webkit`) | 2 | `pytest tests/features/e2e/ --collect-only` discovers test files |
| 0.4.4 | pytest-bdd configured: `pyproject.toml` with `bdd_features_base_dir` | 1 | `pytest --collect-only` lists Gherkin scenarios |

**Epic 0.5 — Security Foundation** `SEC`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 0.5.1 | `SECURITY.md`: responsible disclosure policy, CVE response SLAs (Critical: 48 h; High: 7 d; Medium/Low: next release), reporting channel, in-scope components | 2 | File present at repo root; linked from `README.md` |
| 0.5.2 | `.github/dependabot.yml`: weekly automated dependency PRs for `pip`, `npm`, and `github-actions` with `labels: ["dependencies","security"]` | 1 | Dependabot PRs appear after first weekly run |
| 0.5.3 | `.github/workflows/security.yml`: gitleaks secrets scan + pip-audit + npm audit + bandit (Medium+) — runs on every PR and push to `main` | 3 | All 4 scan jobs green on `main`; any committed secret fails the `secrets-scan` job |
| 0.5.4 | Pin all third-party Actions in `ci.yml` and `build-data.yml` to full 40-char SHA; document resolved SHA → tag mapping in `docs/security/PINNED_ACTIONS.md` | 1 | Zero `@v\d` or `@latest` references remain in workflow files |

**Phase 0 Definition of Done:**
- [ ] `docker compose up` → all services healthy within 60 seconds
- [ ] `pytest tests/unit/` → green (no failures)
- [ ] CI pipeline runs and passes on an empty test suite
- [ ] All 4 developers can clone and run locally without manual steps
- [ ] `SECURITY.md` present and linked from `README.md`; all third-party GitHub Actions pinned to SHA; `security.yml` green on `main`

---

### Phase 1 — Data Pipeline
**Goal:** Real TRI data (or seeded data) is queryable in PostGIS. The foundation all API tests run against.  
**Duration:** ~1.5 weeks  
**Team:** DE (lead), BE supports schema

#### Epics & Stories

**Epic 1.1 — Database Schema** `BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 1.1.1 | Create `facilities` table with PostGIS POINT geometry + GIST index | 2 | `ST_DWithin` query runs in < 50ms on 10K rows |
| 1.1.2 | Create `chemicals`, `release_events` tables with indexes | 2 | Foreign key constraints enforced |
| 1.1.3 | Create `superfund_sites`, `census_county`, `nuclear_plants`, `npri_facilities` tables | 3 | All tables match ADR-001 data model exactly |
| 1.1.4 | Alembic migration: `initial_schema.py` | 2 | `alembic upgrade head` applies all tables cleanly |

**Epic 1.2 — TRI CSV Ingestion** `DE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 1.2.1 | `tri_ingest.py`: download 2022 EPA TRI CSV from EPA URL | 2 | File downloaded to `data/raw/tri_2022.csv` |
| 1.2.2 | `tri_parser.py`: parse CSV → pandas DataFrame, handle nulls/invalid coords | 3 | `df.shape[0]` > 500K rows, zero NaN lat/lon after clean |
| 1.2.3 | Upsert facilities into `facilities` table via geopandas + GeoAlchemy2 | 3 | Duplicate `tri_facility_id` updates, doesn't error |
| 1.2.4 | Upsert chemicals + release_events | 3 | `release_events` row count matches CSV rows |
| 1.2.5 | `--year` CLI flag: `python -m ingestion.tri_ingest --year 2022` | 1 | Single year ingest completes in < 30 minutes |
| 1.2.6 | Loop over years 2010–2022 in CI smoke test | 2 | Multi-year ingest produces correct row counts |

**Epic 1.3 — Superfund Ingestion** `DE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 1.3.1 | `superfund_ingest.py`: download EPA NPL CSV | 2 | NPL sites loaded into `superfund_sites` |
| 1.3.2 | Seed exact UCD records: `VAD070358684` (AVTEX FIBERS), `VAD980554587` | 1 | `SELECT * FROM superfund_sites WHERE epa_id = 'VAD070358684'` returns correct row |

**Epic 1.4 — Census Demographics Ingestion** `DE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 1.4.1 | `census_ingest.py`: load Census TIGER county boundaries for all 50 states | 5 | `census_county` has 3,143 rows with valid polygons |
| 1.4.2 | Attach demographic attributes (income, age, population, race) from Census API or CSV | 3 | Warren County VA (`51187`) has `pct_under_18 = 24.7` |
| 1.4.3 | Cancer mortality data for Harris County TX (`48201`) seeded | 1 | `cancer_mortality_female_per_100k = 162.4` |

**Epic 1.5 — Parquet Build Pipeline (ADR-004 Option A)** `DE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 1.5.1 | `scripts/build_parquet.py`: TRI → per-year `.parquet` files. Function signature must accept `vintage_label: str` (e.g. `"October 2024 freeze"`). Produces two outputs per year: `tri_YEAR.parquet` (data) **and** `tri_YEAR.meta.json` (sidecar with `tri_reporting_year`, `epa_vintage_label`, `build_date`, `record_count`). See `build_data.py` in ADR-004 for reference implementation. | 3 | `tri_2022.parquet` < 50 MB; `tri_2022.meta.json` present with valid `epa_vintage_label` field; omitting `vintage_label` raises `ValueError` |
| 1.5.2 | GitHub Actions `build-data.yml`: 3-checkpoint schedule (Aug 15 preliminary, Oct 20 freeze, Apr 1 spring refresh) + `workflow_dispatch` with `vintage_label` input (required). Runs `build_parquet.py` and uploads `.parquet` **and** `.meta.json` files to R2. See ADR-004 §GitHub Actions Workflow for the full cron + comments. **Do not use a single annual August trigger** — the October freeze dataset is the authoritative source; see ADR-004 Amendment note. | 3 | All 3 scheduled triggers visible in Actions tab; manual trigger with `vintage_label="October 2024 freeze"` → both `tri_2024.parquet` and `tri_2024.meta.json` visible in R2 bucket |
| 1.5.4 | `manifest.json` at R2 bucket root: machine-readable index of all available TRI years with their current vintage labels and build dates. Written by `build_parquet.py` after each run. Read by the React app at startup to populate the year-picker and display the current data vintage in the UI. Schema: `{ "years": [{ "year": 2022, "vintage_label": "October 2024 freeze", "build_date": "2024-10-20" }] }` | 2 | `manifest.json` present in R2; after a rebuild of year 2022, the manifest entry for 2022 reflects the new vintage label |
| 1.5.3 | ~~`scripts/build_pmtiles.py`: US basemap tile generation via Protomaps~~ **Superseded by ADR-005 (2026-07-27).** The MapLibre basemap is now served from OpenFreeMap hosted tiles (`https://tiles.openfreemap.org/styles/liberty`). No PMTiles file is generated or uploaded as part of the build pipeline. The self-hosting fallback procedure is documented in `docs/deployment/PMTILES_R2_UPLOAD.md` if custom tile hosting is needed in future. | ~~5~~ 0 | *(no acceptance criteria — story removed from scope)* |

**Phase 1 Definition of Done:**
- [ ] `psql -f tests/fixtures/seed.sql` runs without errors
- [ ] `python -m ingestion.tri_ingest --year 2022` loads real TRI data
- [ ] T-03 seed record (`89319BHPCP7MILE`, 8,205 lbs copper, land) queryable via raw SQL
- [ ] T-04 seed record (`VAD070358684`, AVTEX FIBERS) queryable via raw SQL
- [ ] `tri_2022.parquet` and `tri_2022.meta.json` both present after running `build_parquet.py`
- [ ] `manifest.json` in R2 contains an entry for year 2022 with a non-empty `epa_vintage_label`

---

### Phase 2 — Core API
**Goal:** All backend endpoints for facility search, chemical lookup, Superfund, and demographics are live and pass contract tests.  
**Duration:** ~2 weeks  
**Team:** BE (lead), DE supports data queries

**QA Parallel Track:** Implement all API-layer Gherkin step definitions (`tests/steps/api_steps.py`) as endpoints become available.

#### Epics & Stories

**Epic 2.1 — Facility Search Endpoint** `BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 2.1.1 | `GET /api/v1/facilities`: radius + bbox + chemical + year + medium filters | 8 | Returns GeoJSON FeatureCollection; Gherkin F1 scenarios 1–4 pass |
| 2.1.2 | `restrict_to_state=true` parameter filters to state boundary | 3 | All returned features have `state_code = requested_state` |
| 2.1.3 | `color_band` property computed server-side per release tier table | 2 | `12485.0` lbs → `"orange"` (10K–99K range) |
| 2.1.4 | Viewport bbox scoping: no features outside `bbox` parameter | 3 | All coordinates within `[-76.6, 39.1, -76.3, 39.4]` bbox |
| 2.1.5 | `GET /api/v1/facilities/{tri_facility_id}`: full facility record | 3 | Returns correct record for `21219BTHLS3RD` |
| 2.1.6 | 422 on missing lat/lon; 400 on radius > 500 | 1 | Error responses match `ErrorResponse` schema |

**Epic 2.2 — Release Time Series** `BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 2.2.1 | `GET /api/v1/facilities/{id}/releases`: 15-year time series | 3 | Array sorted descending; no null `total_release_lbs`; Gherkin F2 scenarios pass |
| 2.2.2 | `GET /api/v1/releases/largest?chemical&state`: state + nationwide comparison | 3 | SC chlorine → `85000.0` lbs; nationwide → `342500.0` lbs (T-07) |

**Epic 2.3 — Chemical Auto-Complete** `BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 2.3.1 | `GET /api/v1/chemicals`: full list, alphabetical, with `atsdr_url` + `pubchem_url` | 2 | 6 seed chemicals returned; Gherkin F3 scenarios 1–2 pass |
| 2.3.2 | `GET /api/v1/chemicals/search?q=`: max 10 results, ≤ 100ms | 2 | `?q=benz` returns BENZENE; response time < 100ms |
| 2.3.3 | 422 on `q` length < 2; empty array (not 404) on no match | 1 | Error + empty-match scenarios pass |

**Epic 2.4 — Superfund API** `BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 2.4.1 | `GET /api/v1/superfund`: radius search, GeoJSON, `marker_shape = "diamond"` | 5 | AVTEX FIBERS returned for Front Royal VA; Gherkin F4 scenarios pass |
| 2.4.2 | `GET /api/v1/superfund/{epa_id}`: full detail with `contaminants[]` and `epa_progress_url` | 3 | `VAD070358684` returns STYRENE in contaminants, correct HRS score |

**Epic 2.5 — Demographics API** `BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 2.5.1 | `GET /api/v1/demographics/county?state=VA`: GeoJSON polygons + `meta.units` | 5 | Warren County (`51187`) returned with `pct_under_18 = 24.7`; `meta.units.pct_under_18 = "%"` |
| 2.5.2 | `GET /api/v1/demographics/tract?county_fips=51187`: sub-county polygons | 3 | All features have FIPS starting with `51187` |

**Epic 2.6 — Optional Layers + Export** `BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 2.6.1 | `GET /api/v1/layers/nuclear`: nuclear plant GeoJSON | 2 | Returns FeatureCollection; `marker_shape = "atom"` |
| 2.6.2 | `GET /api/v1/export/csv`: streaming CSV with correct headers | 3 | Content-Type `text/csv`; headers match contract; chunked transfer |
| 2.6.3 | `GET /api/v1/export/map-metadata`: JSON with filename + query state | 1 | Returns `export_filename` with chemical/year/date encoded |

**Epic 2.7 — OpenAPI + Schemathesis** `BE + QA`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 2.7.1 | FastAPI auto-generates `/openapi.json` for all routes | 1 | Swagger UI at `/docs` shows all 17 endpoints |
| 2.7.2 | Schemathesis CI job: `--checks all` passes against seeded DB | 3 | No `response_schema_conformance` failures |

**Epic 2.8 — API Security Hardening** `BE + SEC`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 2.8.1 | Pydantic field validators: `lat` ∈ [−90, 90]; `lon` ∈ [−180, 180]; `radius_miles` ∈ (0, 500]; `state` matches `^[A-Z]{2}$`; `year` ∈ [1987, 2035]; `medium` ∈ {air, water, land, total} | 3 | `lat=999` → 422; `radius_miles=5000` → 422; `state=NOTASTATE` → 422 |
| 2.8.2 | Rate limiting middleware (`slowapi`): 60 req/min per IP on `/api/v1/` routes; `TESTING=true` disables limit; returns 429 with `Retry-After` header | 3 | 61 requests from same IP → 60 × 200 + 1 × 429; existing QA suite unbroken |
| 2.8.3 | Security response headers (`SecurityHeadersMiddleware`): `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: geolocation=()` | 2 | `curl -I` response includes all four headers on every endpoint |
| 2.8.4 | Error sanitization: override 500 handler; log full trace server-side; return only `{"detail":"Internal server error","status_code":500}` to client | 2 | Schemathesis 500 responses contain no `"Traceback"`, `"File \""`, or `"sqlalchemy"` substring |

**Phase 2 Definition of Done:**
- [ ] All API-layer Gherkin scenarios (Features 1–6 and Feature 9) pass: `pytest tests/features/api/`
- [ ] Schemathesis passes with `--checks all` and seed data loaded
- [ ] T-01 API portion: `GET /api/v1/facilities?lat=39.2197&lon=-76.4785&radius_miles=10&chemical=LEAD+COMPOUNDS&year=2008` returns `21219BTHLS3RD` with `total_release_lbs=12485.0`
- [ ] T-03 API portion: `GET /api/v1/facilities?lat=39.2919&lon=-115.0319&radius_miles=30&chemical=COPPER&year=2008&medium=land` returns `89319BHPCP7MILE`
- [ ] T-07 API: both SC and nationwide chlorine queries return correct facilities
- [ ] `lat=999` returns 422; `radius_miles=5000` returns 422; 61 rapid requests returns 429; no 500 leaks a stack trace

---

### Phase 3 — Core Map UI
**Goal:** A user can open the app, search for a chemical near a location, and see results on the map. T-01, T-03, T-08 pass E2E.  
**Duration:** ~2 weeks  
**Team:** FE (lead), QA implements E2E step stubs in parallel

#### Epics & Stories

**Epic 3.1 — App Shell + Map** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 3.1.1 | React app scaffold with Vite, TypeScript, Tailwind CSS | 2 | `npm run dev` → app at `:3000` |
| 3.1.2 | MapLibre GL map component: US overview, OpenFreeMap basemap. Configure MapLibre with `style: "https://tiles.openfreemap.org/styles/liberty"` (set via `VITE_MAPLIBRE_STYLE` env var). **Do not use a self-hosted PMTiles file** — ADR-005 adopted OpenFreeMap hosted tiles; no R2 upload required for the basemap. | 5 | Map renders street names, state/county boundaries; `VITE_MAPLIBRE_STYLE` controls the tile source |
| 3.1.3 | Typed API client module: `api/facilities.ts`, `api/chemicals.ts` | 2 | All 17 endpoints typed; no `any` |
| 3.1.4 | Landing page (`/`): description + "Launch Map" CTA + FAQ/Glossary links | 2 | Matches Fig 2015-6 in screen catalog |
| 3.1.5 | Data vintage indicator: on app init, fetch `manifest.json` from R2 (prod) or `/api/v1/meta` (dev); display current vintage as an unobtrusive label (e.g. `"2022 TRI · October 2024 freeze"`) in the map footer. In dev mode (`VITE_DATA_SOURCE=api`), FastAPI serves a `/api/v1/meta` endpoint returning the loaded year and DB build info. See ADR-004 Amendment for why vintage transparency is required. | 2 | Vintage label visible in map footer without hover; `data-testid="data-vintage-label"` present; correct vintage string shown for the active TRI year |

**Epic 3.2 — Single Sidebar + Search Panel** `FE`
> **Critical UX invariant:** Map Contents and Search Results can never be visible simultaneously (F-08, UCD 2011).

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 3.2.1 | Sidebar shell: single panel, collapsible via chevron icon | 3 | `data-testid="sidebar-panel"` present; collapses on click |
| 3.2.2 | MapContentsPanel: TRI layer toggles, year checkboxes with `(latest year)` label | 3 | Most-recent year shows `(latest year)` text (UX invariant 7) |
| 3.2.3 | SearchPanel: labeled **"Search Chemical Releases by Location"** (not "Quick Search") | 1 | No element with text "Quick Search" (UX invariant 4) |
| 3.2.4 | Chemical auto-complete input: triggers `GET /api/v1/chemicals/search?q=` on keystroke | 3 | Dropdown appears within 100ms; `data-testid="chemical-autocomplete-option"` |
| 3.2.5 | Location field: city/state text input with Photon browser-direct geocoding (ADR-006). Cache results (max 200, LRU); throttle to ≤ 1 req/s; render `PHOTON_ATTRIBUTION` as JSX links in map footer | 2 | Typing "Sparrows Point, MD" → resolves to lat=39.219, lon=-76.476; Photon/OSM credit visible in footer; repeated searches hit cache (zero network calls) |
| 3.2.6 | State dropdown + "Limit to state" checkbox | 2 | Checkbox triggers `restrict_to_state=true` in query (UX invariant 3) |
| 3.2.7 | Year dropdown: 1987–present + "All years" | 1 | Selected year passed as `year=` parameter |
| 3.2.8 | `useViewportFacilities` hook: re-fetches on map move with `bbox=` param | 5 | Moving map updates results; zero empty rows (UX invariant 2) |
| 3.2.9 | Sidebar switches to Search Results when search runs; MapContents hidden | 2 | `data-testid="map-contents-panel"` not visible after search |

**Epic 3.3 — Map Markers** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 3.3.1 | TRI facility markers: circles, color-coded by `color_band` (green/yellow/orange/red) | 3 | 10K+ markers render without lag; color matches release tier |
| 3.3.2 | Cluster aggregation: MapLibre GL cluster layer for zoomed-out view | 3 | Dots cluster at zoom < 9; expand on zoom in |
| 3.3.3 | Labeled icon toolbar (no separate text menus) | 2 | No duplicate menu/icon controls (UX invariant, UCD 2011) |

**Epic 3.4 — Facility Detail** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 3.4.1 | Facility popup on marker click: name, address, chemical summary table | 3 | Matches layout in screen catalog Fig 6 |
| 3.4.2 | Close link at **bottom** of popup (not only corner X) | 1 | `data-testid="popup-close-bottom"` visible; dismisses popup (UX invariant 9) |
| 3.4.3 | Facility detail drawer: all-chemicals table + 3-tab bar chart (Recharts) | 5 | Tab 1: top 5 chemicals; Tab 2: stacked medium bars; Tab 3: 15-year trend |
| 3.4.4 | Release quantities comma-formatted throughout | 1 | `8205.0` displays as `8,205 lbs` (UX invariant 8) |
| 3.4.5 | ATSDR ToxFAQ + PubChem links open in new tab | 1 | Map state preserved after link click (T-08) |

**Epic 3.5 — Results Table** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 3.5.1 | Results table in SearchPanel: sorted by `total_release_lbs` desc | 2 | Rows match markers on map |
| 3.5.2 | Table is viewport-scoped: empty rows never appear | 2 | Every visible row has facility name + release amount |
| 3.5.3 | Clicking a row highlights the corresponding map marker | 2 | Marker pulses or zooms on row click |

**Epic 3.6 — Onboarding** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 3.6.1 | First-visit tooltip tour (Shepherd.js or React Joyride): 4-step overlay | 3 | Tour runs once; `localStorage["onboarding-seen"]` prevents repeat |
| 3.6.2 | Interpretation banner (persistent, dismissible): "Release quantity does not indicate health risk" | 1 | Banner visible below map on first load |

**Epic 3.7 — Sidebar Layout & Popup Collision Handling** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 3.7.1 | Popup visible when sidebar is open: pass `sidebarWidth` (collapsed=40 px, expanded=320 px) to `MapContainer`; set MapLibre camera padding via declarative `padding` prop on `<Map>` after `{...viewState}` spread so it always wins; add `panBy` guard `useEffect` that pans map right when selected marker falls within `sidebarWidth + gutter + popupHalfWidth` zone | 2 | With sidebar open, no popup hidden beneath sidebar; `easeTo`/`flyTo` centers facility in usable viewport; sidebar toggle re-applies padding without camera jump |
| 3.7.2 | Interpretation banner text right-justified: change `justify-content` from `space-between` to `flex-end` so text and dismiss button are anchored to the visible map area regardless of sidebar state | 1 | Banner text fully visible at all sidebar states (open, collapsed); no text obscured by sidebar |

**E2E Tests — Phase 3 Target:**

| Scenario | Implemented By | Passing After |
|---------|---------------|---------------|
| T-01: Lead near Sparrows Point | QA | Phase 3 |
| T-03: Copper near Ruth NV | QA | Phase 3 |
| T-08: ToxFAQ link opens in new tab | QA | Phase 3 |
| UX Invariant 1: Single sidebar | QA | Phase 3 |
| UX Invariant 2: No empty rows | QA | Phase 3 |
| UX Invariant 3: State restriction | QA | Phase 3 |
| UX Invariant 4: Panel labels | QA | Phase 3 |
| UX Invariant 7: Latest year label | QA | Phase 3 |
| UX Invariant 8: Comma formatting | QA | Phase 3 |
| UX Invariant 9: Close link at bottom | QA | Phase 3 |

**Phase 3 Definition of Done:**
- [ ] T-01 Playwright scenario passes
- [ ] T-03 Playwright scenario passes
- [ ] T-08 Playwright scenario passes
- [ ] UX invariants 1, 2, 3, 4, 7, 8, 9 pass in Playwright
- [ ] Data vintage label visible in map footer (`data-testid="data-vintage-label"`)
- [ ] `npx tsc --noEmit` → zero TypeScript errors
- [ ] App is demoable: someone can search for a chemical and see colored markers

**Technical Decisions Made in Phase 3:**
- **Geocoding — Photon browser-direct (ADR-006):** Nominatim was blocked by server IP and
  Docker SSL inspection; replaced with Photon (photon.komoot.io) called directly from the browser.
  CORS-enabled, no API key, OSM-backed. Fair-use mitigations: 200-entry LRU cache, 1s throttle,
  attribution rendered in map footer. FastAPI `GET /api/v1/geocode` is retained but unused by frontend.
- **Viewport bbox race condition:** Two concurrent facility-search requests fired on each new search
  (pre-zoom and post-zoom viewport). Fix: `setMapBbox(null)` before `setSubmittedSearch` in
  `handleSearchSubmit`; `AbortSignal` threaded through `fetchFacilities` to cancel stale requests.
- **Tailwind volume mount:** `tailwind.config.js` and `postcss.config.js` are baked into the Docker
  image (not volume-mounted). `src/index.css` contains vanilla CSS fallbacks so the app renders
  correctly even when Tailwind PostCSS is not configured (e.g. running against an old image).

**Milestone M3 — First shareable demo**

---

### Phase 4 — Superfund Overlay
**Goal:** Superfund/NPL sites visible as red diamonds on the map. T-02 and T-04 pass E2E.  
**Duration:** ~1.5 weeks  
**Team:** FE (lead), BE confirms API from Phase 2

#### Epics & Stories

**Epic 4.1 — Superfund Map Layer** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 4.1.1 | Superfund diamond markers: red, distinct from TRI circles | 3 | Matches screen catalog Fig 9; no icon ambiguity (UX invariant 6) |
| 4.1.2 | Toggle Superfund layer in MapContentsPanel | 1 | Checkbox shows/hides diamonds |
| 4.1.3 | Superfund markers appear in search results when "Superfund" dataset selected | 2 | SearchPanel has dataset radio: TRI / Superfund / Both |

**Epic 4.2 — Superfund Detail Panel** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 4.2.1 | Superfund detail drawer: EPA ID, HRS score badge, NPL date, contaminant list | 3 | Matches screen catalog Fig 10 layout |
| 4.2.2 | Each contaminant links to ATSDR/PubChem (same pattern as TRI chemicals) | 2 | Links open in new tab |
| 4.2.3 | "EPA Site Progress Profile" link present | 1 | URL pattern: `cumulis.epa.gov/supercpad/SiteProfiles/...` |

**Epic 4.3 — Combined TRI + Superfund Legend** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 4.3.1 | Unified legend when both layers active: TRI release tiers + Superfund NPL status | 3 | No icon reuse; UX invariant 6 passes |
| 4.3.2 | Hospital icons use blue (not red) if hospital layer added | 1 | Red reserved for hazard markers only |

**E2E Tests — Phase 4 Target:**

| Scenario | Passing After |
|---------|---------------|
| T-02: Superfund chemical list within 2 clicks | Phase 4 |
| T-04: AVTEX FIBERS found near Front Royal VA | Phase 4 |
| UX Invariant 6: Distinct TRI vs Superfund icons | Phase 4 |

**Phase 4 Definition of Done:**
- [ ] T-02 and T-04 Playwright scenarios pass
- [ ] UX invariant 6 passes
- [ ] Milestone M4

**Technical Decisions Made in Phase 4:**
- **Superfund browse endpoint (2026-07-28):** The original `/api/v1/superfund` endpoint required `lat`, `lon`,
  and `radius_miles` (capped at 500). This made the always-on diamond layer impossible without viewport-driven
  refetching, which caused different subsets to appear at different zoom levels. Added `/api/v1/superfund/browse`
  endpoint that returns all ~1,700 sites without radius constraint. Frontend `useSuperfundViewport` hook now
  fetches once on mount; MapLibre handles viewport clipping. Mirrors the TRI `/api/v1/facilities/browse` pattern.
- **Layer structure:** Single `superfund-sites` symbol layer with two icon sprites: `superfund-diamond-filled`
  (NPL sites) and `superfund-diamond-outline` (CERCLIS/Deleted). Icon selection via MapLibre expression on
  `status` property. Toggle via `setLayoutProperty('superfund-sites', 'visibility', ...)`.
- **React StrictMode compatibility (2026-07-28):** Data-fetching hooks must set their "has fetched" ref AFTER
  the fetch succeeds, not before. React 18 StrictMode double-invokes effects; if the ref is set before the
  fetch completes, the first fetch is aborted and the second mount skips fetching entirely. Pattern:
  `hasSucceededRef.current = true` inside `.then()`, not before the fetch call.

**Epic 4.BUG — Bug Fixes & Regressions** `FE + QA`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 4.BUG.1 | Fix: `useSuperfundViewport` StrictMode bug — `hasFetchedRef` set before fetch completion | 2 | Superfund diamonds appear on initial page load; regression test passes |
| 4.BUG.2 | Fix: `conftest.py` teardown — tuples → lists for `ANY()`; sync facility IDs with `seed.sql` | 1 | `pytest -k Regression` passes without `WrongObjectType` error |
| 4.BUG.3 | Fix: `seed.sql` idempotency — replace `TRUNCATE` with surgical `DELETE` | 2 | Real ingested data preserved after test runs; script is idempotent |
| 4.BUG.4 | Add: Regression tests for TRI circle and Superfund diamond visibility | 2 | 5 new Gherkin scenarios pass; MapLibre layer assertions verify data loaded |

**Milestone M4 — Superfund Layer**

---

### Phase 5 — Demographics Overlay
**Goal:** Census health data overlays work. T-05, T-06, T-09 pass E2E.  
**Duration:** ~2 weeks  
**Team:** FE (lead), BE confirms demographics API

> **Census 2020 Decision (2026-07-28):** Census 2020 tab shows "Coming soon" for MVP. Seed data
> contains Census 2000 only. Real Census 2020 data loads via `census_ingest.py`; Parquet includes
> both years. Phase 5 DoD tests use Census 2000 layer.

#### Epics & Stories

**Epic 5.1 — Census Health Data Panel** `FE`

> **Tab hierarchy specification:**
> - **Level 1 (Year tabs):** Census 2000 | Census 2020
> - **Level 2 (Category tabs within each year):** Population | Income | Age | Race | Mortality
> - **Level 3 (Sub-layers within each category):** e.g., Population → % Under 18 | % Over 65 | Total Pop
> - **Level 4 (Gender radio for mortality only):** Cancer → Male | Female
> 
> Navigation pattern: `Year > Category > Sub-layer > [Gender]`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 5.1.1 | Panel labeled **"US Census & Health Data"** (not "Demographics") | 1 | No "Demographics" label visible (UX invariant 4); `data-testid="census-health-panel"` |
| 5.1.2 | Tab structure: Year tabs (Census 2000 / Census 2020) > Category tabs > Sub-layer buttons > Gender radio | 3 | Matches screen catalog Fig 2015-5 layout; Census 2020 tab shows "Coming soon" placeholder |
| 5.1.3 | Cancer/Heart Disease tabs under Mortality; Cancer has Male/Female radio | 2 | No combined Cancer option; tooltip explains "data reported by gender separately" |
| 5.1.4 | One layer at a time enforced: selecting new layer clears previous | 2 | Map shows only one choropleth shading at a time; previous legend disappears |
| 5.1.5 | Zoom notice: "Zoom out to see more counties" when zoom > 8 | 1 | Appears below legend; hidden when zoom ≤ 8 (UCD 2011 finding) |

**Epic 5.2 — Choropleth Map Layer** `FE`

> **Choropleth color scale specification:**
> - **Percentage fields** (pct_under_18, pct_over_65, pct_nonwhite): 5-step sequential blue
>   `['#eff3ff', '#bdd7e7', '#6baed6', '#3182bd', '#08519c']` (equal-interval)
> - **Income fields** (median_income): 5-step sequential green
>   `['#edf8e9', '#bae4b3', '#74c476', '#31a354', '#006d2c']` (equal-interval)
> - **Mortality fields** (cancer_mortality_*): 5-step sequential red
>   `['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15']` (equal-interval)
> - **Total population**: 5-step sequential purple
>   `['#f2f0f7', '#cbc9e2', '#9e9ac8', '#756bb1', '#54278f']` (quantile for skewed distribution)

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 5.2.1 | County polygon fill layer: color-coded by selected demographic variable | 5 | Warren County VA colored by `pct_under_18 = 24.7%`; MapLibre `fill-color` interpolate expression using color scales above |
| 5.2.2 | TRI/Superfund markers remain visible over demographic shading | 2 | Point layers rendered above fill layer (`z-index` via layer order); no visual obstruction |

**Epic 5.3 — Inline Legend** `FE`
> **Critical UX invariant:** Legend values must be visible without hovering (UCD 2011 §"Mouse-Over Legend").

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 5.3.1 | InlineLegend component: color blocks with range values always visible | 3 | At least 3 color-range entries visible without hover; `data-testid="demographic-legend"`, `demographic-legend-entry"` |
| 5.3.2 | Units shown for every field: `%`, `$`, `people`, `per 100,000` | 2 | Units sourced from `meta.units` in API response — no hardcoding |
| 5.3.3 | "Clear layer" button in demographic panel removes choropleth | 1 | Shading removed; legend disappears (T-06); `data-testid="clear-layer-btn"` |

**Epic 5.4 — Co-Occurrence Disclaimer** `FE`
> Source: UCD 2011 §"Explanation of Mortality Categories" + NLM misinterpretation concern.

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 5.4.1 | Disclaimer on mortality tabs only: "Correlation does not imply causation" | 2 | Visible on Cancer/Heart Disease tab; NOT on Population/Income tabs (UX invariant 10); `data-testid="cooccurrence-disclaimer"` |
| 5.4.2 | Explanation link for why Male/Female cannot be combined | 1 | Tooltip or info icon explains "Cancer mortality data is reported separately by gender" |

**E2E Tests — Phase 5 Target:**

| Scenario | Passing After |
|---------|---------------|
| T-05: TRI styrene + under-18 overlay, no panel confusion | Phase 5 |
| T-06: Income layer, units, removable | Phase 5 |
| T-09: Benzene + cancer mortality, co-occurrence disclaimer | Phase 5 |
| UX Invariant 5: Inline legend values without hover | Phase 5 |
| UX Invariant 10: Disclaimer on mortality tab only | Phase 5 |

**Phase 5 Definition of Done:**
- [ ] T-05, T-06, T-09 Playwright scenarios pass
- [ ] UX invariants 5 and 10 pass
- [ ] Milestone M5

---

### Phase 6 — Full QA Pass
**Goal:** All Gherkin scenarios pass (count grows across phases — gate on `pytest tests/features/ --tb=short` exiting 0, not a hardcoded number). All 10 UX invariants pass. Performance SLAs met.  
**Duration:** ~1.5 weeks  
**Team:** QA (lead), BE + FE on bug fixes

#### Epics & Stories

**Epic 6.1 — Complete Gherkin Step Implementations** `QA`

| Story | Description | Points |
|-------|-------------|--------|
| 6.1.1 | Implement all remaining API step stubs in `api_steps.py` | 5 |
| 6.1.2 | Implement all E2E step stubs in `tests/steps/` modules | 8 |
| 6.1.3 | All Gherkin scenarios green (count grows across phases): `pytest tests/features/ --tb=short` exits 0 | 8 |

**Epic 6.2 — Performance Benchmarks** `BE + QA`

| Story | SLA Target | Tool |
|-------|-----------|------|
| Radius search p95 | < 500ms | `pytest-benchmark` |
| Viewport bbox re-fetch p95 | < 200ms | `pytest-benchmark` |
| Chemical auto-complete | < 100ms | Gherkin assertion |
| Superfund search p95 | < 300ms | `pytest-benchmark` |
| CSV first byte | < 1,000ms | `pytest-benchmark` |

**Epic 6.3 — Bug Bash** `All`

| Story | Description | Points |
|-------|-------------|--------|
| 6.3.1 | Fix all Schemathesis failures | varies |
| 6.3.2 | Fix all performance SLA failures | varies |
| 6.3.3 | Cross-browser smoke test: Chrome, Firefox, Safari | 3 |
| 6.3.4 | Mobile viewport test: 375px width (iOS Safari) | 2 |

**Epic 6.4 — Security Hardening & Review** `SEC`

| Story | Description | Points |
|-------|-------------|--------|
| 6.4.1 | Semgrep full scan (`p/owasp-top-ten` + `p/python` + `p/typescript`): zero High/Critical findings; document any suppressions in `docs/security/FINDINGS_REGISTER.md`; add `semgrep` job to `security.yml` | 5 |
| 6.4.2 | CORS header audit: `Access-Control-Allow-Origin` never `*`; `OPTIONS` returns only `GET, OPTIONS` allowed methods | 2 |
| 6.4.3 | DuckDB WASM COEP/COOP validation: Vite dev server + `frontend/public/_headers` both serve `Cross-Origin-Embedder-Policy: require-corp` and `Cross-Origin-Opener-Policy: same-origin`; DuckDB WASM initializes in Playwright | 3 |
| 6.4.4 | Security regression tests (`tests/security/`): input validation (422 for out-of-bounds params), rate limiting (429 on 61st request), and error sanitization (no stack trace in 500 responses) | 5 |

**Phase 6 Definition of Done:**
- [ ] `pytest tests/features/ --tb=short` exits 0 (all Gherkin scenarios pass — count grows with phases; do not gate on a hardcoded number)
- [ ] `pytest tests/features/e2e/` → all E2E tests pass
- [ ] All 5 performance SLAs pass under `pytest-benchmark`
- [ ] Schemathesis: `--checks all` passes
- [ ] `pytest tests/security/` → 0 failures (input validation, rate limiting, error sanitization)
- [ ] `semgrep --config p/owasp-top-ten backend/ frontend/src/` → 0 High/Critical findings (or all documented)
- [ ] Cross-browser smoke test: Chrome, Firefox, Safari all pass (story 6.3.3)
- [ ] Mobile viewport test: 375px width passes smoke test (story 6.3.4)
- [ ] **Milestone M6 — Feature Complete**

---

### Phase 7 — Production Deployment (DuckDB WASM)
**Goal:** App deployed live on Cloudflare Pages. No server. $0/month. Full TRI history queryable.  
**Duration:** ~1.5 weeks  
**Team:** FE + DE (lead), OPS supports Cloudflare config

#### Epics & Stories

**Epic 7.1 — DuckDB WASM Integration** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 7.1.1 | Install `@duckdb/duckdb-wasm`; initialize in a Web Worker | 3 | WASM loads in < 2s; no UI thread blocking |
| 7.1.2 | `useDuckDBFacilities` hook replaces `GET /api/v1/facilities` | 5 | Radius + chemical + year + medium filters work via DuckDB SQL on Parquet |
| 7.1.3 | `useDuckDBSuperfund` hook replaces `GET /api/v1/superfund` | 3 | `ST_DWithin` on superfund Parquet returns correct sites |
| 7.1.4 | Chemical auto-complete via DuckDB: `SELECT DISTINCT name ... ILIKE` | 2 | < 100ms; matches API behavior |
| 7.1.5 | `useDuckDBDemographics` hook: loads county GeoJSON from R2 directly | 2 | Static GeoJSON (small file); no WASM query needed |
| 7.1.6 | `restrict_to_state` filter implemented client-side in DuckDB query | 2 | `WHERE state_code = $state` in Parquet query |
| 7.1.7 | CSV export: `conn.query(...).then(result => exportToCsv(result))` | 2 | Same CSV headers as API contract |
| 7.1.8 | Feature flag: `VITE_DATA_SOURCE=api|duckdb` — API used in dev, DuckDB in prod | 2 | `npm run build` uses DuckDB; `npm run dev` uses FastAPI |

**Epic 7.2 — Cloudflare Deployment** `OPS`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 7.2.1 | Cloudflare Pages project created; `npm run build` as build command | 2 | Push to `main` → auto-deploy |
| 7.2.2 | Cloudflare R2 bucket: CORS configured for `GET` on `*.parquet`, `*.meta.json`, `manifest.json`, and `*.pmtiles` | 2 | DuckDB WASM can fetch range requests from browser; `manifest.json` readable by React app on init |
| 7.2.3 | GitHub Actions: upload built Parquet + PMTiles to R2 on tag | 3 | `git tag v1.0.0` → files appear in R2 |
| 7.2.4 | Service worker: cache WASM + first Parquet chunks for offline use | 3 | Second visit loads without network (Chrome DevTools: offline) |

**Epic 7.3 — Smoke Tests Against Production** `QA`

| Story | Description | Points |
|-------|-------------|--------|
| 7.3.1 | Playwright smoke suite against `https://toxmap.pages.dev` | 3 |
| 7.3.2 | T-01 and T-03 pass against production Parquet data | 3 |

**Epic 7.4 — Production Security Hardening** `SEC + OPS`

| Story | Description | Points |
|-------|-------------|--------|
| 7.4.1 | `frontend/public/_headers`: full Cloudflare Pages security header set — CSP (`'wasm-unsafe-eval'` + `worker-src blob:`), COEP `require-corp`, COOP `same-origin`, HSTS `max-age=63072000`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy` | 3 |
| 7.4.2 | R2 bucket access audit: confirm Cloudflare API token has minimum IAM scope (Object Write on `toxmap-data` only); manual `PUT` attempt returns 403; document required token scopes in `SECURITY.md §Cloud Infrastructure` | 2 |
| 7.4.3 | Parquet + manifest integrity: add `integrity: "sha256-<base64>"` field per Parquet entry in `manifest.json`; `build_parquet.py` computes and writes it; React verifies `Content-Type: application/json` on manifest before parsing | 3 |

**Phase 7 Definition of Done:**
- [ ] App live at Cloudflare Pages URL
- [ ] `VITE_DATA_SOURCE=duckdb` build passes T-01 and T-03 smoke tests
- [ ] Page loads in < 3s on 4G (Lighthouse Performance > 80)
- [ ] $0 monthly cost verified (Cloudflare dashboard)
- [ ] `curl -I https://toxmap.pages.dev` → `cross-origin-embedder-policy: require-corp` + `strict-transport-security` + `x-frame-options: DENY` all present
- [ ] DuckDB WASM loads and queries successfully (confirms COEP/COOP headers are correct)
- [ ] **Milestone M7 — MVP Shipped 🚀**

---

### Phase 8 — Tribal Lands Data (Post-MVP)
**Goal:** Facilities on tribal lands queryable via dedicated filter. Users can select "Tribal" in state dropdown to view all TRI reporters on federally recognized tribal lands.  
**Duration:** ~1 week  
**Team:** DE (lead), BE, FE, QA supports

> **Background:** EPA TRI data includes facilities located on tribal lands, identified by Bureau of Indian Affairs (BIA) code (TRI Field 10) and tribe name (TRI Field 11). EPA also publishes separate "tribal data files" containing all submissions from facilities on tribal lands. This phase adds support for ingesting and filtering by tribal land location.

#### Epics & Stories

**Epic 8.1 — Schema Extension** `BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 8.1.1 | Add `bia_code VARCHAR(3)` and `tribe_name VARCHAR(350)` columns to `facilities` table | 2 | `alembic upgrade head` applies migration cleanly |
| 8.1.2 | Add index on `bia_code` for tribal filtering | 1 | `CREATE INDEX idx_facilities_bia_code ON facilities(bia_code) WHERE bia_code IS NOT NULL` |

**Epic 8.2 — TRI Tribal Data Ingestion** `DE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 8.2.1 | Update `TRI_COLUMN_MAP` with `"BIA": "bia_code"` and `"TRIBE": "tribe_name"` mappings | 1 | Columns mapped from TRI CSV Fields 10–11 |
| 8.2.2 | `tri_ingest.py`: populate `bia_code` and `tribe_name` from national data file | 2 | Non-null `bia_code` values present for tribal facilities after ingest |
| 8.2.3 | Optional: ingest EPA tribal-specific data file (`{year}_TRIBAL_US.csv`) for validation | 2 | Tribal file row count matches `SELECT COUNT(*) FROM facilities WHERE bia_code IS NOT NULL` |
| 8.2.4 | Seed data: add tribal facility test record | 1 | At least one facility with `bia_code='NAV'` (Navajo Nation) in `seed.sql` |

**Epic 8.3 — Tribal Filter API** `BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 8.3.1 | `GET /api/v1/facilities`: add `tribal_only=true` query parameter | 2 | Returns only facilities where `bia_code IS NOT NULL` |
| 8.3.2 | `GET /api/v1/facilities/browse`: support `tribal_only=true` | 1 | Browse mode returns all tribal facilities without radius constraint |
| 8.3.3 | `GET /api/v1/tribes`: list all tribes with facility counts | 3 | Returns `[{bia_code, tribe_name, facility_count}]` sorted by name |

**Epic 8.4 — Tribal Filter UI** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 8.4.1 | Add "Tribal Lands" option to state dropdown (after territories) | 2 | Option value `TRIBAL`; triggers `tribal_only=true` API param |
| 8.4.2 | Tribal filter: when selected, hide state dropdown and show tribe sub-dropdown | 3 | Sub-dropdown populated from `GET /api/v1/tribes`; optional filter by specific tribe |
| 8.4.3 | DuckDB WASM: `WHERE bia_code IS NOT NULL` filter for production mode | 2 | `useDuckDBFacilities` handles `tribal_only` flag |

**Epic 8.5 — Parquet & Export** `DE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 8.5.1 | `build_parquet.py`: include `bia_code` and `tribe_name` columns | 2 | Columns present in `tri_YEAR.parquet` schema |
| 8.5.2 | CSV export: include `bia_code` and `tribe_name` columns | 1 | Headers match updated API contract |

**Epic 8.6 — QA & Testing** `QA`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 8.6.1 | Gherkin scenario: T-10 "Find facilities on Navajo Nation tribal lands" | 3 | API + E2E scenarios pass with seeded tribal facility |
| 8.6.2 | UX regression: ensure state filter still works with tribal option added | 1 | T-01 still passes; state dropdown tests green |

**Phase 8 Definition of Done:**
- [ ] `bia_code` and `tribe_name` columns populated for all applicable facilities
- [ ] `GET /api/v1/facilities?tribal_only=true` returns only tribal facilities
- [ ] "Tribal Lands" option visible in state dropdown
- [ ] T-10 Gherkin scenario passes (API + E2E)
- [ ] Parquet files include tribal columns
- [ ] **Milestone M8 — Tribal Lands Data**

---

### Phase 9 — Multi-Chemical Search (Post-MVP)
**Goal:** Users can search for multiple chemicals simultaneously on a single map (F-23).  
**Duration:** ~1.5 weeks  
**Team:** BE (lead), FE, QA supports

> **Background:** UCD 2011 participants requested the ability to view releases of multiple chemicals at once (e.g., "show me all facilities releasing BOTH benzene AND toluene"). This requires API changes to accept multiple chemical parameters and frontend changes for multi-select UI.

#### Epics & Stories

**Epic 9.1 — API Multi-Chemical Support** `BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 9.1.1 | `GET /api/v1/facilities`: support `chemical` param as comma-separated list | 3 | `?chemical=BENZENE,TOLUENE` returns facilities releasing either |
| 9.1.2 | Add `chemical_match` param: `any` (default) or `all` | 2 | `chemical_match=all` returns only facilities releasing ALL listed chemicals |
| 9.1.3 | `GET /api/v1/facilities/browse`: support multi-chemical filtering | 2 | Browse mode respects multi-chemical filters |
| 9.1.4 | Update API contract documentation | 1 | `TOXMAP_API_CONTRACT.md` updated with multi-chemical examples |

**Epic 9.2 — Multi-Select Chemical UI** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 9.2.1 | Replace single chemical autocomplete with multi-select chip input | 4 | Users can add multiple chemicals as "chips"; each has X to remove |
| 9.2.2 | Add "Match any / Match all" toggle below chemical input | 2 | Toggle controls `chemical_match` API param |
| 9.2.3 | Results table: show which chemical(s) each facility releases | 2 | Column or tooltip shows matched chemicals per row |
| 9.2.4 | DuckDB WASM: multi-chemical WHERE clause | 2 | `useDuckDBFacilities` handles comma-separated chemicals |

**Epic 9.3 — Map Legend Updates** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 9.3.1 | Legend shows active chemical filters as pills | 2 | Chemical names visible in legend area when filtered |
| 9.3.2 | Color-coding option: different colors per chemical (optional) | 3 | Toggle for "Color by chemical" vs "Color by release volume" |

**Epic 9.4 — QA & Testing** `QA`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 9.4.1 | Gherkin scenario: T-11 "Search for facilities releasing benzene AND toluene" | 3 | API + E2E scenarios pass |
| 9.4.2 | Regression: single-chemical search still works | 1 | T-01, T-03 still pass |

**Phase 9 Definition of Done:**
- [ ] Multi-chemical search works via API and UI
- [ ] "Match any" and "Match all" modes functional
- [ ] T-11 Gherkin scenario passes
- [ ] **Milestone M9 — Multi-Chemical Search**

---

### Phase 10 — EPA Monitoring Sites (Post-MVP)
**Goal:** Overlay EPA air quality monitoring sites on the map (F-24).  
**Duration:** ~1.5 weeks  
**Team:** DE (lead), BE, FE, QA supports

> **Background:** UCD 2011 participants requested EPA monitoring site data to complement TRI facility data. EPA AQS (Air Quality System) provides monitoring station locations and pollutant measurements.

#### Epics & Stories

**Epic 10.1 — Data Ingestion** `DE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 10.1.1 | Create `monitoring_sites` table schema | 2 | Columns: `site_id`, `name`, `address`, `city`, `state_code`, `zip_code`, `location`, `pollutants[]`, `agency` |
| 10.1.2 | `monitoring_ingest.py`: parse EPA AQS site list CSV | 3 | All active monitoring sites ingested |
| 10.1.3 | Seed data: add 3 monitoring site test records | 1 | Sites in VA, TX, NV for test coverage |
| 10.1.4 | `build_parquet.py`: create `monitoring_sites.parquet` | 2 | Parquet file generated in build pipeline |

**Epic 10.2 — Monitoring Sites API** `BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 10.2.1 | `GET /api/v1/monitoring`: list monitoring sites within radius | 3 | Returns GeoJSON FeatureCollection |
| 10.2.2 | `GET /api/v1/monitoring/browse`: all sites (no radius) | 2 | Browse mode for monitoring layer |
| 10.2.3 | Filter by pollutant: `?pollutant=OZONE` | 2 | Returns only sites monitoring that pollutant |

**Epic 10.3 — Monitoring Layer UI** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 10.3.1 | Add "EPA Monitoring Sites" toggle in Map Contents panel | 2 | Checkbox in new "Monitoring" section |
| 10.3.2 | Monitoring site markers: distinct triangle icon | 3 | Triangle shape, green color, distinguishable from TRI/Superfund |
| 10.3.3 | Monitoring site popup: site name, agency, pollutants monitored | 2 | Popup on marker click |
| 10.3.4 | Legend: add monitoring site icon | 1 | Triangle icon in legend when layer active |
| 10.3.5 | DuckDB WASM: `useMonitoringSites` hook | 3 | Production mode queries monitoring parquet |

**Epic 10.4 — QA & Testing** `QA`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 10.4.1 | Gherkin scenario: T-12 "Find EPA monitoring sites near Houston" | 3 | API + E2E scenarios pass |
| 10.4.2 | Visual regression: monitoring icons don't overlap TRI/Superfund | 1 | Icons distinguishable at zoom level 10 |

**Phase 10 Definition of Done:**
- [ ] Monitoring sites visible on map when toggled
- [ ] Popup shows site details
- [ ] T-12 Gherkin scenario passes
- [ ] **Milestone M10 — EPA Monitoring Sites**

---

### Phase 11 — Onboarding & UX Polish (Post-MVP)
**Goal:** In-app tutorial for first-time users + consolidated icon toolbar (F-21, F-22).  
**Duration:** ~1 week  
**Team:** FE (lead), QA supports

> **Background:** UCD 2011 found a steep learning curve for non-GIS users. Participants requested an in-app tutorial. The study also noted redundant menus + icon toolbars causing confusion.

#### Epics & Stories

**Epic 11.1 — In-App Tutorial** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 11.1.1 | Tutorial overlay component with step-by-step guide | 4 | Modal with "Next" / "Previous" / "Skip" buttons |
| 11.1.2 | Tutorial step 1: Search panel introduction | 2 | Highlights chemical + location fields |
| 11.1.3 | Tutorial step 2: Map interaction basics | 2 | Highlights zoom controls + marker click |
| 11.1.4 | Tutorial step 3: Results table usage | 2 | Highlights facility selection + detail drawer |
| 11.1.5 | Tutorial step 4: Layer toggles | 2 | Highlights TRI/Superfund/Demographics toggles |
| 11.1.6 | "Show tutorial again" link in footer or help menu | 1 | Tutorial can be restarted anytime |
| 11.1.7 | LocalStorage flag: don't show tutorial after first completion | 1 | `toxmap_tutorial_completed` flag |

**Epic 11.2 — Toolbar Consolidation** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 11.2.1 | Audit current navigation: remove redundant text menus | 2 | Single navigation mechanism (labeled icons) |
| 11.2.2 | Add icon labels below or on hover | 2 | All toolbar icons have accessible labels |
| 11.2.3 | Keyboard navigation for toolbar | 2 | Tab through icons; Enter activates |

**Epic 11.3 — QA & Testing** `QA`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 11.3.1 | Gherkin scenario: T-13 "First-time user completes tutorial" | 3 | E2E test walks through tutorial |
| 11.3.2 | Accessibility audit: toolbar keyboard navigation | 2 | WCAG 2.1 AA compliance for toolbar |

**Phase 11 Definition of Done:**
- [ ] Tutorial appears for first-time users
- [ ] Tutorial can be skipped and restarted
- [ ] Toolbar has single navigation mechanism
- [ ] T-13 Gherkin scenario passes
- [ ] **Milestone M11 — Onboarding & UX Polish**

---

### Phase 12 — Canadian NPRI (Post-MVP)
**Goal:** Canadian National Pollutant Release Inventory facility layer (F-25).  
**Duration:** ~1.5 weeks  
**Team:** DE (lead), BE, FE, QA supports

> **Background:** NLM's 2013 TOXMAP redesign included Canadian NPRI data. This extends coverage beyond US borders for researchers studying cross-border pollution patterns.

#### Epics & Stories

**Epic 12.1 — NPRI Data Ingestion** `DE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 12.1.1 | Create `npri_facilities` table schema | 2 | Columns: `npri_id`, `name`, `address`, `city`, `province`, `postal_code`, `location`, `naics_code` |
| 12.1.2 | `npri_ingest.py`: parse NPRI CSV from Environment Canada | 4 | All reporting facilities ingested |
| 12.1.3 | Create `npri_releases` table for release events | 2 | Links to chemicals table |
| 12.1.4 | Seed data: add 2 Canadian facility test records | 1 | Facilities in ON, AB for test coverage |
| 12.1.5 | `build_parquet.py`: create `npri_YEAR.parquet` | 2 | Parquet file generated |

**Epic 12.2 — NPRI API** `BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 12.2.1 | `GET /api/v1/npri`: list NPRI facilities within radius | 3 | Returns GeoJSON FeatureCollection |
| 12.2.2 | `GET /api/v1/npri/browse`: all NPRI facilities | 2 | Browse mode for NPRI layer |
| 12.2.3 | Filter by chemical, year, province | 2 | Same filter patterns as TRI |

**Epic 12.3 — NPRI Layer UI** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 12.3.1 | Add "Canadian NPRI" toggle in Map Contents panel | 2 | Checkbox in TRI Layers section |
| 12.3.2 | NPRI markers: maple leaf or distinct icon | 3 | Distinguishable from US TRI markers |
| 12.3.3 | NPRI facility drawer: release details | 2 | Same format as TRI drawer |
| 12.3.4 | Map extends to show Canada when NPRI toggled | 2 | Viewport includes southern Canada |
| 12.3.5 | DuckDB WASM: `useNPRIFacilities` hook | 3 | Production mode queries NPRI parquet |

**Epic 12.4 — QA & Testing** `QA`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 12.4.1 | Gherkin scenario: T-14 "Find NPRI facilities in Ontario" | 3 | API + E2E scenarios pass |
| 12.4.2 | Cross-border search: US + Canada results combined | 2 | Radius search near Detroit shows both |

**Phase 12 Definition of Done:**
- [ ] NPRI facilities visible on map when toggled
- [ ] Province filter works for NPRI
- [ ] T-14 Gherkin scenario passes
- [ ] **Milestone M12 — Canadian NPRI**

---

### Phase 13 — Nuclear Power Plants (Post-MVP)
**Goal:** US commercial nuclear facility location overlay (F-26).  
**Duration:** ~1 week  
**Team:** DE (lead), BE, FE, QA supports

> **Background:** NLM's 2013 TOXMAP redesign included nuclear power plant locations. This provides context for radioactive material releases and proximity analysis.

#### Epics & Stories

**Epic 13.1 — Nuclear Data Ingestion** `DE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 13.1.1 | Create `nuclear_plants` table schema | 2 | Columns: `plant_id`, `name`, `operator`, `city`, `state_code`, `location`, `reactor_count`, `status` |
| 13.1.2 | `nuclear_ingest.py`: parse NRC plant list | 2 | All ~100 commercial plants ingested |
| 13.1.3 | Seed data: add 2 nuclear plant test records | 1 | Plants in PA, CA for test coverage |
| 13.1.4 | `build_parquet.py`: create `nuclear_plants.parquet` | 1 | Parquet file generated |

**Epic 13.2 — Nuclear API** `BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 13.2.1 | `GET /api/v1/nuclear`: list plants within radius | 2 | Returns GeoJSON FeatureCollection |
| 13.2.2 | `GET /api/v1/nuclear/browse`: all plants | 1 | Browse mode for nuclear layer |

**Epic 13.3 — Nuclear Layer UI** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 13.3.1 | Add "Nuclear Power Plants" toggle in Map Contents panel | 2 | Checkbox in new "Infrastructure" section |
| 13.3.2 | Nuclear markers: radiation symbol or distinct icon | 2 | Yellow/black distinguishable icon |
| 13.3.3 | Nuclear popup: plant name, operator, reactor count | 1 | Popup on marker click |
| 13.3.4 | DuckDB WASM: `useNuclearPlants` hook | 2 | Production mode queries parquet |

**Epic 13.4 — QA & Testing** `QA`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 13.4.1 | Gherkin scenario: T-15 "Find nuclear plants near Philadelphia" | 2 | API + E2E scenarios pass |

**Phase 13 Definition of Done:**
- [ ] Nuclear plants visible on map when toggled
- [ ] Popup shows plant details
- [ ] T-15 Gherkin scenario passes
- [ ] **Milestone M13 — Nuclear Power Plants**

---

### Phase 14 — Congressional Districts (Post-MVP)
**Goal:** Congressional district boundary overlay for political context (F-27).  
**Duration:** ~1 week  
**Team:** DE (lead), BE, FE, QA supports

> **Background:** NLM's 2013 TOXMAP redesign included congressional district boundaries. This enables users to identify their representative for advocacy purposes.

#### Epics & Stories

**Epic 14.1 — District Data Ingestion** `DE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 14.1.1 | Create `congressional_districts` table schema | 2 | Columns: `district_id`, `state_code`, `district_number`, `representative`, `party`, `boundary` (geometry) |
| 14.1.2 | `districts_ingest.py`: parse Census TIGER congressional district shapefiles | 3 | All 435 districts + territories ingested |
| 14.1.3 | Seed data: add VA-07, TX-29 district test records | 1 | Districts with test facilities inside |
| 14.1.4 | `build_parquet.py`: create `districts.parquet` with geometries | 2 | GeoParquet file generated |

**Epic 14.2 — Districts API** `BE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 14.2.1 | `GET /api/v1/districts`: list districts intersecting bbox | 2 | Returns GeoJSON FeatureCollection |
| 14.2.2 | `GET /api/v1/districts/{state}`: districts for a state | 2 | Filter by state code |

**Epic 14.3 — Districts Layer UI** `FE`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 14.3.1 | Add "Congressional Districts" toggle in Map Contents panel | 2 | Checkbox in Demographics section |
| 14.3.2 | District boundary polygons: outline style (not filled) | 3 | Dashed or solid outline, labeled with district number |
| 14.3.3 | District popup: representative name, party, contact link | 2 | Popup on polygon click |
| 14.3.4 | DuckDB WASM: `useDistricts` hook with spatial queries | 3 | Production mode queries GeoParquet |

**Epic 14.4 — QA & Testing** `QA`

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| 14.4.1 | Gherkin scenario: T-16 "View congressional district for a TRI facility" | 3 | E2E: click facility → see district overlay |
| 14.4.2 | Performance: district polygons don't slow map | 1 | Viewport render < 500ms with districts on |

**Phase 14 Definition of Done:**
- [ ] Congressional district boundaries visible on map when toggled
- [ ] Popup shows representative info
- [ ] T-16 Gherkin scenario passes
- [ ] **Milestone M14 — Congressional Districts**

---

## 6. Testing Strategy & Cadence

| Phase | QA Activity | Target Coverage |
|-------|-------------|-----------------|
| 0 | Write `seed.sql`, configure pytest-bdd + Playwright | Infrastructure |
| 1 | Validate ingestion: row counts, T-03/T-04 raw SQL queries | Data integrity |
| 2 | Implement API step stubs; run Features 1–6 as endpoints ship | API contract |
| 3 | Implement E2E steps T-01, T-03, T-08; run UX invariants 1–4, 7–9 | Core user flows |
| 4 | Implement T-02, T-04; run UX invariant 6 | Superfund layer |
| 5 | Implement T-05, T-06, T-09; run UX invariants 5, 10 | Demographics layer |
| 6 | Bug bash; all Gherkin scenarios + performance SLAs (`pytest tests/features/ --tb=short` exits 0) | Full coverage |
| 7 | Production smoke suite against Cloudflare URL | Deploy validation |
| 8 | T-10 tribal scenario; regression tests for state filter | Tribal lands filter |
| 9 | T-11 multi-chemical scenario; single-chemical regression | Multi-chemical search |
| 10 | T-12 monitoring sites scenario; visual regression | EPA monitoring overlay |
| 11 | T-13 onboarding scenario; accessibility audit | Tutorial + toolbar |
| 12 | T-14 NPRI scenario; cross-border search | Canadian NPRI layer |
| 13 | T-15 nuclear plants scenario | Nuclear overlay |
| 14 | T-16 congressional districts scenario; performance | Districts overlay |

**Test Execution Commands (Reference):**

```bash
# Unit tests (Phase 0+)
pytest tests/unit/

# All API Gherkin scenarios (Phase 2+)
pytest tests/features/api/ -v

# E2E scenarios (Phase 3+)
pytest tests/features/e2e/

# Full suite
pytest tests/

# Contract validation
schemathesis run http://localhost:8000/openapi.json --checks all

# Performance benchmarks
pytest tests/benchmarks/ --benchmark-only
```

---

## 7. Risk Register

| ID | Risk | Probability | Impact | Mitigation | Owner |
|----|------|------------|--------|-----------|-------|
| R-01 | EPA TRI CSV format changes annually (column renames) | High | Medium | Column mapping dict in `tri_parser.py`; version-pinned mapping per year | DE |
| R-02 | Cloudflare R2 free tier exceeded (10 GB) if full TRI history loaded | Medium | Medium | Per-year Parquet files; user downloads only the years queried (HTTP range) | DE |
| R-03 | DuckDB WASM spatial extension unavailable or broken on Safari iOS | Medium | High | Feature-detect on load; fall back to API (Option B / Fly.io) if WASM fails | FE |
| R-04 | Supabase free tier pauses after 1 week inactivity (if Option B fallback used) | High | Low | Cron ping job in GitHub Actions every 5 days | OPS |
| R-05 | PMTiles generation requires 100 GB planet file download | Low | High | Use US-only extract (~8 GB); Protomaps provides pre-built US extracts | DE |
| R-06 | MapLibre GL WebGL not supported on all target browsers | Low | High | Graceful degradation to Leaflet.js fallback layer | FE |
| R-07 | Census TIGER shapefile boundary complexity causes slow polygon queries | Medium | Medium | Simplify geometries at ingestion (`ST_Simplify` with 0.001 tolerance) | DE |
| R-08 | ATSDR ToxFAQ URL format changes (external dependency) | Low | Low | Store full URLs in `chemicals` table; update annually with ingestion | DE |
| R-09 | Parquet build targets July preliminary dataset instead of October-frozen dataset, understating releases by ~1–9% | **High** | **High** | Build pipeline must run at October checkpoint (primary) and April spring refresh; preliminary build labeled as such and not used as production default. EPA measured +1.4% release qty and +9% waste management qty drift between preliminary and frozen snapshots for the same year. Source: [EPA TRI Data Considerations](https://www.epa.gov/toxics-release-inventory-tri-program/tri-data-considerations) | DE + OPS |
| R-10 | DuckDB WASM requires `SharedArrayBuffer` which requires `Cross-Origin-Embedder-Policy: require-corp` + `Cross-Origin-Opener-Policy: same-origin`; missing headers cause WASM to fail silently or degrade to single-threaded mode across all browsers | **High** | **High** | Configure COEP/COOP in both Vite dev server headers and Cloudflare Pages `_headers`; validate with Playwright in Phase 6 (story 6.4.3) | SEC + OPS |
| R-11 | No rate limiting at MVP launch; a single client issuing `radius_miles=500` queries in a tight loop could exhaust PostGIS resources and degrade service for all users | **Medium** | **High** | `slowapi` rate limiting (60 req/min per IP) added in Phase 2 (story 2.8.2); production DuckDB WASM path has no server to exhaust | SEC + BE |
| R-12 | GitHub Actions workflows pin dependencies with mutable version tags (e.g., `cloudflare/wrangler-action@v3`); a compromised tag could poison the Parquet build pipeline or push malicious assets to R2 | **Medium** | **High** | Pin all third-party Actions to full 40-char SHA in Phase 0 (story 0.5.4); use Dependabot to track SHA updates | SEC + OPS |

---

## 8. Definition of Ready (Per Story)

A story is **Ready** when:
- [ ] Acceptance criteria are written and linked to a Gherkin scenario or acceptance test
- [ ] Seed data required for the test exists in `seed.sql`
- [ ] API contract for the endpoint exists in `TOXMAP_API_CONTRACT.md`
- [ ] UI reference screenshot identified in `TOXMAP_SCREEN_CATALOG.md` (if FE story)
- [ ] Dependencies on prior stories are complete

## 9. Definition of Done (Per Story)

A story is **Done** when:
- [ ] Code merged to `main` via reviewed PR
- [ ] Associated Gherkin scenario passes in CI
- [ ] No new Schemathesis failures introduced
- [ ] No `any` types added to TypeScript (FE)
- [ ] `docker compose up` still works from cold start
- [ ] `security.yml` still passes (no new secrets, no new CVEs above threshold, bandit clean)

---

## 10. Story Point Summary by Phase

| Phase | BE | FE | DE | QA | OPS | SEC | Total |
|-------|----|----|----|----|-----|-----|-------|
| Phase 0 — Foundation | 4 | 2 | 0 | 8 | 12 | 7 | **33** |
| Phase 1 — Data Pipeline | 10 | 0 | 33 | 0 | 3 | 2 | **48** |
| Phase 2 — Core API | 44 | 0 | 0 | 8 | 0 | 10 | **62** |
| Phase 3 — Core Map UI | 0 | 54 | 0 | 15 | 0 | 3 | **72** |
| Phase 4 — Superfund | 0 | 18 | 0 | 10 | 0 | 0 | **28** |
| Phase 5 — Demographics | 0 | 25 | 0 | 8 | 0 | 0 | **33** |
| Phase 6 — Full QA | 5 | 5 | 0 | 26 | 0 | 15 | **51** |
| Phase 7 — Production | 0 | 22 | 5 | 6 | 10 | 8 | **51** |
| Phase 8 — Tribal Lands | 3 | 7 | 6 | 4 | 0 | 0 | **20** |
| Phase 9 — Multi-Chemical | 8 | 15 | 0 | 4 | 0 | 0 | **27** |
| Phase 10 — EPA Monitoring | 7 | 11 | 8 | 4 | 0 | 0 | **30** |
| Phase 11 — Onboarding/UX | 0 | 20 | 0 | 5 | 0 | 0 | **25** |
| Phase 12 — Canadian NPRI | 7 | 12 | 11 | 5 | 0 | 0 | **35** |
| Phase 13 — Nuclear Plants | 3 | 7 | 6 | 2 | 0 | 0 | **18** |
| Phase 14 — Congressional | 4 | 10 | 8 | 4 | 0 | 0 | **26** |
| **Total** | **91** | **204** | **77** | **109** | **25** | **45** | **559** |

> At a team velocity of ~20 points/week (2 devs), this is approximately **28 weeks** for full feature set.  
> At 30 points/week (3 devs), approximately **19 weeks**.
> 
> **Note:** Phases 8–14 are post-MVP enhancements. MVP ships at Phase 7 (~378 points).
> Post-MVP features (F-21 through F-27) add ~181 points across Phases 8–14.

---

## 11. Handoff Checklist

Before development begins, confirm the following are complete:

**Documentation ✅**
- [ ] All 9 TOXMAP artifact files reviewed by Engineering Lead
- [ ] `TOXMAP_ACCEPTANCE_TESTS.md` — all Gherkin scenarios understood by QA
- [ ] `TOXMAP_TEST_SEED_DATA.md` — exact seed values confirmed by DE
- [ ] `TOXMAP_API_CONTRACT.md` — 17 endpoint contracts reviewed by BE
- [ ] `TOXMAP_SCREEN_CATALOG.md` — 18 screenshots reviewed by FE

**Environment ✅**
- [ ] GitHub repo created, branch protection enabled
- [ ] Cloudflare account created (free, no CC required)
- [ ] GitHub Actions secrets configured: `CF_API_TOKEN`, `CF_ACCOUNT_ID`
- [ ] All developers have Docker Desktop installed

**Decisions Locked ✅**
- [ ] ADR-001 (FastAPI stack) accepted by team
- [ ] ADR-004 (Cloudflare + DuckDB WASM) accepted as production target
- [ ] ADR-002 and ADR-003 formally rejected (documented)
- [ ] $0 budget constraint acknowledged by all stakeholders

**First Sprint Backlog (Phase 0, Week 1):**
1. `0.1.1` — Create GitHub repo
2. `0.2.1` — Docker Compose skeleton
3. `0.2.2` — PostGIS service
4. `0.4.2` — `seed.sql` file from seed data doc
5. `0.3.1` — CI pipeline

---

## 12. Contacts & Escalation

| Topic | Go To |
|-------|-------|
| **Where are we in the project?** | `CURRENT_PHASE.txt` + `docs/product/TOXMAP_PROGRESS_TRACKER.md` |
| **Which agent should run next?** | `agents/phase-manager/prompt.md` |
| Requirements clarification (F-01 through F-27) | `TOXMAP_TECH_STACK_ANALYSIS.md §3` |
| UX invariant disputes | `TOXMAP_TECH_STACK_ANALYSIS.md §8` + `TOXMAP_SCREEN_CATALOG.md` |
| API shape questions | `TOXMAP_API_CONTRACT.md` |
| Test data questions | `TOXMAP_TEST_SEED_DATA.md §9` (Known Good Assertion Values) |
| Architecture decisions | `ADR-001`, `ADR-002`, `ADR-003`, `ADR-004` |
| Hosting budget questions | `ADR-004` |
| Phase advancement / sprint status | `agents/phase-manager/prompt.md` → Phase Manager agent |
| Agent blocker triage | Open `[agent-escalation]` issue; Phase Manager is first triage |

