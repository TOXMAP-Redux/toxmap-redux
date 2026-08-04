# TOXMAP Design & Technical Assumptions

**Date:** 2026-07-17  
**Last Updated:** 2026-08-04 — Phase 6 audit: ADR-005/006/007/008 added; A-014/A-015/A-020 updated (Photon/OpenFreeMap); A-051–A-053 added; A-038/A-041 corrected; Summary Table revised  
**Scope:** Full project — data, architecture, infrastructure, UX, security, and testing  
**Sources Reviewed:** ADR-001, ADR-002, ADR-003, ADR-004, ADR-005, ADR-006, ADR-007, ADR-008,  
WASM_MEMORY_LIMIT_ASSESSMENT.md, TOXMAP_TECH_STACK_ANALYSIS.md, TWO_MODES_DEEP_DIVE.md,  
TECH_STACK_ONBOARDING.md, GOVERNANCE.md, AGENTS.md, TOXMAP_API_CONTRACT.md,  
TOXMAP_TESTING_STRATEGY.md, TOXMAP_TRI_DATA_AUDIT.md

> **Why this document exists:** Design transparency. Every non-trivial decision in this project
> rests on at least one unstated premise. Listing those premises up front lets contributors
> spot when a premise is wrong before the code is already built around it.

---

## Table of Contents

