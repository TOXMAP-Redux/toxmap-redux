# Changelog

All notable changes to TOXMAP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Update policy:**
> - **AI agents** may add per-story entries to `[Unreleased]` during their work session (one entry per story shipped; follow the format below; use the commit type as the category). See `AGENTS.md §2`.
> - **Phase Manager** adds milestone-level summaries when a milestone (M0–M7) is declared.
> - **Human maintainers** promote `[Unreleased]` entries to a versioned release section at release time.

---

## [Unreleased]

### Added

<!-- Phase 4 — Superfund Browse (2026-07-28) [agent] -->
- `GET /api/v1/superfund/browse` — backend endpoint returning ALL Superfund sites
  without radius constraint (mirrors `/facilities/browse` pattern); enables always-on
  diamond layer (story 4.1.1, 2026-07-28) [agent]
- `api/superfund.ts` — added `fetchAllSuperfundBrowse()` API client function
  (story 4.1.1, 2026-07-28) [agent]

### Changed

<!-- Phase 4 — Superfund Browse (2026-07-28) [agent] -->
- `hooks/useSuperfundViewport.ts` — REWRITTEN: now fetches all ~1.7k sites ONCE
  via `/superfund/browse` on mount; removed bbox dependency; MapLibre handles
  viewport clipping; fixes issue where different zoom levels showed different
  subsets due to 500-mile radius cap (story 4.1.1, 2026-07-28) [agent]
- `App.tsx` — removed `mapBbox` param from `useSuperfundViewport()` call
  (story 4.1.1, 2026-07-28) [agent]
- Updated `docs/escalations/TRI_CLUSTERED_LAYER_HANDOFF.md` — renamed to "Map Layers
  Resolution Summary"; now covers both TRI and Superfund browse patterns
  (story 4.1.1, 2026-07-28) [agent]
- Updated protected files (`TOXMAP_API_CONTRACT.md`, `ADR-001`, `CONTEXT_SUMMARY.md`,
  `TOXMAP_DEVELOPMENT_ROADMAP.md`, `AGENTS.md`, `agents/frontend-engineer/prompt.md`)
  to document the Superfund browse endpoint pattern (story 4.1.1, 2026-07-28) [agent]

<!-- Phase 4 — Superfund Overlay (stories 4.1.x–4.3.x, 2026-07-28) [agent] -->
- `api/superfund.ts` — typed API client for `GET /api/v1/superfund` and
  `GET /api/v1/superfund/{epa_id}`; no `any` types (story 4.1.1, 2026-07-28) [agent]
- `api/types.ts` — `SuperfundProperties`, `SuperfundFeature`, `SuperfundCollection`,
  `SuperfundContaminant`, `SuperfundDetail` TypeScript types matching API contract
  (stories 4.1.1–4.2.3, 2026-07-28) [agent]
- `hooks/useSuperfundViewport.ts` — always-on Superfund viewport hook: fetches NPL
  sites in current bbox on every map move (story 4.1.1, 2026-07-28) [agent]
- `hooks/useSuperfundSearch.ts` — Superfund search results hook: active when
  `dataset=superfund` and user submits a search (story 4.1.3, 2026-07-28) [agent]
- `hooks/useSuperfundDetail.ts` — fetches full Superfund site detail by EPA ID
  for `SuperfundDrawer` (story 4.2.1, 2026-07-28) [agent]
- `MapContainer` — Superfund diamond markers as a separate, unclustered `symbol`
  layer (`superfund-sites`); SVG diamond sprite registered at map load
  (`superfund-diamond-filled` for NPL, `superfund-diamond-outline` for CERCLIS/Deleted);
  `onSuperfundSiteClick` handler; UX Invariant 6 enforced (story 4.1.1, 2026-07-28) [agent]
- `MapContentsPanel` — `data-testid="layer-toggle-superfund"` checkbox toggles
  diamond layer visibility; unified legend: TRI Release Tiers + Superfund diamond entry
  (stories 4.1.2, 4.3.1, 2026-07-28) [agent]
