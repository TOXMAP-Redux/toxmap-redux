# TOXMAP Testing Strategy

**Author:** Victor Cannestro  
**Date:** 2026-07-17  
**Status:** Accepted  
**Linked ADR:** [ADR-001](../adr/ADR-001-fastapi-postgis-react.md) · [ADR-004](../adr/ADR-004-zero-budget-hosting.md)

---

## Table of Contents

1. [Testing Goals](#1-testing-goals)
2. [Architecture Under Test](#2-architecture-under-test)
3. [Testing Methodologies](#3-testing-methodologies)
4. [Tool Selection](#4-tool-selection)
5. [Risk Management](#5-risk-management)
6. [CI/CD Strategy](#6-cicd-strategy)
7. [Coverage Targets](#7-coverage-targets)
8. [Linked Test Plans](#8-linked-test-plans)

---

## 1. Testing Goals

TOXMAP is an open-source geospatial application (FastAPI + PostGIS + React/MapLibre) that reproduces the original NLM TOXMAP, decommissioned in 2019. Testing must satisfy six non-negotiable goals:

| #   | Goal                                                                                                  | Driver                                                                 |
|-----|-------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| G-1 | Verify geospatial query correctness — radius, bbox, state filter, color band assignment               | PostGIS spatial logic is complex and failure is silent                 |
| G-2 | Lock in API contract stability so the React frontend and future consumers can rely on response shapes | Single-page app is tightly coupled to JSON schema                      |
| G-3 | Validate all 9 UCD 2011 task scenarios end-to-end in a real browser with real seed data               | Usability study is the authoritative source of functional requirements |
| G-4 | Enforce all  UX design invariants derived from the 2011 usability critical findings                   | Prior regression against these invariants degraded user experience     |
| G-5 | Support zero-budget production (DuckDB WASM) — test harness must not require a running server         | Production runs without any backend                                    |
| G-6 | Run fully automated on every pull request without manual setup beyond `docker compose up`             | Open-source project; contributor onboarding must be frictionless       |

---

## 2. Architecture Under Test

```
┌──────────────────────────────────────────────────────────────┐
│  Browser (React 18 · MapLibre GL · Recharts · Tailwind)      │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS REST/JSON
┌───────────────────────────▼──────────────────────────────────┐
│  FastAPI ≥ 0.111.0 (Python 3.12)                             │
│  Routers → Services → Repositories                           │
│  SQLAlchemy 2.0 async · GeoAlchemy2                          │
└───────────────────────────┬──────────────────────────────────┘
                            │ asyncpg
┌───────────────────────────▼──────────────────────────────────┐
│  PostgreSQL 16 + PostGIS 3.4                                 │
│  facilities · release_events · chemicals                     │
│  superfund_sites · census_county                             │
└──────────────────────────────────────────────────────────────┘

Production mode (no server):
  React → DuckDB WASM → Parquet files on Cloudflare R2
```

### Two-Mode Awareness

Per [ADR-004](../adr/ADR-004-zero-budget-hosting.md), TOXMAP runs in two fundamentally different modes. Test layer applicability differs by mode:

| Mode           | Backend           | Data Source                            | Applicable Test Layers                             |
|----------------|-------------------|----------------------------------------|----------------------------------------------------|
| **Dev / CI**   | FastAPI + PostGIS | Live PostgreSQL                        | Layers 1–5                                         |
| **Production** | None (static CDN) | DuckDB WASM + Parquet on Cloudflare R2 | Layers 1–2 only; Layer 5 smoke via `PROD_BASE_URL` |

Endpoints marked `⚠️ dev only` in [TOXMAP_API_CONTRACT.md](../api/TOXMAP_API_CONTRACT.md) are excluded from production E2E runs.

---

## 3. Testing Methodologies

The test suite is organized into five primary layers plus four cross-cutting concerns. Each layer has a distinct purpose, scope boundary, and execution trigger.

| Layer                       | Type      | Purpose                                                                                                                                                  | Scope Boundary                                           | Trigger                        | Responsible       |
|-----------------------------|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------|--------------------------------|-------------------|
| **1 — Unit**                | Automated | Verify pure logic with zero I/O: color band thresholds, GeoJSON coordinate order, Pydantic validation, comma formatting, sidebar state machine           | No database, network, or filesystem                      | Every push                     | Dev / QA          |
| **2 — Component**           | Automated | Verify service-layer contracts in isolation using mocked repositories (backend) and MSW (React frontend)                                                 | No real DB or network                                    | Every push                     | Dev / QA          |
| **3 — Integration**         | Automated | Verify FastAPI request-response correctness against a real PostGIS database loaded with deterministic seed data                                          | Real PostGIS, seeded; no browser                         | Every PR                       | QA                |
| **4 — API Contract**        | Automated | Validate all 17 endpoints against the OpenAPI schema via Schemathesis fuzzing + 40 explicit BDD scenarios; enforce response headers and performance SLAs | Real PostGIS, seeded; committed OpenAPI spec; no browser | Every PR                       | QA                |
| **5 — E2E / UI Acceptance** | Automated | Drive a real browser through the 9 UCD 2011 task scenarios and  UX design invariants against the full stack                                              | Full stack: FastAPI + PostGIS + React; browser           | PR (smoke); `main`/tags (full) | QA                |
| **A11y**                    | Automated | WCAG 2.1 AA compliance via axe-core on key UI views                                                                                                      | Full stack; browser                                      | Phase 5 / weekly               | QA                |
| **Visual Regression**       | Automated | Pixel-level rendering stability for map, popups, choropleth overlays                                                                                     | Full stack; browser                                      | Weekly                         | QA                |
| **Security**                | Automated | SQL injection prevention, XSS escaping, CORS header validation                                                                                           | API layer; real PostGIS                                  | Release gates                  | QA                |
| **Mutation**                | Automated | Measure test suite quality on highest-risk pure-logic modules                                                                                            | Offline code mutation                                    | Phase 5 / on demand            | QA lead           |
| **Exploratory / Manual**    | Manual    | Edge cases, UX judgment calls, release candidate sign-off                                                                                                | Any environment                                          | Release candidate              | QA / Stakeholders |

### TOXMAP-Specific Testing Considerations

**Geospatial correctness**: PostGIS queries are asserted against known geographic fixture points with specific radius 
values that must deterministically include or exclude seeded facilities. Unit tests verify coordinate serialization 
order (`[lon, lat]` per RFC 7946) independently of integration behavior.

**UCD 2011 fidelity**: The 9 task scenarios and 10 UX invariants are automated as Gherkin BDD scenarios (Layer 5). They
are the authoritative acceptance criteria and may not be removed without maintainer approval.

**Production-mode divergence**: A separate production smoke suite runs against the Cloudflare Pages deployment using 
relaxed assertions (`>= 1 facility`) rather than fixture-exact values.

**TRI unit integrity (R-12)**: Per TRI Data Audit 2026-07-23, the `release_events.unit_of_measure` column distinguishes 
pounds (all non-dioxin chemicals) from grams (dioxin/dioxin-like compounds, N150). All seed records use `'Pounds'`; the
test suite asserts this in Feature 2 and Feature 6 scenarios. Any future ingestion of dioxin facility data requires the 
frontend to read `meta.units` before rendering release quantities — an omission causes a ~453× display error. Layer 1 
unit tests must include a test for the color-band logic receiving a gram-unit record and scaling thresholds accordingly.

---

## 4. Tool Selection

### Test Execution

| Layer(s)     | Language    | Framework                           | Rationale                                                                 |
|--------------|-------------|-------------------------------------|---------------------------------------------------------------------------|
| 1–4 Backend  | Python 3.12 | `pytest` ≥ 8.0                      | Single runner for all Python test layers; rich plugin ecosystem           |
| 1–2 Frontend | TypeScript  | `Vitest` + `@testing-library/react` | Co-located with Vite build; fast HMR-mode execution                       |
| BDD (all)    | Python      | `pytest-bdd` ≥ 7.0                  | Gherkin feature files shared between API (Layer 4) and E2E (Layer 5)      |
| 5 E2E        | Python      | `pytest-playwright` ≥ 0.5           | **All Playwright automation in Python** — no TypeScript Playwright runner |

### Specialized Tools

| Concern                       | Tool                    | Purpose                                                                                      |
|-------------------------------|-------------------------|----------------------------------------------------------------------------------------------|
| API contract fuzzing          | `schemathesis`          | Property-based testing against `openapi.json`; auto-generates hundreds of edge-case requests |
| OpenAPI drift detection       | `test_openapi_drift.py` | Asserts committed `openapi.json` matches live `/openapi.json` on every PR                    |
| Performance SLA               | `pytest-benchmark`      | Measures p95 latency for key endpoints against documented SLAs                               |
| Accessibility                 | `axe-playwright-python` | Injects axe-core via `page.evaluate()`, asserts WCAG 2.1 AA                                  |
| Visual regression             | `Pillow` + `numpy`      | Pixel-diff comparison of Playwright screenshots against committed baselines                  |
| Mutation testing — Python     | `mutmut`                | Mutates `app/domain/` and `app/services/`; target ≥ 85% kill rate                            |
| Mutation testing — TypeScript | `Stryker`               | Mutates `src/utils/formatters.ts` and `src/state/sidebarState.ts`                            |

### Infrastructure

| Component         | Solution                                     | Notes                                                                                |
|-------------------|----------------------------------------------|--------------------------------------------------------------------------------------|
| Test database     | `postgis/postgis:16-3.4` Docker image        | Pinned to exact version to prevent spatial function drift                            |
| DB fixture driver | `psycopg2-binary`                            | Synchronous; used in `conftest.py` only — separate from the app's `asyncpg`          |
| Seed data         | `tests/fixtures/seed.sql`                    | Single source of truth; `seed_db` fixture loads before each test and TRUNCATEs after |
| Browser binaries  | `playwright install chromium firefox webkit` | Installed via Python CLI; `npm install playwright` is **not** required               |
| CI environment    | GitHub Actions `ubuntu-latest`               | PostGIS runs as a service container; browser binaries installed per-job              |

---

## 5. Risk Management

| ID   | Risk                                                                                                                             | Likelihood | Impact | Mitigation                                                                                                                                                                                                                           |
|------|----------------------------------------------------------------------------------------------------------------------------------|------------|--------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| R-01 | GeoJSON coordinate order inversion (`[lat,lon]` vs RFC 7946 `[lon,lat]`) silently misplaces map pins                             | Medium     | High   | `test_geojson_builder.py` asserts order explicitly; `test_geojson_rfc7946.py` validates all spatial endpoints                                                                                                                        |
| R-02 | PostGIS `ST_DWithin` results diverge between PostGIS point releases                                                              | Low        | High   | Pin `postgis/postgis:16-3.4` in CI; integration tests include 1-mile exclusion and 10-mile inclusion boundary cases                                                                                                                  |
| R-03 | DuckDB WASM production mode diverges from FastAPI dev mode                                                                       | Medium     | High   | Separate production smoke E2E suite; Parquet schema validated against OpenAPI schema in CI                                                                                                                                           |
| R-04 | MapLibre GL WebGL unavailable in CI headless Chromium                                                                            | Medium     | Medium | `--disable-gpu` flag; canvas-pixel assertions avoided; DOM/text assertions preferred for map state                                                                                                                                   |
| R-05 | `data-testid` selectors added without updating TEST_ID_REGISTRY.md                                                               | Medium     | Medium | Registry is authoritative; PR review checklist enforces registry-first                                                                                                                                                               |
| R-06 | Date-sensitive seed fixture fields (`eventTimestamp`, `startDate`) become past-dated                                             | High       | Low    | Pre-test-cycle review checklist in each test plan; TOXMAP_TEST_SEED_DATA.md annotates all date-sensitive fields                                                                                                                      |
| R-07 | OpenAPI spec drift — `openapi.json` committed to VCS falls out of sync with running app                                          | Medium     | Medium | `test_openapi_drift.py` is a required CI gate; PR blocked if spec diverges                                                                                                                                                           |
| R-08 | `pytest-xdist` parallel execution corrupts shared seed data state                                                                | Low        | High   | `addopts = "-p no:xdist"` enforced in `pyproject.toml`; documented in `conftest.py` header                                                                                                                                           |
| R-09 | UCD 2011 exact assertion values inadvertently changed in `seed.sql`                                                              | Low        | High   | Protected records documented in TOXMAP_TEST_SEED_DATA.md; any change requires maintainer-approved PR                                                                                                                                 |
| R-10 | axe-core false positives on MapLibre `<canvas>` element                                                                          | Medium     | Low    | Accessibility scans scoped to named components via `axe.run()` context; canvas excluded                                                                                                                                              |
| R-11 | E2E full suite wall time exceeds CI budget                                                                                       | Medium     | Low    | Smoke subset (3 scenarios) gates every PR; full suite on `main`/tags only; WebKit is smoke-only                                                                                                                                      |
| R-12 | `unit_of_measure` absent from API response silently causes dioxin quantities to be displayed as pounds — a ~453× magnitude error | Low        | High   | Feature 2 and Feature 6 Gherkin scenarios assert `unit_of_measure` is present in every `release_events` response item and CSV row; Parquet `schema_version = "1.1"` check (A-038) detects stale pre-audit files that lack the column |

### Risk Review Cadence

- **Continuous (every CI run):** R-01, R-07, R-08 — enforced by automated gates
- **Every deployment:** R-03 — production smoke suite
- **Sprint start:** R-06 — QA lead reviews date-sensitive fixtures
- **Phase transitions and release candidate:** All risks reviewed

---

## 6. CI/CD Strategy

All test stages run within GitHub Actions. Fast, infrastructure-free stages gate slower, infrastructure-dependent stages.

| Stage                  | Layers                                         | Trigger                         | Pass Criteria                                                    | Duration |
|------------------------|------------------------------------------------|---------------------------------|------------------------------------------------------------------|----------|
| Unit                   | 1                                              | Every push                      | All green; backend coverage ≥ 80% new code                       | ~30s     |
| Component              | 2                                              | Every push                      | All green                                                        | ~60s     |
| Integration + Contract | 3, 4                                           | Every PR                        | All green; Schemathesis 0 violations; OpenAPI drift check passes | ~8 min   |
| E2E Smoke              | 5 (T-01, T-03, T-08 + Invariants 1–4, 7–9, 11) | Every PR                        | Passing on Chromium                                              | ~5 min   |
| E2E Full + A11y        | 5 (all 26), A11y                               | `main` / version tags           | All E2E passing; Chromium + Firefox; 0 critical a11y violations  | ~20 min  |
| Visual Regression      | Visual                                         | Scheduled weekly                | Pixel diff ≤ 2% on all baselines                                 | ~10 min  |
| Production Smoke       | 5 (prod mode)                                  | Post-deploy to Cloudflare Pages | T-01, T-03, T-08 pass against real EPA data                      | ~5 min   |

**Branch protection:** `main` requires Unit + Component + Integration + Contract + E2E Smoke. Release tags additionally require E2E Full + A11y.

---

## 7. Coverage Targets

| Scope                                       | Metric        | Target               |
|---------------------------------------------|---------------|----------------------|
| `app/domain/` (color_band, geo_utils)       | Line + Branch | **100%**             |
| `app/services/`                             | Line          | **90%**              |
| `app/routers/`                              | Line          | 85%                  |
| Backend overall                             | Line          | **80%**              |
| `src/utils/` + `src/state/`                 | Line          | **100%**             |
| `src/components/`                           | Line          | 75%                  |
| Frontend overall                            | Line          | **75%**              |
| API BDD scenarios (Features 1–9)            | Passing in CI | **40/40** by Phase 5 |
| UCD 2011 task scenarios                     | Passing in CI | **9/9** by Phase 5   |
| UX design invariants                        | Passing in CI | **10/10** by Phase 5 |
| Mutation score — domain + formatter modules | Kill rate     | **≥ 85%**            |

---

## 8. Linked Test Plans

The detailed test scenarios, infrastructure setup, entry/exit criteria, and automation traceability matrices are in dedicated test plans. This strategy establishes *what* and *why*; the test plans establish *how*.

| Layer                         | Test Plan                                                                          | Primary Template                         |
|-------------------------------|------------------------------------------------------------------------------------|------------------------------------------|
| Layer 1 — Unit                | [TOXMAP_TEST_PLAN_LAYER1_UNIT.md](TOXMAP_TEST_PLAN_LAYER1_UNIT.md)                 | Side-Effect-Driven (simplified — no I/O) |
| Layer 2 — Component           | [TOXMAP_TEST_PLAN_LAYER2_COMPONENT.md](TOXMAP_TEST_PLAN_LAYER2_COMPONENT.md)       | Side-Effect-Driven (mocked I/O)          |
| Layer 3 — Integration         | [TOXMAP_TEST_PLAN_LAYER3_INTEGRATION.md](TOXMAP_TEST_PLAN_LAYER3_INTEGRATION.md)   | Side-Effect-Driven (real PostGIS)        |
| Layer 4 — API Contract        | [TOXMAP_TEST_PLAN_LAYER4_API_CONTRACT.md](TOXMAP_TEST_PLAN_LAYER4_API_CONTRACT.md) | Event-Consumer (HTTP as event stream)    |
| Layer 5 — E2E / UI Acceptance | [TOXMAP_TEST_PLAN_LAYER5_E2E.md](TOXMAP_TEST_PLAN_LAYER5_E2E.md)                   | Side-Effect-Driven (browser as output)   |

### Supporting Reference Documents

| Document                                                 | Purpose                                                                       |
|----------------------------------------------------------|-------------------------------------------------------------------------------|
| [TOXMAP_ACCEPTANCE_TESTS.md](TOXMAP_ACCEPTANCE_TESTS.md) | Full Gherkin BDD feature files — Features 1–9 (API) and E2E task scenarios    |
| [TOXMAP_TEST_SEED_DATA.md](TOXMAP_TEST_SEED_DATA.md)     | Deterministic SQL fixtures, seed reference table, known-good assertion values |
| [TOXMAP_API_CONTRACT.md](../api/TOXMAP_API_CONTRACT.md)  | OpenAPI 3.1 endpoint specifications, request/response schemas, SLAs           |
| [TEST_ID_REGISTRY.md](TEST_ID_REGISTRY.md)               | Canonical `data-testid` attribute registry for Playwright selectors           |
| [test-step-coverage.md](test-step-coverage.md)           | Gherkin step implementation status and phase delivery assignments             |

> **Deferred test plans (created in their respective phases):**
> - `TOXMAP_TEST_PLAN_SECURITY.md` — Phase 6 (rate limiting, error sanitization, CORS, security headers); corresponds to Roadmap story 6.4.4
> - `TOXMAP_TEST_PLAN_LAYER7_DUCKDB.md` — Phase 7 (DuckDB WASM hook component tests, production smoke); corresponds to Roadmap stories 7.1.1–7.1.8
> - `features/api/nuclear.feature`, `features/api/npri.feature`, `features/api/congressional_districts.feature` — Phase 4/5 (optional layer Gherkin stubs)

---

*Last updated: 2026-07-23 — TRI Data Audit remediation: R-12 added (unit_of_measure integrity); TOXMAP-Specific Testing Considerations expanded. Changes require a PR and maintainer review per [GOVERNANCE.md](../GOVERNANCE.md).*