- [How to Read This Document](#how-to-read-this-document)
- [Highest-Risk Assumptions at a Glance](#highest-risk-assumptions-at-a-glance)
- [1. Data Source & Freshness Assumptions](#1-data-source--freshness-assumptions)
- [2. Architecture & Technology Assumptions](#2-architecture--technology-assumptions)
- [3. Hosting & Infrastructure Assumptions](#3-hosting--infrastructure-assumptions)
- [4. Browser Compatibility Assumptions](#4-browser-compatibility-assumptions)
- [5. UX & Product Assumptions](#5-ux--product-assumptions)
- [6. Performance Assumptions](#6-performance-assumptions)
- [7. Security Assumptions](#7-security-assumptions)
- [8. Build Pipeline & Data Pipeline Assumptions](#8-build-pipeline--data-pipeline-assumptions)
- [9. Testing Assumptions](#9-testing-assumptions)
- [10. Scope & Product Boundary Assumptions](#10-scope--product-boundary-assumptions)
- [Summary Table](#summary-table)

---

## How to Read This Document

Each assumption is assigned:

- **ID** — stable reference used in ADRs, RFCs, and PRs
- **Category** — the domain the assumption belongs to
- **Confidence** — how certain we are the assumption holds: `High` / `Medium` / `Low`
- **Risk if Wrong** — what breaks if the assumption turns out to be false
- **Source** — the ADR or document where this was established or first recorded

An assumption marked `Low` confidence is not necessarily wrong — it means we should validate it before the production launch phase that depends on it.

---

## Highest-Risk Assumptions at a Glance

Validate these before the corresponding feature ships — getting any of them wrong has outsized consequences.

| ID        | Assumption                                                           | When to Validate                         |
|-----------|----------------------------------------------------------------------|------------------------------------------|
| **A-013** | All state fits in a URL hash; no server session needed               | Before any feature requiring persistence |
| **A-028** | Co-occurrence disclaimer required on mortality tab only              | Before the demographics overlay ships    |
| **A-034** | No auth needed; fully public read-only                               | Before any write feature is considered   |
| **A-035** | R2 CORS `Range` header is required; omitting it silences Parquet queries | Before first production deploy       |
| **A-045** | All dependencies must be MIT/Apache 2.0 compatible                   | On every new dependency PR               |
| **A-048** | Dioxin releases are stored in grams; `unit_of_measure` column required | Before first dioxin facility ingest run |
| **A-051** | OpenFreeMap availability is a runtime dependency for basemap tiles   | Monitor for outages post-launch          |

---

## 1. Data Source & Freshness Assumptions

### A-001 · TRI data updates on a predictable batch schedule, not in real-time
**Confidence:** High  
**Source:** ADR-004 (Amendment note); TWO_MODES_DEEP_DIVE.md §The Real TRI Update Cadence  
**Detail:** Facilities submit revisions via EPA TRI-MEweb year-round, but the **public database refreshes follow known checkpoints**: July preliminary, multi-point Aug–Oct processing, October data freeze (authoritative), spring data refresh. Because updates arrive in batches at known intervals rather than continuously, a snapshot-based static architecture with periodic rebuilds is sufficient.  
**Risk if Wrong:** If EPA ever shifts to a continuous-update public API, the build-pipeline approach would produce stale data between rebuilds. The UI's vintage label mechanism is the primary mitigation.

---

### A-002 · The October data freeze is the authoritative TRI snapshot for a given reporting year
**Confidence:** High  
**Source:** ADR-004 §GitHub Actions Workflow; TWO_MODES_DEEP_DIVE.md  
**Detail:** The EPA freezes the TRI dataset in October for its National Analysis. This is the version used by official EPA tools (TRI Explorer). The July preliminary is raw and incomplete; the spring refresh applies retroactive corrections. The October freeze is therefore the correct primary source for production Parquet builds.  
**Risk if Wrong:** Building from the preliminary (July) understates releases. EPA's own measurement shows +9% waste management and +1.4% release quantities can differ between August preliminary and October freeze snapshots for the same reporting year.

---

### A-003 · Full TRI history (1987–present, ~4M rows) is ~150 MB compressed in Parquet
**Confidence:** Medium  
**Source:** ADR-004 §Option A; WASM_MEMORY_LIMIT_ASSESSMENT.md §Per-Year Parquet File Strategy  
**Detail:** Per-year average is ~4 MB/file; full history across ~38 years ≈ 150 MB using Snappy compression. This estimate drives the Cloudflare R2 storage plan (10 GB free tier) and the memory safety argument for DuckDB WASM.  
**Risk if Wrong:** If annual TRI submissions grow significantly (new reporting chemicals, expanded facilities), per-year file sizes increase. The R2 free tier (10 GB) can absorb ~25× growth before cost is incurred. Memory safety is unaffected at any realistic data scale given the wasm32 4 GB ceiling.

---

### A-004 · Each per-year query working set is 5–20 MB via HTTP range requests
**Confidence:** High  
**Source:** WASM_MEMORY_LIMIT_ASSESSMENT.md §Per-Year Parquet File Strategy  
**Detail:** DuckDB WASM fetches only the columns and row groups needed for a given query via HTTP `Range: bytes=N-M` headers. A filter on `chemical_name` and `total_release_lbs` does not download `address`, `zip_code`, or unrelated columns. Even full materialization of a single year's file (4 MB) would be 0.1% of the wasm32 2 GB default memory limit.  
**Risk if Wrong:** If queries are ever redesigned to join multiple years or load large demographics through DuckDB (rather than direct `fetch()`), working sets could grow to hundreds of MB. This is a future concern only; current query patterns are safe.

---

### A-005 · Superfund/NPL dataset is ~1,500 sites; NPRI is ~7,000 facilities; both are negligible in size
**Confidence:** High  
**Source:** ADR-001 §Data Model; TOXMAP_TECH_STACK_ANALYSIS.md §2.2 Data Sources  
**Detail:** Superfund `parquet` and `us_counties.geojson` are described as small files. The basemap tiles are served by OpenFreeMap (not loaded into DuckDB), so they do not contribute to the DuckDB memory budget.  
**Risk if Wrong:** If congressional district shapefiles (~60 MB uncompressed) or Census TIGER data are ever piped through DuckDB rather than served as static GeoJSON, the working set grows. Current design correctly routes these through direct `fetch()`.

---

### A-006 · TRI CSV column names are stable enough across years to use a single column map
**Confidence:** Medium  
**Source:** ADR-004 §build_data.py (`TRI_COLUMN_MAP`); TOXMAP_TRI_DATA_AUDIT.md (C-4, H-1, H-2)  
**Detail:** The ingestion script uses a dict (`TRI_COLUMN_MAP`) mapping raw EPA CSV headers to normalized field names. The TRI Data Audit (2026-07-23) confirmed three specific column-name failures in the original map, all now remediated:
1. **`"ON-SITE LAND RELEASES"` is not a documented TRI column header (C-4 — Critical):** Land release totals are now computed as the sum of whichever of TRI Fields 57–64 are present in a given year's CSV, rather than depending on a named aggregate that EPA may or may not include. The same computed-sum pattern is applied to air (Fields 51+52) and underground (Fields 55+56).
2. **`"ST"` vs. `"STATE"` (Field 8, H-1):** Both names are mapped as fallback aliases. Historical EPA downloadable CSVs use `"ST"`; the official documentation names the field `"STATE"`. Alias detection prevents silent state-code loss if EPA standardizes to the documented name.
3. **`"CAS #"` vs. `"CAS NUMBER"` (Field 40, H-2):** Both names are mapped as aliases for the same future-proofing reason.

The computed-aggregation approach for release medium totals is now the canonical ingestion pattern and is more robust than relying on any single named aggregate column that may not exist across all reporting years.  
**Risk if Wrong:** EPA periodically revises TRI submission forms and CSV exports. An undetected column rename silently drops data fields (e.g., `LATITUDE`, `LONGITUDE`) and produces Parquet files with missing coordinates, causing rows to be dropped by the `dropna(subset=["lat", "lon"])` filter without warning. The mitigations above address land, state, and CAS columns specifically; coordinate column mappings (`LATITUDE`, `LONGITUDE`) remain single-name and are the highest remaining exposure in the current map.

---

### A-007 · Coordinates in TRI CSV are plausible US-bounds values (lat –25–72, lon –180–-60)
**Confidence:** Medium  
**Source:** ADR-004 §`clean_tri_dataframe()` plausibility filter  
**Detail:** The ingestion pipeline filters out rows where lat/lon fall outside the defined bounding box for the continental US, Alaska, Hawaii, and US territories. Rows with invalid or out-of-bounds coordinates are silently dropped.  
**Risk if Wrong:** Facilities near territorial boundaries (Guam: lon ~145°E; US Virgin Islands: lon ~-65°W) may be clipped by the longitude bound of -60°W. Intentional; territorial coverage is a product decision, not a bug — but the assumption should be explicit.

---

### A-047 · `total_release_lbs` represents on-site releases only (TRI Field 65), not the full total including off-site transfers (Field 107)
**Confidence:** High  
**Source:** TOXMAP_TRI_DATA_AUDIT.md (C-1); ADR-001 §Data Model; UCD 2011 usability study task scenarios  
**Detail:** TRI Field 65 (`ON-SITE RELEASE TOTAL`) sums air + water + land + underground injection releases from the reporting facility itself. TRI Field 107 (`TOTAL RELEASES`) adds off-site transfers (POTWs, RCRA landfills, injection wells managed by receiving facilities) on top of that. The original TOXMAP and every UCD 2011 task scenario exclusively reference on-site medium breakdowns — the four columns that sum to Field 65. The `TRI_COLUMN_MAP` therefore maps `"ON-SITE RELEASE TOTAL"` → `total_release_lbs` (Field 65). The `off_site_lbs` column captures Field 88 (`OFF-SITE RELEASE TOTAL`) separately but is not surfaced in the primary map UI. Field 107 is retained in the map as `total_release_lbs_field107` for informational purposes only.  
**Risk if Wrong:** Using Field 107 for `total_release_lbs` would inflate values for any facility with off-site transfers, trigger higher color-band assignments than the on-site footprint warrants, and break the arithmetic invariant `total_release_lbs = air + water + land + underground`. All color-band thresholds, CSV exports, and seed-data assertions (T-01, T-03) assume on-site totals exclusively.

---

### A-048 · Dioxin and dioxin-like compound releases are stored in grams; the `unit_of_measure` column is required to prevent a ~453× magnitude display error
**Confidence:** High  
**Source:** TOXMAP_TRI_DATA_AUDIT.md (C-2); EPA TRI Basic Data Files Documentation (Field 50, `UNIT OF MEASURE`)  
**Detail:** TRI Field 50 (`UNIT OF MEASURE`) distinguishes pounds (all non-dioxin chemicals) from grams (17 dioxin/dioxin-like congeners, classification `N150`). The `_lbs` column suffix on `total_release_lbs`, `air_release_lbs`, etc. is a historical naming convention that is correct only for non-dioxin chemicals. The `release_events` DDL now includes `unit_of_measure VARCHAR(6) DEFAULT 'Pounds'`, and `"UNIT OF MEASURE"` is mapped in `TRI_COLUMN_MAP`. The API response includes a `meta.units` field; the frontend **must** read this before formatting release quantities for display. A dioxin quantity displayed as if it were pounds would appear ~453× smaller than the actual reported gram value.  
**Risk if Wrong:** Dioxin facility release values would be displayed hundreds of times smaller than the EPA-reported figures, misleading public-health researchers and journalists. The `color_band` logic would assign green or yellow to facilities with significant dioxin releases. This is the highest per-record data-accuracy risk for any ingest run that includes dioxin facilities.

---

### A-049 · TRI compound categories (N-prefix IDs) do not have CAS numbers; `chemicals.cas_number` is nullable with a partial unique index
**Confidence:** High  
**Source:** TOXMAP_TRI_DATA_AUDIT.md (C-3, M-4); EPA TRI Appendix A (Category 1 Metals)  
**Detail:** Approximately 40 TRI chemical categories use EPA N-prefix identifiers (e.g., `N420` = Lead Compounds, `N010` = Antimony Compounds, `N100` = Copper Compounds) rather than CAS numbers assigned by the Chemical Abstracts Service. The original DDL constraint `cas_number VARCHAR(12) NOT NULL UNIQUE` was incompatible with compound categories and has been replaced with a partial unique index: `CREATE UNIQUE INDEX idx_chemicals_cas_number ON chemicals (cas_number) WHERE cas_number IS NOT NULL`. The T-01 seed scenario (Bethlehem Steel) uses LEAD COMPOUNDS (`N420`, `cas_number = NULL`) — not elemental LEAD (`CAS 7439-92-1`), which is a distinct TRI chemical entry with a separate reporting line.  
**Risk if Wrong:** Compound category records cannot be inserted into the `chemicals` table, silently excluding any TRI-reporting facility that uses an N-prefix chemical identifier. For metals reporting specifically (lead, arsenic, cadmium, chromium, nickel, zinc, etc.), N-prefix compound categories are the most common reporting form — their exclusion would drop a large fraction of industrial facility release records from the application entirely.

---

## 2. Architecture & Technology Assumptions

### A-008 · DuckDB WASM spatial extension covers all required PostGIS query patterns
**Confidence:** High  
**Source:** ADR-004 §DuckDB WASM Spatial Query Example; TWO_MODES_DEEP_DIVE.md §Mental Model 3  
**Detail:** Every spatial function used in the application — `ST_DWithin`, `ST_Distance`, `ST_Point`, `ST_GeomFromText`, `ST_Transform` — exists in both PostGIS and DuckDB's spatial extension with identical semantics for this query set. `ST_ClusterDBSCAN` (not needed — MapLibre GL handles clustering client-side) is the only material PostGIS function not available in DuckDB WASM.  
**Risk if Wrong:** If a future feature requires a PostGIS function not in DuckDB's spatial extension, the production code path would need to fall back to Option B (Fly.io + FastAPI). The spatial extension's coverage should be verified per the planned query set for each new feature.

---

### A-009 · MapLibre GL JS handles client-side marker clustering (ST_ClusterDBSCAN is not needed server-side)
**Confidence:** High  
**Source:** ADR-004 §Option E — H2 Spatial comparison table; TOXMAP_TECH_STACK_ANALYSIS.md §5.3  
**Detail:** MapLibre GL's built-in clustering (`GeoJSONSource` with `cluster: true`) replaces the server-side DBSCAN clustering the original TOXMAP used. This was an explicit design decision to keep clustering in the rendering layer, which enables it to be dynamic (changes with zoom level) at no server cost.  
**Risk if Wrong:** MapLibre GL clustering is visual only — it doesn't aggregate release quantities across clustered facilities for display. If a requirement emerges for "total releases within this cluster" to be shown on the cluster bubble, a DuckDB aggregate query or bounding-box API query would need to be added.

---

### A-010 · FastAPI (ADR-001) is the only viable backend choice for Option B at zero budget
**Confidence:** High  
**Source:** ADR-004 §Option B (warning block); ADR-002 §Zero-Budget Hosting Compatibility  
**Detail:** Spring Boot's JVM baseline is ~280 MB at idle, which exceeds Fly.io's free VM limit of 256 MB before a single request is handled. GraalVM native compilation can reduce this to ~90 MB but requires significant Hibernate Spatial reflection configuration work. ADR-002 documents this in full.  
**Risk if Wrong:** If GraalVM native + Hibernate Spatial is ever fully configured, a Spring Modulith Option B becomes viable. This does not change the recommended primary stack (ADR-001) but expands the Java team's options.

---

### A-011 · React component layer and MapLibre GL rendering are fully data-source-agnostic
**Confidence:** High  
**Source:** TWO_MODES_DEEP_DIVE.md §Part 7 — What's the Same in Both Modes  
**Detail:** The React UI, MapLibre GL rendering logic, Recharts charts, Tailwind styles, URL hash routing, and all UX behavior are designed to be identical in dev mode (FastAPI) and production mode (DuckDB WASM). The only code that changes between modes is inside `frontend/src/api/*.ts` and `duckdbCompat.ts`.  
**Risk if Wrong:** If a feature requires capabilities only available through the FastAPI path (e.g., server-side sessions, write operations, real-time WebSocket events), the React layer must be modified to conditionally handle it — breaking the clean seam.

---

### A-012 · The VITE_DATA_SOURCE environment variable is sufficient to switch modes at build time
**Confidence:** High  
**Source:** ADR-004 §Browser Compatibility Check; TWO_MODES_DEEP_DIVE.md §Part 5  
**Detail:** `VITE_DATA_SOURCE` is baked into the JavaScript bundle at Vite build time. Setting it to `api` produces a bundle with no DuckDB WASM binary; setting it to `duckdb` produces a bundle with no FastAPI fetch paths. The build-time split means neither mode's code ships to users of the other mode.  
**Risk if Wrong:** None under the current design. Would become a limitation if runtime feature flags (not build-time) were required (e.g., A/B testing the two backends with the same bundle).

---

### A-013 · All URL state can be encoded in a URL hash fragment (no server-side session required)
**Confidence:** High  
**Source:** ADR-001 §URL Routing / Deep Link Scheme (H-7)  
**Detail:** The application is fully stateless on the server side. All shareable state (map center, zoom, active filters, selected chemical, year, dataset) is encoded in the URL hash (`/#/map?lat=...`). This is a precondition for Cloudflare Pages static hosting, which cannot persist server-side sessions.  
**Risk if Wrong:** If a future feature requires per-user persistent state (saved searches, favorites, user-contributed data), a backend and authentication layer must be introduced. This would be a significant architectural change, not a minor addition.

---

### A-014 · Address geocoding via Photon (Komoot) is sufficient for location search
**Confidence:** High  
**Source:** ADR-006 §Decision (supersedes ADR-001 §Geocoding Specification)  
**Detail:** Address-to-coordinate conversion uses the Photon geocoder (photon.komoot.io) operated by Komoot GmbH. Photon is called directly from the browser with full CORS support. It requires no API key, has no registration requirement, and is backed by OpenStreetMap data. The frontend `geocode.ts` module implements an in-memory LRU cache (max 200 entries) and a 1-second throttle between distinct requests. A scoring algorithm (ADR-008) ranks candidates by address component match, and viewport proximity bias favors nearby results.  
**Risk if Wrong:** Photon's coverage for rural US addresses and industrial facility addresses depends on OSM data quality. The geocoding confidence scoring (A-052) mitigates this by flagging low-confidence results in the UI. If Komoot ever discontinues the service, a self-hosted Photon instance or switch to the US Census TIGER geocoder would be required.

---

### A-015 · Photon's fair-use guidelines are satisfied with cache + 1-second throttle
**Confidence:** High  
**Source:** ADR-006 §Fair-Use Status; `frontend/src/api/geocode.ts`  
**Detail:** Photon does not publish a strict rate limit, but the OpenStreetMap ecosystem convention is 1 request/second. The `geocode.ts` module enforces ≥1,000ms between distinct HTTP requests and caches up to 200 results in memory. Geocoding is triggered only on explicit Search button click (not on every keystroke), so the throttle rarely introduces perceptible latency. Attribution text linking to Photon/Komoot and OpenStreetMap is rendered in the map footer.  
**Risk if Wrong:** If TOXMAP is embedded in a high-traffic page or called programmatically without the frontend safeguards, Photon could block the origin. Self-hosting a Photon instance would eliminate this dependency but adds operational complexity.

---

### A-052 · Geocoding confidence scoring distinguishes high-fidelity from approximate matches
**Confidence:** High  
**Source:** ADR-008 §Scoring Algorithm; `frontend/src/api/geocode.ts`  
**Detail:** The Photon client requests 5 candidates and scores each against the original query using weighted signals: house number match (+0.35), street name similarity (+0.25), city match (+0.10), state match (+0.10), postal code match (+0.10), and viewport proximity (+0.10). Results are classified as `exact` (≥0.85), `high` (0.65–0.84), `approximate` (0.40–0.64), or `low` (<0.40). The UI displays a confidence badge and warning text for approximate/low results. Viewport bias passes the current map center (`lat`/`lon`) to Photon to favor nearby matches for ambiguous queries.  
**Risk if Wrong:** If the scoring weights are miscalibrated, users may see incorrect confidence badges (e.g., "exact" for an interpolated street-level match). The mitigations are: (1) conservative thresholds, (2) always showing the resolved canonical address so users can visually verify.

---

## 3. Hosting & Infrastructure Assumptions

### A-016 · Cloudflare R2 free tier (10 GB storage, 10M reads/month) is sufficient for Parquet data
**Confidence:** High  
**Source:** ADR-004 §Free Services Used; ADR-005 (amendment — basemap tiles no longer on R2)  
**Detail:** Full TRI Parquet history is ~150 MB; Superfund Parquet is <5 MB; all other static files are small. Total storage is well under 500 MB — roughly 5% of the 10 GB free allowance. With ADR-005, the basemap tiles are served by OpenFreeMap (not R2), so the original ~600 MB PMTiles estimate no longer applies. 10M reads/month at the per-year query pattern (one R2 read = 5–20 MB range request) allows ~500K–2M queries/month on the free tier.  
**Risk if Wrong:** A viral event (heavy press coverage) could spike reads beyond 10M/month. Cloudflare R2 charges $0.015/GB for egress beyond the free tier — not a budget crisis, but not zero either. A cost cap alert on the R2 bucket is recommended before production launch.

---

### A-017 · Cloudflare Pages handles all frontend hosting at zero cost with no traffic limits
**Confidence:** High  
**Source:** ADR-004 §Free Services Used  
**Detail:** Cloudflare Pages offers unlimited requests and unlimited bandwidth on the free tier with no expiry conditions. The React app bundle is ~2 MB and changes only when a new build is deployed.  
**Risk if Wrong:** Cloudflare's pricing terms could change. As a mitigation, the build is a standard `npm run build` output — deployable to any static CDN (GitHub Pages, Netlify, Vercel) without code changes.

---

### A-018 · GitHub Actions free tier (2,000 min/month) is sufficient for 3 annual data builds
**Confidence:** High  
**Source:** ADR-004 §GitHub Actions Workflow  
**Detail:** Each Parquet build run processes ~4M TRI rows with `pandas` + `pyarrow`. On a `ubuntu-latest` runner, this is estimated at 15–30 minutes per run. Three annual triggers × 30 min = 90 minutes/year — well within the 2,000-minute monthly free tier.  
**Risk if Wrong:** If the pipeline is triggered frequently via `workflow_dispatch` (e.g., during development testing), minutes accumulate faster. The pipeline should have a cost guard: only rebuild years that have changed, not all 38 years on every trigger.

---

### A-019 · Fly.io + Supabase (Option B) can serve the API within free-tier memory and storage limits
**Confidence:** Medium  
**Source:** ADR-004 §Option B; TWO_MODES_DEEP_DIVE.md §Mode 3  
**Detail:** Fly.io's free VM has 256 MB RAM — sufficient for FastAPI + uvicorn workers handling geospatial queries, but tight under concurrent load. Supabase free tier has 500 MB storage — sufficient for ~20 years of TRI data (not full history). Supabase pauses after 1 week of inactivity.  
**Risk if Wrong:** Option B is not the primary deployment target; it is an optional fallback for features requiring a live backend. However, if Option A's DuckDB WASM fallback (for SIMD-unsupported browsers) points to an Option B endpoint that is paused, unsupported-browser users see an error rather than data.

---

### A-020 · The basemap is served by OpenFreeMap and consumed exclusively by MapLibre GL
**Confidence:** High  
**Source:** ADR-005 §Decision (supersedes ADR-004 §Option A PMTiles assumption)  
**Detail:** The original ADR-004 assumed a self-hosted Protomaps PMTiles file (~600 MB for US) on Cloudflare R2. ADR-005 documented that the actual US extract is 2–5 GiB (127 GiB for the full planet build), Wrangler CLI has a 300 MiB upload limit, and the upload/refresh pipeline added significant operational complexity. The decision was to switch to OpenFreeMap (openfreemap.org), a free hosted vector tile service backed by OSM data. MapLibre GL JS streams tiles on demand from OpenFreeMap's CDN using the "Liberty" style. No PMTiles file is self-hosted; no R2 storage is consumed by basemap data.  
**Risk if Wrong:** OpenFreeMap is a third-party service with no SLA. If Tilen Mrak (operator) discontinues the service, the fallback is to self-host a Protomaps extract (scripts/upload_r2.py exists for this purpose) or switch to another tile provider. The basemap is visual-only — its unavailability does not affect data queries or facility markers.

---

### A-051 · OpenFreeMap availability is a runtime dependency; outages degrade UX but not data access
**Confidence:** High  
**Source:** ADR-005 §Risk Analysis  
**Detail:** Unlike the Parquet data files (which can be cached in the browser and served from R2), the basemap tiles are streamed on demand from OpenFreeMap's CDN. If OpenFreeMap experiences an outage, users see a blank or partially-loaded basemap but facility markers and data queries continue to work. The fallback `scripts/upload_r2.py` script exists to self-host a PMTiles extract if a long-term outage occurs, but this requires manual intervention and R2 storage provisioning.  
**Risk if Wrong:** If OpenFreeMap becomes permanently unavailable without warning, there is no automatic fallback. A status check or tile-load error handler could detect the failure and display a degraded-UX warning, but this is not currently implemented.

---

## 4. Browser Compatibility Assumptions

### A-021 · Chrome 91+ / Firefox 90+ / Safari 16.4+ cover the vast majority of the target user base
**Confidence:** High  
**Source:** ADR-004 §DuckDB WASM Browser Compatibility Check; WASM_MEMORY_LIMIT_ASSESSMENT.md §Browser Compatibility  
**Detail:** DuckDB WASM's spatial extension requires WebAssembly SIMD, which is supported in Chrome 91+ (May 2021), Firefox 90+ (July 2021), Safari 16.4+ (March 2023), and Chrome Android 91+. Safari iOS 15.x has partial support; Safari iOS <15 has none. The SIMD check (`isDuckDBWasmSupported()`) gates access automatically.  
**Risk if Wrong:** If a significant portion of the target audience (e.g., government employees on locked-down IE11 or legacy Edge) uses an unsupported browser, those users see the API fallback path — which requires Option B to be live. Without Option B, those users see no data.

---

### A-022 · Chrome 91+ implicitly guarantees 4 GB WASM memory support (coincidental, but correct)
**Confidence:** High  
**Source:** WASM_MEMORY_LIMIT_ASSESSMENT.md §Browser Compatibility Check  
**Detail:** The Chrome M83 V8 TypedArray rewrite that enables 4 GB WASM memory was released May 2020. Chrome 91 (required by DuckDB WASM SIMD) was released May 2021 — one year later. Every browser in the DuckDB WASM support matrix therefore already has 4 GB WASM memory support. The SIMD check coincidentally enforces a stricter baseline than the memory limit alone requires.  
**Risk if Wrong:** No violation possible. This is a confirmed fact; the gap is only a documentation one (the browser compatibility matrix doesn't explain this relationship).

---

### A-023 · DuckDB WASM's memory defaults are safe without explicit `maximumMemory` configuration
**Confidence:** Medium  
**Source:** WASM_MEMORY_LIMIT_ASSESSMENT.md §DuckDB Init: Missing Memory Configuration  
**Detail:** The documented DuckDB initialization does not set an explicit `maximumMemory` budget. For TOXMAP's current 5–20 MB query working sets this is safe — the margin to the wasm32 4 GB ceiling is three orders of magnitude. The omission is a documentation gap, not a current correctness issue.  
**Risk if Wrong:** Becomes a real concern if future features add multi-year aggregate queries (e.g., trend analysis across 14 years simultaneously), large in-browser joins, or loading demographics data through DuckDB rather than direct `fetch()`. Mitigated by adding an explicit `maximumMemory` cap to `duckdb.open()`.

---

### A-024 · WASM OOM errors are not a realistic risk under current query patterns
**Confidence:** High  
**Source:** WASM_MEMORY_LIMIT_ASSESSMENT.md §OOM Error Handling  
**Detail:** Per-query working sets are 5–20 MB. A mid-range Android device with 3 GB total RAM and 2 GB consumed by OS + browser still has ~1 GB headroom — 50–200× the working set size. A DuckDB WASM OOM error under current patterns would require an extreme environment (heavy tab load + very low RAM device + large query).  
**Risk if Wrong:** The existing `resolveDataSource()` fallback only handles SIMD availability, not OOM errors. An OOM exception would surface as an unhandled query failure rather than a graceful fallback. A `try/catch` OOM wrapper around DuckDB queries is a recommended low-severity improvement.

---

## 5. UX & Product Assumptions

### A-025 · The 2011 UCD Inc. usability study findings are still valid for the current target audience
**Confidence:** Medium  
**Source:** ADR-001 §UX Architecture Decisions; TOXMAP_TECH_STACK_ANALYSIS.md §8  
**Detail:** The study used 15 participants (4 concerned citizens, 11 professionals including toxicologists, public health researchers) in 2011. The critical findings — dual-panel confusion, empty table rows, state filter behavior, panel label confusion — are treated as **non-negotiable frontend constraints**. The assumption is that these findings reflect durable cognitive patterns, not era-specific UI conventions.  
**Risk if Wrong:** 15 participants is a small sample. If the 2026 target audience (more mobile users, different GIS familiarity curve) has meaningfully different mental models, some UCD 2011 constraints may be suboptimal. A new lightweight usability test at MVP stage is advisable to validate the most critical decisions (single sidebar, viewport-scoped table).

---

### A-026 · Viewport-scoped search results (re-fetched on map move) are preferable to paged country-wide results
**Confidence:** High  
**Source:** ADR-001 §UX Architecture Decisions (F-09); TOXMAP_TECH_STACK_ANALYSIS.md §8.1  
**Detail:** The 2011 UCD study identified 500-row paged tables with mostly empty rows as the most confusing element in the entire study. The design decision is to show only facilities within the current map viewport, re-fetching as the user pans and zooms.  
**Risk if Wrong:** Re-fetching on every map move increases DuckDB WASM query frequency. With the per-query 5–20 MB range request pattern, rapid panning can generate multiple overlapping requests. A debounce on map move events (300–500ms) is required to avoid request storms.

---

### A-027 · A single collapsible sidebar (never dual panels) resolves the panel confusion finding
**Confidence:** High  
**Source:** ADR-001 §UX Architecture Decisions (F-08); TOXMAP_TECH_STACK_ANALYSIS.md §8.1  
**Detail:** The original TOXMAP showed "Map Contents" and "Search Results" simultaneously. Users interacted with the wrong panel. The clone uses a single sidebar that shows only one context at a time: either the search panel or the map contents panel, never both.  
**Risk if Wrong:** The single-panel constraint limits information density. Power users performing complex tasks (comparing multiple chemical layers while viewing a search result) may find it restrictive. The design accepts this tradeoff explicitly in favor of reducing confusion for first-time users.

---

### A-028 · Co-occurrence of TRI releases and demographic data does not imply causation; disclaimer required on mortality tab only
**Confidence:** High  
**Source:** ADR-001 §UX Architecture Decisions; TOXMAP_TECH_STACK_ANALYSIS.md §8.2 (F-15); NLM source articles  
**Detail:** Both the NLM source articles and the 2011 usability study require a causation disclaimer when mortality/health overlays are displayed alongside release data. The study found the disclaimer was previously shown on all demographic tabs, which was incorrect — it is only relevant for mortality data, not income, age, or population layers.  
**Risk if Wrong:** Showing the disclaimer too broadly (all tabs) dilutes its impact. Not showing it at all on the mortality tab exposes the project to reputational and legal risk. This is a non-negotiable content requirement.

---

### A-029 · Geocoding requests transmit user addresses to a third-party service (Photon)
**Confidence:** High  
**Source:** ADR-006 §Privacy; `frontend/src/api/geocode.ts`  
**Detail:** In both dev and production modes, user-typed addresses are sent to `photon.komoot.io`. The frontend calls Photon directly (browser-to-service). Komoot GmbH operates the service; their privacy policy applies to geocoding queries. There is no TOXMAP backend intermediary to log address queries.  
**Risk if Wrong:** Users in privacy-sensitive contexts (e.g., entering a home address to check nearby facilities) may be uncomfortable with their address being transmitted to a third-party service. A privacy disclosure in the UI near the location search field is recommended.

---

## 6. Performance Assumptions

### A-030 · PostGIS ST_DWithin with GIST index on ~90K TRI facilities returns results in <50ms
**Confidence:** High  
**Source:** ADR-001 §Positive Consequences; API contract performance SLAs  
**Detail:** The `facilities.location` column has a GIST spatial index. `ST_DWithin` with a GIST index on ~90K points (approximate number of active TRI facilities) is a well-benchmarked query pattern. The architecture review confirms <50ms is achievable.  
**Risk if Wrong:** Performance degrades if the table grows significantly (facilities from all historical years in one table vs. per-year sharding) or if concurrent queries on Fly.io's single 256 MB free VM contend for CPU. The review checklist in ADR-001 requires a benchmark before accepting the ADR.

---

### A-031 · DuckDB WASM cold start of ~1–2 seconds is acceptable UX for the first query per session
**Confidence:** Medium  
**Source:** ADR-004 §Tradeoffs; TWO_MODES_DEEP_DIVE.md §Mode 2  
**Detail:** DuckDB WASM requires downloading a ~5 MB binary on first load, then initializing the WASM module and loading the spatial extension. This takes 1–2 seconds on a typical connection. After first load, the binary is browser-cached and subsequent queries start in milliseconds.  
**Risk if Wrong:** On slow mobile connections (3G, rural broadband), the 5 MB WASM binary download could take 5–10 seconds. A loading indicator is required. If perceived startup latency is rejected in user testing, a pre-warming approach (load DuckDB WASM in a service worker during initial page load, before the user triggers a search) would eliminate the perceived delay.

---

### A-032 · Chemical auto-complete returns results in <100ms
**Confidence:** High  
**Source:** ADR-001 §Review Checklist  
**Detail:** The chemicals table (~700 unique chemicals in the TRI dataset) is a small lookup. In dev mode, a PostgreSQL `ILIKE` query on an indexed column returns in <5ms. In production, DuckDB WASM queries the `chemicals.parquet` file (small, likely cached after first use) for `name ILIKE '%q%'`. The 100ms target is conservative.  
**Risk if Wrong:** None significant. If ILIKE on a small dataset somehow runs slow, a prefix index or pre-loaded in-memory array (all chemical names ~30 KB) can replace the query entirely.

---

### A-033 · Viewport-scoped facility re-fetch takes <200ms on map move
**Confidence:** Medium  
**Source:** ADR-001 §Review Checklist  
**Detail:** This is a tighter SLA than the general <500ms p95. In dev mode (FastAPI + PostGIS), this is achievable. In production mode (DuckDB WASM + Parquet range requests), the first move after cold start fetches 5–20 MB — this may exceed 200ms on slower connections. Subsequent moves within the same year's data are served from the DuckDB Parquet cache.  
**Risk if Wrong:** Map panning would feel sluggish on the first move after page load if range requests are not cached. The Parquet cache invalidation policy (how long DuckDB WASM caches fetched byte ranges) needs to be verified against the DuckDB WASM API.

---

## 7. Security Assumptions

### A-034 · No authentication or authorization is required; the application is fully public read-only
**Confidence:** High  
**Source:** TOXMAP_TECH_STACK_ANALYSIS.md §4 (NF-04); ADR-001 Context  
**Detail:** TRI data is a US government public dataset. The application is an open-source read-only viewer. No user accounts, no write operations, no private data. In Option A (production), there is no backend server at all — the attack surface is limited to the React bundle and Cloudflare R2 CORS headers.  
**Risk if Wrong:** If the project ever adds user-contributed data, facility comments, saved searches, or any write operation, authentication and authorization must be introduced before that feature ships. This would be a significant architectural addition.

---

### A-035 · Cloudflare R2 CORS must allow Range requests; omitting this silently breaks all production queries
**Confidence:** High  
**Source:** ADR-004 §Cloudflare R2 CORS Configuration; TWO_MODES_DEEP_DIVE.md §CORS Configuration  
**Detail:** The `Range` header must be in `AllowedHeaders` on the R2 CORS policy. Without it, browsers refuse to send range requests, DuckDB WASM cannot fetch partial Parquet files, and every production query returns nothing — with no error message visible to end users. This is the most common production deployment failure mode.  
**Risk if Wrong:** Full production data loss, silent. The mitigation is a smoke test in the GitHub Actions deploy workflow that verifies a DuckDB query returns results after every deployment.

---

### A-036 · Input validation in production mode (Option A) is fully the responsibility of the React layer
**Confidence:** High  
**Source:** ADR-004 §Negative Consequences; TWO_MODES_DEEP_DIVE.md §Mental Model 4  
**Detail:** In dev mode, FastAPI validates query parameters via Pydantic type annotations. In production mode, there is no server — DuckDB SQL query strings are constructed in `frontend/src/api/*.ts`. SQL injection into DuckDB WASM queries (parameterized via `$variable` syntax) is mitigated by DuckDB's prepared statement model, but all type coercion and bounds checking is the frontend's responsibility.  
**Risk if Wrong:** Malformed parameters (e.g., an invalid year like `2099` or a non-numeric radius) would generate DuckDB errors rather than a user-friendly validation message. All API client functions must validate inputs before building DuckDB queries.

---

## 8. Build Pipeline & Data Pipeline Assumptions

### A-037 · The Python ingestion pipeline (pandas + geopandas + pyarrow) is the canonical data build tool regardless of deployment mode
**Confidence:** High  
**Source:** ADR-001 §Consequences; ADR-004 §Option A; TWO_MODES_DEEP_DIVE.md §Part 6  
**Detail:** Even in Option A (no FastAPI, no PostgreSQL), the ingestion pipeline still runs in Python. It reads EPA TRI CSV, normalizes columns, filters invalid coordinates, and writes Parquet files. There is no "Java-only" or "TypeScript-only" path to data ingestion — any team working on this project needs Python available for data builds.  
**Risk if Wrong:** A purely Java team attempting to bypass the Python pipeline would need to rewrite `build_data.py` in Java. This is possible (Apache Arrow Java can write Parquet) but would duplicate the column mapping, coordinate validation, and vintage metadata logic. The risk is dual-maintenance drift between two ingestion implementations.

---

### A-038 · Parquet files must carry vintage metadata (.meta.json sidecar); omitting it is a data integrity issue
**Confidence:** High  
**Source:** ADR-004 §Build Pipeline (Amendment Note); TWO_MODES_DEEP_DIVE.md §Data Vintage Metadata; TOXMAP_TRI_DATA_AUDIT.md (L-3)  
**Detail:** A `tri_YEAR.parquet` filename is ambiguous without a sidecar — it could be a July preliminary (raw, incomplete), October freeze (authoritative), or spring refresh (corrected). The React app reads the `.meta.json` to display the vintage label to users. Omitting the sidecar means users cannot assess data currency and the UI falls back to showing no vintage information. The `SCHEMA_VERSION` constant in `build_parquet.py` is pinned at `"1.0.0"`. DuckDB WASM consumers must verify `schema_version` in the sidecar before executing queries against cached Parquet files to detect schema drift between the cached file and the current query expectations.  
**Risk if Wrong:** Users (researchers, public health officials, journalists) make decisions based on reported release quantities. A user looking at July preliminary data without knowing it's preliminary may draw incorrect conclusions that the October-freeze data would correct. Additionally, a DuckDB WASM consumer querying a Parquet file with an older schema would fail to find expected columns (e.g., `unit_of_measure` for dioxin handling — see A-048).

---

### A-039 · Historical Parquet files must be rebuildable for prior years (not just the current year)
**Confidence:** High  
**Source:** TWO_MODES_DEEP_DIVE.md §When It Should Run  
**Detail:** The spring data refresh incorporates retroactive corrections to prior years' TRI data. A Parquet file for 2019 built before a 2026 spring refresh may contain different values than one built after. The `workflow_dispatch` input `years` supports targeting specific years (e.g., `2018 2019 2020`) rather than only `latest`.  
**Risk if Wrong:** Historical Parquet files that are never rebuilt become progressively less accurate as EPA incorporates retroactive corrections. For research use cases, stale historical files are a data quality problem. Periodic full-history rebuilds (or differential updates for years with known revisions) are needed for long-term data quality.

---

### A-040 · `pyarrow` is an optional dependency; it must be in the `[ingestion]` extras, not the base install
**Confidence:** High  
**Source:** ADR-001 §Appendix A — Python Dependency Specification; TWO_MODES_DEEP_DIVE.md §Build Parquet  
**Detail:** `pyarrow` (Parquet writer used by pandas `to_parquet()`) is listed under `[project.optional-dependencies] ingestion` in `pyproject.toml`, not in the base `dependencies`. The FastAPI backend itself does not need Parquet writing. Installing the full `[ingestion]` extras set on the API server would waste ~30 MB and introduce an unnecessary dependency.  
**Risk if Wrong:** Accidentally moving `pyarrow` to base dependencies adds unnecessary bloat to the Docker image used for the FastAPI API server.

---

### A-050 · TRI land, air, and underground release totals are computed from their constituent fields; no pre-aggregated EPA column name is assumed
**Confidence:** High  
**Source:** TOXMAP_TRI_DATA_AUDIT.md (C-4); EPA TRI Basic Data Files Documentation (Fields 51–64)  
**Detail:** EPA TRI CSV exports do not guarantee the presence of a pre-computed aggregate column named `"ON-SITE LAND RELEASES"` or equivalent — the documented approach is to sum the constituent fields for a given reporting year. Release medium totals are therefore computed in the ingestion pipeline using three constant lists: `LAND_RELEASE_FIELDS` (TRI Fields 57–64: RCRA landfills, land treatment, surface impoundments, other disposal), `AIR_RELEASE_FIELDS` (Fields 51+52: fugitive air + stack air), and `UNDERGROUND_RELEASE_FIELDS` (Fields 55+56: Class I + Class II-V wells). The `min_count=1` parameter in `pandas.DataFrame.sum()` ensures rows where all constituent columns are absent produce `NaN` rather than `0.0`, preserving the NULL-means-absent semantics of Data Integrity Rule 3.  
**Risk if Wrong:** If the pipeline assumed a named aggregate column that is absent in a given year's EPA export, pandas would silently return `NaN` for all rows of that medium, effectively zeroing out an entire release category with no error raised. The computed-sum approach eliminates this silent-drop failure mode but requires updating the field-name constant lists whenever EPA renames or adds land-disposal subcategories across reporting years (e.g., the `5.5.3 – SURFACE IMPOUNDMENT` legacy field was split into `5.5.3A – RCRA` and `5.5.3B – OTHER` in a prior revision).

---

### A-053 · Chemical Families transparently expand searches to include related TRI reporting categories
**Confidence:** High  
**Source:** ADR-007 §Decision; `backend/app/models/chemical_family.py`  
**Detail:** EPA TRI allows facilities to report the same element under multiple categories (e.g., LEAD, LEAD COMPOUNDS, LEAD AND LEAD COMPOUNDS). A citizen searching for "lead" may inadvertently see incomplete results. ADR-007 introduces a Chemical Families feature: when a user searches for a parent element, the system auto-expands the search to include all related TRI reporting categories, aggregates releases across family members per facility per year, preserves an audit trail showing breakdown by chemical variant, and discloses the expansion with a banner. The data model uses `chemical_families` (parent → children mapping) and `chemical_family_members` (join table with `is_parent` flag) tables.  
**Risk if Wrong:** Without chemical families, users searching for "lead" would miss facilities that reported under "LEAD COMPOUNDS" only — defeating the purpose of right-to-know legislation. The opt-out ("Search exact term only") exists for researchers who need raw TRI data without aggregation.

---

## 9. Testing Assumptions

### A-041 · All Gherkin acceptance scenarios run against the FastAPI dev server, not the DuckDB WASM path
**Confidence:** High  
**Source:** TWO_MODES_DEEP_DIVE.md §Running the Tests in Dev Mode; ADR-004 §Neutral Consequences  
**Detail:** The acceptance test suite (`TOXMAP_ACCEPTANCE_TESTS.md`) runs against `docker compose`-hosted FastAPI. As of Phase 6, there are 111 Gherkin scenarios across 9 feature files. The tests need a real queryable server to verify behaviors like `restrict_to_state=true` returning only in-state facilities. Playwright E2E tests can run against either mode; most are mode-agnostic.  
**Risk if Wrong:** Any behavior that diverges between the FastAPI path and the DuckDB WASM path would pass acceptance tests but fail in production. The Playwright E2E suite (which can be pointed at the DuckDB build) is the primary guard for production-mode regressions.

---

### A-042 · pytest must run single-threaded (no pytest-xdist) because tests share a database session
**Confidence:** High  
**Source:** ADR-001 §Appendix A — pyproject.toml (`addopts = "-p no:xdist"`)  
**Detail:** Integration tests use a shared PostGIS database session. Parallel test execution via `pytest-xdist` would cause test interference (concurrent inserts/deletes sharing the same facility IDs, race conditions on seed data state). The `addopts = "-p no:xdist"` line enforces sequential execution.  
**Risk if Wrong:** If `pytest-xdist` is accidentally installed and run, tests fail intermittently with foreign-key violations or unexpected query results — a notoriously difficult bug to diagnose. The `pyproject.toml` flag prevents this.

---

### A-043 · Seed data values (facility coordinates, release quantities) must trace to primary sources
**Confidence:** High  
**Source:** GOVERNANCE.md §2.4 Data Steward; TOXMAP_TEST_SEED_DATA.md  
**Detail:** The seed data (`TOXMAP_TEST_SEED_DATA.md`) uses real facility names, coordinates, and release quantities sourced from the 2011 UCD usability study task scenarios. These values are used in both the acceptance test scenarios and as the deterministic test fixtures for the API contract tests. Any change requires a Data Steward review with a primary source citation.  
**Risk if Wrong:** Seed data with incorrect coordinates or quantities would cause acceptance tests to pass in isolation but test the wrong behavior (e.g., a radius search returning a facility that would not actually be within range at the specified coordinates).

---

## 10. Scope & Product Boundary Assumptions

### A-044 · TOXMAP is a public-read-only application; no user accounts, no write operations
**Confidence:** High  
**Source:** TOXMAP_TECH_STACK_ANALYSIS.md §4 (NF-04)  
**Detail:** Explicit non-functional requirement. The application targets government agencies, businesses, academia, and the general public — all as read-only consumers of EPA data. There is no planned feature that requires user identity.  
**Risk if Wrong:** See A-013 (stateless URL routing) and A-034 (no auth). Any write feature requires a significant rearchitecture.

---

### A-045 · The application is an open-source clone with MIT/Apache 2.0 license; all dependencies must be compatible
**Confidence:** High  
**Source:** TOXMAP_TECH_STACK_ANALYSIS.md §4 (NF-05); GOVERNANCE.md §3  
**Detail:** All chosen libraries (MapLibre GL MIT, FastAPI MIT, React MIT, DuckDB WASM MIT) are open-source compatible. ESRI's proprietary ArcGIS stack (used in the original TOXMAP) is explicitly not used. New dependency PRs require a maintainer review of license and CVE status.  
**Risk if Wrong:** Adding a GPL-3 dependency to a project licensed as MIT/Apache 2.0 creates a license incompatibility. The governance process (§3 of GOVERNANCE.md) requires maintainer license review on every new dependency PR.

---

### A-046 · Pre-2005 TRI data is a lower priority; Option B (Supabase, 500 MB) covers 2005–present
**Confidence:** High  
**Source:** ADR-004 §Option B — Data Size vs. Supabase 500 MB Limit  
**Detail:** If Option B is adopted, the Supabase database holds ~20 years of TRI data (~300 MB). Data from 1987–2004 is available only through Option A's Parquet files. The explicit recommendation is to load 2005–present for Option B, as this covers the data range most users care about. Researchers needing pre-2005 data are expected to use Option A or the EPA's own TRI Explorer.  
**Risk if Wrong:** A user specifically researching 1987–2004 industrial chemical releases (e.g., studying Superfund site formation history) would not find that data in an Option B deployment. This is an accepted scope limitation, not a bug.

---

## Summary Table

| ID    | Category             | Confidence | Risk Level |
|-------|----------------------|------------|------------|
| A-001 | Data Freshness       | High       | Low        |
| A-002 | Data Freshness       | High       | Medium     |
| A-003 | Data Sizing          | Medium     | Low        |
| A-004 | Memory / Performance | High       | Low        |
| A-005 | Data Sizing          | High       | Low        |
| A-006 | Data Pipeline        | Medium     | Medium ¹   |
| A-007 | Data Pipeline        | Medium     | Low        |
| A-008 | Technology           | High       | Low        |
| A-009 | Technology           | High       | Medium     |
| A-010 | Technology           | High       | Low        |
| A-011 | Architecture         | High       | Low        |
| A-012 | Architecture         | High       | Low        |
| A-013 | Architecture         | High       | **High**   |
| A-014 | Geocoding            | High       | Medium     |
| A-015 | Geocoding            | High       | Low        |
| A-016 | Hosting              | High       | Low        |
| A-017 | Hosting              | High       | Low        |
| A-018 | Hosting              | High       | Low        |
| A-019 | Hosting              | Medium     | Medium     |
| A-020 | Hosting              | High       | Low        |
| A-021 | Browser Compat       | High       | Medium     |
| A-022 | Browser Compat       | High       | Low        |
| A-023 | Memory               | Medium     | Low        |
| A-024 | Memory               | High       | Low        |
| A-025 | UX                   | Medium     | Medium     |
| A-026 | UX                   | High       | Low        |
| A-027 | UX                   | High       | Low        |
| A-028 | UX / Legal           | High       | **High**   |
| A-029 | Privacy              | High       | Medium     |
| A-030 | Performance          | High       | Low        |
| A-031 | Performance          | Medium     | Medium     |
| A-032 | Performance          | High       | Low        |
| A-033 | Performance          | Medium     | Medium     |
| A-034 | Security             | High       | **High**   |
| A-035 | Security             | High       | **High**   |
| A-036 | Security             | High       | Medium     |
| A-037 | Build Pipeline       | High       | Low        |
| A-038 | Data Integrity       | High       | Medium     |
| A-039 | Data Integrity       | High       | Medium     |
| A-040 | Build Pipeline       | High       | Low        |
| A-041 | Testing              | High       | Medium     |
| A-042 | Testing              | High       | Low        |
| A-043 | Testing              | High       | Medium     |
| A-044 | Scope                | High       | Low        |
| A-045 | License              | High       | **High**   |
| A-046 | Scope                | High       | Low        |
| A-047 | Data Source          | High       | Medium     |
| A-048 | Data Integrity       | High       | **High**   |
| A-049 | Data Integrity       | High       | Medium     |
| A-050 | Build Pipeline       | High       | Low        |
| A-051 | Hosting / Runtime    | High       | Medium ²   |
| A-052 | Geocoding            | High       | Low        |
| A-053 | Data Model           | High       | Medium     |

¹ A-006 risk mitigated by computed-aggregation approach (C-4 fix) and alias detection (H-1, H-2 fixes) per TRI Data Audit 2026-07-23. Coordinate column mappings (`LATITUDE`, `LONGITUDE`) remain single-name and are the highest residual exposure.

² A-051 (OpenFreeMap runtime dependency) is medium risk because the basemap is visual-only; its unavailability degrades UX but does not prevent data access or facility search functionality.