- `components/FacilityDetail/SuperfundDrawer.tsx` — full Superfund detail drawer:
  site name/EPA ID/address header, HRS score badge (red ≥50/amber 28–50/green <28;
  `data-testid="superfund-hrs-score"`), NPL date, contaminants list with ATSDR links
  (`data-testid="superfund-contaminants-list"`, `superfund-contaminant-link`), EPA
  Site Progress Profile link (`superfund-epa-progress-link`), close at bottom
  (`popup-close-bottom`); UX Invariant 9 (stories 4.2.1–4.2.3, 2026-07-28) [agent]
- `App.tsx` — wires Phase 4: `selectedSuperfundEpaId` state, `showSuperfundLayer`
  toggle, `handleSuperfundSiteClick`, `useSuperfundViewport`, `useSuperfundSearch`;
  `SuperfundDrawer` renders when a Superfund site is selected (stories 4.1–4.3, 2026-07-28) [agent]
- Updated `tests/features/e2e/ucd_task_scenarios.feature` — T-02 and T-04 are now
  fully implemented Gherkin scenarios (no longer `@skip`); Phase 5+ remain skipped
  (QA story 4.QA, 2026-07-28) [agent]
- Updated `tests/features/e2e/ux_invariants.feature` — Invariant 6 fully implemented;
  asserts `layer-toggle-superfund` and `superfund-detail-panel` open on Superfund result
  click (QA story 4.QA, 2026-07-28) [agent]
- Updated `tests/steps/e2e_steps.py` — Phase 4 step implementations: `select dataset`,
  `click superfund result`, `Superfund detail panel opens`, `contaminants list visible`,
  `contaminants list contains`, `EPA site progress link`, `Superfund layer toggle`,
  `TRI facility detail panel not shown`; stubs for Phase 5+ retained (QA, 2026-07-28) [agent]

### Changed
- `SearchPanel` — removed `dataset-radio-both` (deferred per screen catalog Fig 2015-4;
  only TRI/Superfund; `data-testid="dataset-radio-both"` removed from DOM);
  `SearchFormValues` now includes `dataset: 'tri' | 'superfund'`; dataset radio uses
  controlled `checked` state (story 4.1.3, 2026-07-28) [agent]
- `ResultsTable` — now accepts `mode: 'tri' | 'superfund'`, `triData`, `superfundData`
  props; Superfund mode renders site name, city+state, HRS score badge, status badge
  (`results-row-hrs`); TRI mode unchanged (story 4.1.3, 2026-07-28) [agent]
- `Sidebar` — threaded `superfundResults`, `showSuperfundLayer`, and
  `onToggleSuperfundLayer` props to `MapContentsPanel` and `SearchPanel`
  (stories 4.1.2, 4.1.3, 2026-07-28) [agent]
- `api/types.ts` — `SubmittedSearch` now includes `dataset: 'tri' | 'superfund'`
  (story 4.1.3, 2026-07-28) [agent]
- `tests/conftest.py` — strip `+psycopg2` SQLAlchemy driver prefix from
  `DATABASE_URL_SYNC` env var before passing to `psycopg2.connect()` (pre-existing
  issue surfaced by Phase 4 test run, 2026-07-28) [agent]

<!-- Phase 3 — Core Map UI (stories 3.1.x–3.6.x, 2026-07-27) [agent] -->
- Tailwind CSS + PostCSS setup (`tailwind.config.js`, `postcss.config.js`, `src/index.css`)
  for the React frontend; Vite-env type declarations in `vite-env.d.ts` (story 3.1.1, 2026-07-27) [agent]
- `MapContainer` component — full-viewport MapLibre GL JS map with OpenFreeMap Liberty basemap
  (`VITE_MAPLIBRE_STYLE`); GeoJSON Source with TRI facility circle markers color-coded by
  `color_band`; cluster aggregation via MapLibre `cluster=true`; `data-testid="map-container"`
  (stories 3.1.2, 3.3.1, 3.3.2, 2026-07-27) [agent]
- Typed API clients with zero `any`: `api/facilities.ts`, `api/chemicals.ts`, `api/meta.ts`,
  `api/geocode.ts`, `api/types.ts`; all 17 domain endpoints covered (story 3.1.3, 2026-07-27) [agent]
- `DataVintageLabel` — map footer component showing EPA TRI vintage from `GET /api/v1/meta`;
  `data-testid="data-vintage-label"`; UX Invariant 7 `(latest year)` label (story 3.1.5, 2026-07-27) [agent]
- `lib/duckdbCompat.ts` — two-mode seam (`resolveDataSource()`, `isDuckDBMode()`); dev mode
  active; DuckDB WASM hooks deferred to Phase 7 (story 3.1.3, 2026-07-27) [agent]
- `utils/formatLbs.ts` — `formatLbs(n)` and `formatNumber(n)` utilities enforcing comma
  formatting on all release quantities; UX Invariant 8 (all phases, 2026-07-27) [agent]
- `Sidebar` component — collapsible left panel with single-panel enforcement (UX Invariant 1);
  tabs for MapContentsPanel / SearchPanel; `data-testid="sidebar-panel"`,
  `data-testid="sidebar-collapse-btn"` (stories 3.2.1, 3.2.9, 2026-07-27) [agent]
- `MapContentsPanel` — TRI layer toggles; `(latest year)` label on most-recent year
  (`data-testid="year-toggle-latest"`); color-band legend (story 3.2.2, 2026-07-27) [agent]
- `SearchPanel` — labeled "Search Chemical Releases by Location" (UX Invariant 4); chemical
  autocomplete (`data-testid="chemical-input"`, `data-testid="chemical-autocomplete-option"`);
  ATSDR + PubChem links on selected chemical (`data-testid="atsdr-link"`, T-08); location
  geocode input; year dropdown; state dropdown + "Limit to state" checkbox (UX Invariant 3);
  dataset radio buttons (TRI/Superfund/Both); `data-testid="search-submit-btn"`
  (stories 3.2.3–3.2.7, 2026-07-27) [agent]
- `useViewportFacilities` hook — fetches `GET /api/v1/facilities` with bbox on map move;
  abort-controller cancels stale requests; UX Invariant 2 (story 3.2.8, 2026-07-27) [agent]
- `useChemicalAutocomplete` hook — 300ms debounced call to `GET /api/v1/chemicals/search?q=`
  (story 3.2.4, 2026-07-27) [agent]
- `useMeta`, `useFacilityDetail`, `useFacilityReleases` hooks (stories 3.1.5, 3.4.1, 3.4.3,
  2026-07-27) [agent]
- `ResultsTable` — viewport-scoped results table sorted by `total_release_lbs` DESC; UX
  Invariants 2 and 8; `data-testid="results-table"`, `data-testid="results-row"`,
  `data-testid="results-row-name"`, `data-testid="results-row-release"` (stories 3.5.1–3.5.3,
  2026-07-27) [agent]
- `FacilityPopup` — MapLibre GL JS popup on marker click; comma-formatted release amount;
  close link at bottom (`data-testid="popup-close-bottom"`); UX Invariant 9 (story 3.4.1–3.4.2,
  2026-07-27) [agent]
- `FacilityDrawer` — fixed right panel with 3-tab Recharts: top chemicals (BarChart), release
  by medium (BarChart), 15-year trend (LineChart); ATSDR + PubChem links; comma-formatted
  amounts; UX Invariants 8 and 9 (stories 3.4.3–3.4.5, 2026-07-27) [agent]
- `InterpretationBanner` — dismissable interpretation disclaimer (story 3.6.2, 2026-07-27) [agent]
- Updated `App.tsx` — wires all Phase 3 components; manages map viewport, search flow, facility
  selection, and sidebar panel state; replaces Phase 0 placeholder (stories 3.1.4, all epics,
  2026-07-27) [agent]
- `tests/steps/e2e_steps.py` — Phase 3 Playwright step implementations for T-01, T-03, T-08
  and UX invariants 1–4, 7–9; `@skip` hook auto-skips Phase 4+ stubs (QA stories, 2026-07-27) [agent]
- Updated `tests/features/e2e/ucd_task_scenarios.feature` — full Phase 3 Gherkin for T-01,
  T-03, T-08; Phase 4+ scenarios as `@skip` stubs (QA, 2026-07-27) [agent]
- Updated `tests/features/e2e/ux_invariants.feature` — full Phase 3 Gherkin for Invariants
  1–4, 7–9; Phase 4+ as `@skip` stubs (QA, 2026-07-27) [agent]
- Updated `.github/workflows/ci.yml` — E2E job now installs Playwright, runs both
  `ux_invariants.feature` and UCD task scenarios T-01/T-03/T-08 (OPS story 3.OPS, 2026-07-27) [agent]

### Changed
- `frontend/src/api/geocode.ts` — **switched geocoding from Nominatim backend proxy to Photon
  browser-direct** (ADR-006, 2026-07-27). Nominatim blocked server IP; Docker SSL inspection
  prevented container HTTPS. Photon (photon.komoot.io) is CORS-enabled, no API key, OSM-backed.
  Added 200-entry LRU cache, 1-second throttle, and attribution links [agent]
- `frontend/src/components/DataVintageLabel.tsx` — added Photon/OSM attribution (JSX `<a>` links,
  no `dangerouslySetInnerHTML`) in map footer per Photon fair-use policy (ADR-006, 2026-07-27) [agent]
- `frontend/src/hooks/useViewportFacilities.ts` — threaded `AbortSignal` through `fetchFacilities`
  to fix viewport bbox race condition (stale pre-zoom request overwrote correct results, 2026-07-27) [agent]
- `frontend/src/api/facilities.ts` — `fetchFacilities` now accepts optional `AbortSignal` (2026-07-27) [agent]
- `frontend/src/App.tsx` — `handleSearchSubmit` resets `mapBbox` to null before setting new
  `submittedSearch`, eliminating the stale-viewport-bbox race condition (2026-07-27) [agent]
- `frontend/.env.example` — `VITE_NOMINATIM_UA` commented out (geocoding no longer uses Nominatim
  or the backend proxy, 2026-07-27) [agent]
- `backend/app/routers/geocode.py` — switched backend geocode proxy from Nominatim to Photon
  (endpoint retained for CLI use but unused by frontend, 2026-07-27) [agent]

### Added
- `docs/adr/ADR-006-photon-geocoding.md` — Architecture Decision Record for Photon geocoding,
  browser-direct pattern, fair-use mitigations, and viewport bbox race condition fix (2026-07-27) [agent]

<!-- Phase 2 — Core API (Milestone M2, 2026-07-26) -->
- `GET /api/v1/facilities` — PostGIS `ST_DWithin` radius search with GIST index; full filter
  chain: `restrict_to_state`, `bbox`, `chemical`, `year`, `medium`, `naics`, `limit`
  (stories 2.1.1–2.1.4, 2026-07-26) [agent]
- `color_band` computed field on facility search results: `green` (0–999 lbs) / `yellow`
  (1,000–9,999) / `orange` (10,000–99,999) / `red` (≥ 100,000); virtual `marker_shape="circle"`
  added by serializer (story 2.1.5, 2026-07-26) [agent]
- `GET /api/v1/facilities/{tri_facility_id}` — full facility detail with `top_chemicals` list
  (up to 5 chemicals ranked by `total_release_lbs` DESC for the facility's latest year)
  (story 2.1.6, 2026-07-26) [agent]
- `GET /api/v1/facilities/{tri_facility_id}/releases` — 15-year time series sorted by
  `reporting_year` DESC; `from_year`/`to_year` params; all four medium fields always present
  (story 2.2.1, 2026-07-26) [agent]
- `GET /api/v1/releases/largest` — returns highest-release facility for a chemical, optionally
  restricted to state; T-07 verified: SC chlorine → 85,000 lbs; nationwide → 342,500 lbs
  (story 2.2.2, 2026-07-26) [agent]
- `GET /api/v1/chemicals` — full chemical list sorted alphabetically; `cas_number` is `null`
  for TRI compound categories (N-prefix IDs such as N420 for LEAD COMPOUNDS)
  (story 2.3.1, 2026-07-26) [agent]
- `GET /api/v1/chemicals/search?q=` — live autocomplete; case-insensitive ilike; max 10
  results; returns empty array (not 404) on no match; p95 < 100ms enforced via DB index
  (stories 2.3.2–2.3.3, 2026-07-26) [agent]
- `GET /api/v1/superfund` — GeoJSON FeatureCollection; `marker_shape="diamond"` on every
  feature; radius + state + chemical + status filters (story 2.4.1, 2026-07-26) [agent]
- `GET /api/v1/superfund/{epa_id}` — full Superfund site detail with typed contaminants list;
  T-04 verified: `VAD070358684` → AVTEX FIBERS INC → FRONT ROYAL, VA
  (story 2.4.2, 2026-07-26) [agent]
- `GET /api/v1/demographics/county` — county GeoJSON FeatureCollection with `meta.units`
  object for inline legend labels; VA → Warren County (FIPS 51187) verified
  (story 2.5.1, 2026-07-26) [agent]
- `GET /api/v1/demographics/tract` — census tract endpoint; returns county-level fallback
  (no tract table in current schema; tracked as known limitation)
  (story 2.5.2, 2026-07-26) [agent]
- `GET /api/v1/layers/nuclear` — US nuclear plant locations GeoJSON; `marker_shape="atom"`
  (story 2.6.1, 2026-07-26) [agent]
- `GET /api/v1/export/csv` — streaming CSV download via `StreamingResponse`; chunked transfer
  encoding; `Content-Disposition` filename encodes active chemical + year + date
  (story 2.6.2, 2026-07-26) [agent]
- `GET /api/v1/export/map-metadata` — returns `export_filename`, active query snapshot, and
  `generated_at` ISO timestamp for map image exports (story 2.6.3, 2026-07-26) [agent]
- FastAPI OpenAPI schema auto-generated at `/openapi.json`; all 17 domain paths confirmed;
  Swagger UI at `/docs` lists every endpoint (story 2.7.1, 2026-07-26) [agent]
- `GET /api/v1/meta` — dev-mode metadata endpoint returning `available_years`, `latest_year`,
  `vintage_label`, `total_facility_count`, `total_release_event_count`, `source: "fastapi-dev"`;
  returns 503 when `release_events` table is empty (story 2.7.3, 2026-07-26) [agent]
- pytest-bdd step implementations for all 7 API feature files (F1–F7): 18 Gherkin scenarios,
  18 passed; T-01 API (Sparrows Point lead compounds → `21219BTHLS3RD`, 12,485 lbs, orange)
  and T-03 API (Nevada copper → `89319BHPCP7MILE`, 8,205 lbs) verified
  (stories 2.QA.1–2.QA.3, 2026-07-26) [agent]

<!-- Phase 1 — Data Pipeline (Milestone M1, 2026-07-26) -->
- Alembic initial schema migration: `facilities`, `chemicals`, `release_events`,
  `superfund_sites`, `census_county`, `nuclear_plants`, `npri_facilities` tables with
  PostGIS GIST and B-tree indexes (stories 1.1.1–1.1.4, 2026-07-26) [agent]
- TRI CSV ingestion pipeline: `tri_parser.py` (`TRI_COLUMN_MAP`), `tri_ingest.py` CLI
  (`--year`), EPA EFService download, coordinate bounds filter, upsert to PostGIS
  (stories 1.2.1–1.2.6, 2026-07-26) [agent]
- Superfund / NPL ingestion: `superfund_ingest.py` → `superfund_sites` table with SSRF
  allow-list guard (stories 1.3.1–1.3.2, 2026-07-26) [agent]
- Census TIGER ingestion: `census_ingest.py` → `census_county` table with geopandas
  MULTIPOLYGON load (stories 1.4.1–1.4.3, 2026-07-26) [agent]
- Parquet build pipeline: `scripts/build_parquet.py` → `tri_2022.parquet` (3 MB, 75,224
  rows), `superfund.parquet`, `manifest.json` with `epa_vintage_label`
  (stories 1.5.1–1.5.4, 2026-07-26) [agent]
- `build-data.yml` upgraded from stub to real pipeline with PostGIS service container,
  TRI ingest, Parquet build, and R2 upload stub (story 1.5.2, 2026-07-26) [agent]

<!-- Phase 0 — Foundation (Milestone M0, 2026-07-25) -->
- `README.md` — full project landing page: backstory, quick-start, architecture, features, data
  sources, acceptance tests table, 8-phase roadmap, contributing guide, security section
  (story 0.1.1, 2026-07-21) [agent]
- Monorepo directory structure: `backend/`, `frontend/`, `scripts/`, `tests/`, `docs/` with
  placeholder files so git tracks directories (story 0.1.2, 2026-07-25) [agent]
- `.github/` templates: `pull_request_template.md`, `ISSUE_TEMPLATE/bug_report.yml`,
  `rfc.yml`, `agent-escalation.yml`, `CODEOWNERS` (story 0.1.3, 2026-07-25) [agent]
- `docker-compose.yml` with `postgres`, `backend`, `frontend` services; volume mounts for hot
  reload; `./tests/fixtures/seed.sql` auto-loaded via `docker-entrypoint-initdb.d/`
  (stories 0.2.1, 0.2.2, 0.2.5, 2026-07-25) [agent]
- `backend/Dockerfile` — Python 3.12, FastAPI, uvicorn; `GET /health → {"status":"ok"}`
  liveness probe (story 0.2.3, 2026-07-25) [agent]
- `frontend/Dockerfile` — Node 22, Vite dev server, React 18 + TypeScript scaffold; port 3000
  (story 0.2.4, 2026-07-25) [agent]
- `.github/workflows/ci.yml` — 5-gate CI pipeline: Python lint (`ruff`, `mypy`), unit tests,
  API contract tests (Gate 2), E2E / UX invariants (Gate 3), performance benchmarks (Gate 5)
  (story 0.3.1, 2026-07-25) [agent]
- `.github/workflows/build-data.yml` — stub pipeline with 3 EPA cron triggers (Aug 1, Oct 1,
  Apr 1) and `workflow_dispatch`; upgraded to real pipeline in story 1.5.2
  (story 0.3.2, 2026-07-25) [agent]
- Codecov upload step in `ci.yml` `python-unit` job; coverage token via `secrets.CODECOV_TOKEN`
  (story 0.3.3, 2026-07-25) [agent]
- `tests/conftest.py` — `db_connection` (session-scoped), `seed_db` (function-scoped
  TRUNCATE/reload), `api_client` (FastAPI `TestClient`), `browser_base_url`, `step_context`
  fixtures (story 0.4.1, 2026-07-25) [agent]
- `tests/fixtures/seed.sql` — 7 TRI facilities, 6 chemicals, 14 release events, 2 Superfund
  sites, 3 census counties; immutable UCD 2011 seed values (story 0.4.2, 2026-07-25) [agent]
- `pytest-playwright` and `pytest-bdd` configured in `backend/pyproject.toml`; `--base-url`,
  `--screenshot only-on-failure`, `bdd_features_base_dir` set; feature stub files created
  (stories 0.4.3, 0.4.4, 2026-07-25) [agent]
- `tests/features/api/` — 7 Gherkin feature stubs: `facility_search.feature`,
  `superfund.feature`, `chemicals.feature`, `demographics.feature`, `release_trends.feature`,
  `export.feature`, `metadata.feature` (stories 0.4.4 + V10-B fix, 2026-07-25) [agent]
- `tests/features/e2e/` — 2 Gherkin feature stubs: `ucd_task_scenarios.feature`,
  `ux_invariants.feature` (V10-B fix, 2026-07-25) [agent]
- `bandit.yaml` — SAST config at repo root; B101 skipped for test files; all other Medium+
  findings are hard CI failures (V10-F fix, 2026-07-25) [agent]

### Security

<!-- Phase 2 — Core API -->
- Pydantic `Query()` parameter validators: `lat` ∈ [−90, 90], `lon` ∈ [−180, 180],
  `radius_miles` ≤ 500, `state` sanitized to uppercase 2-char before DB use; `lat=999` → 422,
  `radius_miles=5000` → 422 verified (story 2.8.1, 2026-07-26) [agent]
- `slowapi` rate limiter at 60 requests/minute per IP (`get_remote_address`); request #61
  returns 429; `SlowAPIMiddleware` registered as outermost middleware layer
  (story 2.8.2, 2026-07-26) [agent]
- `SecurityHeadersMiddleware` (pure ASGI, not `BaseHTTPMiddleware`): injects
  `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`
  on every HTTP response (story 2.8.3, 2026-07-26) [agent]
- Global `Exception` handler: all unhandled errors return
  `{"detail": "Internal server error", "code": "INTERNAL_ERROR"}`; no tracebacks, no
  SQLAlchemy file paths, no internal structure exposed in 500 bodies; `bandit -r backend/app/`
  exits 0 (story 2.8.4, 2026-07-26) [agent]
- Schemathesis Gate 2 activated in `ci.yml`: `|| true` guard removed, `--checks all` enforced,
  `TESTING=1` env var set (triggers `NullPool` in `database.py` to prevent asyncpg
  cross-event-loop conflicts under pytest) (story 2.OPS.1, 2026-07-26) [agent]

<!-- Phase 1 — Data Pipeline -->
- All ingestion scripts (`tri_ingest.py`, `superfund_ingest.py`, `census_ingest.py`) audited
  for SSRF; `_validate_url()` allow-list guard confirmed on every `requests.get()` call; no
  f-string SQL patterns found (story 1.SEC.1, 2026-07-26) [agent]

<!-- Phase 0 — Foundation -->
- All third-party GitHub Actions in `ci.yml`, `security.yml`, `build-data.yml` pinned to full
  40-character commit SHAs; SHA → tag mapping documented in `docs/security/PINNED_ACTIONS.md`;
  zero mutable `@vX` tags remain (story 0.5.4, 2026-07-25) [agent]
- `.github/dependabot.yml` — automated dependency PRs for `pip`, `npm`, and `github-actions`;
  weekly schedule; `dependencies` + `security` labels (story 0.5.2, pre-existing) [agent]
- `.github/workflows/security.yml` — 4-job security pipeline: `gitleaks` secret scan,
  `pip-audit` CVE audit, `npm audit`, `bandit` SAST (story 0.5.3, pre-existing) [agent]

---

<!-- Releases are added above this line in reverse chronological order -->
<!-- Template:
## [X.Y.Z] - YYYY-MM-DD

### Added
- ...
-->

[Unreleased]: https://github.com/VictorCannestro/toxmap/compare/v0.0.0...HEAD
<!-- Update this line to the latest release tag when v0.1.0 is cut, e.g.: -->
<!-- [Unreleased]: https://github.com/VictorCannestro/toxmap/compare/v0.1.0...HEAD -->

