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

- **Epic 6.EXPORT: Data Export UI** — Full export functionality for TRI facilities, Superfund sites, and map screenshots. See [docs/product/EXPORT_FEATURE_PLAN.md](docs/product/EXPORT_FEATURE_PLAN.md). [agent]
  - **ResultsTable CSV export** — "Download CSV" button exports search results. (`data-testid="export-csv-btn"`)
  - **FacilityDrawer export** — Export button in drawer header downloads single facility's multi-year release history. (`data-testid="facility-export-btn"`)
  - **SuperfundDrawer export** — Export button downloads site contaminants list. (`data-testid="superfund-export-btn"`)
  - **Map screenshot** — Screenshot button captures PNG with OSM attribution watermark. (`data-testid="map-screenshot-btn"`)
  - **Browse export endpoint** — `GET /api/v1/export/csv/browse` for nationwide searches without spatial constraint.
- **CSV injection protection** — `escapeCsvField()` utility prefixes formula chars (`=+-@`) with single quote; escapes quotes and wraps fields. [agent]
- **ADR-010: Unified Site Search** — Extended `GET /api/v1/facilities/search` endpoint to search **both TRI facilities and Superfund sites**. Returns unified results with `site_type` discriminator ("tri" | "superfund") and `site_id` field. Supports TRI ID, EPA ID, or name with same relevance scoring. Frontend shows site type badge (TRI/Superfund) alongside match type badge. See [docs/adr/ADR-010](docs/adr/ADR-010-facility-search-autocomplete.md). [agent]
- **Facility search frontend hook** — `useFacilitySearch` hook with 300ms debounce for typeahead autocomplete. [agent]
- **FacilitySearchInput component** — Autocomplete search input in search panel with dropdown showing site ID, facility name, city/state for each result. Match type badges (ID Match/Name Match) and site type badges (TRI/Superfund) indicate relevance and dataset. (`data-testid="facility-search-input/dropdown/option"`). [agent]
- **TRI Facility ID link in drawer** — TRI ID below facility name in FacilityDrawer is now clickable, linking to EPA EnviroFacts (`data-testid="facility-tri-id-link"`). [agent]
- **EPA TRI Facility Report link** — Added "EPA TRI Facility Report ↗" link at bottom of FacilityDrawer (above Close button) for parity with Superfund panel (`data-testid="facility-epa-report-link"`). [agent]
- **7.UX.1: State-only browse mode** — Users can now select a state and click Search without entering a chemical or location. Map zooms to selected state center. Works for both TRI and Superfund datasets. [agent]
- **STATE_CENTERS map constant** — Added 56-entry `STATE_CENTERS` in `App.tsx` with lat/lon/zoom for all US states, DC, and territories for state-based map centering. [agent]
- **CI Workflow Onboarding Guide** — New [docs/onboarding/CI_WORKFLOW_GUIDE.md](docs/onboarding/CI_WORKFLOW_GUIDE.md) documenting all 6 CI jobs, 5 quality gates, artifacts, and troubleshooting. [agent]
- **ADR-009: Cloudflare Workers Geocoding Proxy** — Documents production scaling path for geocoding with global cache and aggregate rate limiting (~$0-5/month). See [docs/adr/ADR-009](docs/adr/ADR-009-cloudflare-workers-geocoding-proxy.md). [agent]
- **Deployment guide Workers proxy section** — Complete implementation guide for deploying the geocoding proxy. See [docs/deployment/DEPLOYMENT_GUIDE.md](docs/deployment/DEPLOYMENT_GUIDE.md) §"Cloudflare Workers Proxy". [agent]

### Changed

- **Superfund panel EPA ID now clickable** — EPA ID in `SuperfundDrawer.tsx` is now an `<a>` link to the EPA Site Progress Profile when `epa_progress_url` is available (`data-testid="superfund-epa-id-link"`). [agent]
- **Superfund contaminants display decluttered** — Removed inline CAS numbers from contaminant rows for cleaner UI; chemical name + PubChem/ToxFAQs links remain. [agent]
- **7.UX.2: Superfund drawer EPA link parity** — Moved "EPA Site Progress Profile" link from scrollable body to fixed footer position (above Close button), matching TRI drawer layout. [agent]
- **7.UX.3: Reporting Year filter now applies to facility drawer** — Added `year` query parameter to `GET /api/v1/facilities/{id}` endpoint. Frontend passes selected year to drawer; "Top Chemicals", "By Medium", and "15-Year Trend" tabs now show year-filtered data. Labels dynamically display "(2020)" or "(all years)" based on selection. [agent]
- Updated ACCEPTED_RISKS.md RISK-009 and RISK-010 to reference Workers proxy as recommended mitigation [agent]
- Updated ADR-006 (Photon geocoding) with reference to ADR-009 for production scaling [agent]
- Updated ADR-004 free services table to include Workers, Photon, and OpenFreeMap [agent]
- Updated CONTEXT_SUMMARY.md geocoding line with ADR-009 reference [agent]

### Fixed

- **Superfund drawer close button parity** — Updated SuperfundDrawer close button to match FacilityDrawer style (centered gray "Close panel" instead of left-aligned blue "← Close"). [agent]
- **By Medium discrepancy note conditional display** — Fixed confusing note in By Medium tab that always talked about discrepancies even when no meaningful discrepancy existed. Now shows three variants: (1) full discrepancy explanation when aggregate ≥1 lb, (2) "aggregate minimal but some years show ≥5%" warning when per-year discrepancies cancel out, (3) simple note when no discrepancies exist. [agent]
- **Superfund ingestion now populates `epa_progress_url`** — `superfund_ingest.py` now builds EPA Site Progress Profile URL from SEMS `site_id` (different from `epa_id`). Re-ran ingestion to update 2,021 existing sites. [agent]
- **ci.yml YAML syntax error** — Fixed line 369 unquoted colon in benchmark step name (`gate: +20%` → `"gate: +20%"`) that caused GitHub Actions parse failure. [agent]
- **mypy strict mode errors** — Configured targeted overrides in `pyproject.toml` for FastAPI decorators (`disallow_untyped_decorators = false`), GeoAlchemy2 geometry columns, and SQLAlchemy forward refs. Reduced errors from 97 → 0. [agent]
- **Unit test ATSDR toxid values** — Fixed incorrect toxid assertions in `test_atsdr_family_inheritance.py` (e.g., NICKEL was 18 but should be 44 per actual ATSDR data). [agent]
- **Missing ATSDR known gaps** — Added SULFURIC ACID, HYDROCHLORIC ACID, NITRIC ACID to `KNOWN_GAPS` set in unit tests (not in ATSDR ToxFAQs). [agent]
- **Duplicate dict keys** — Removed duplicate dictionary key entries in `superfund_cas_lookup.py` flagged by ruff F601. [agent]
- **6.EXPORT.16: Nationwide search CSV export** — Fixed empty CSV when searching by state without map location. Root cause: `/api/v1/export/csv` required lat/lon; frontend fell back to Kansas center (38.5, -96) with 500-mile radius, excluding distant states. Fix: Added `/api/v1/export/csv/browse` endpoint without spatial constraint; frontend detects `lat=null` and uses browse endpoint. [agent]
- **6.EXPORT.17: Map screenshot blank PNG** — Fixed blank screenshot caused by WebGL clearing drawing buffer after each frame. Fix: Added `preserveDrawingBuffer={true}` to MapLibre `<Map>` component, allowing `toDataURL()` to capture rendered map content. [agent]

### Tests

- **6.EXPORT regression tests** — Added E2E scenarios (`export.feature`) for nationwide CSV export and non-blank PNG screenshot; unit tests (`test_export_browse.py`) for browse endpoint state/chemical filtering. [agent]
- **6.UX regression tests** — Added API tests (`superfund.feature`) verifying `epa_progress_url` populated with SEMS URL pattern; E2E tests (`ux_invariants.feature`) verifying EPA ID link visible and no CAS patterns in contaminant rows. [agent]
- **7.UX.1 regression tests** — Added API tests (`facility_search.feature`, `superfund.feature`) for state-only browse endpoints; E2E tests (`ux_invariants.feature`) for state-only search flow and map zoom behavior. [agent]
- **7.UX.2 regression tests** — Added E2E test (`ux_invariants.feature`) verifying Superfund EPA link is in fixed footer position above close button. [agent]
- **7.UX.3 regression tests** — Added API tests (`release_trends.feature`) for facility detail year filter; E2E tests (`ux_invariants.feature`) verifying drawer tabs show year-specific data when year is selected. [agent]
- **ADR-010 regression tests** — Added 4 E2E scenarios (`@ADR010`): facility search input present, autocomplete dropdown shows results, TRI ID link visible and points to EPA EnviroFacts, EPA TRI Facility Report link above close button. [agent]

### Security

- **Replaced gitleaks-action with CLI** — `gitleaks/gitleaks-action` now requires paid license for organizations. Replaced with direct CLI invocation (`gitleaks detect`) which is Apache 2.0 licensed and free. Updated `PINNED_ACTIONS.md` to document change. [agent]
- **Major dependency upgrades** — Updated all frontend and backend dependencies to latest versions to address Dependabot security flags [agent]:
  - **Frontend**: React 18→19, Vite 5→6, maplibre-gl 4→6, TypeScript 5.5→5.7, ESLint 8→9
  - **Backend**: FastAPI 0.111→0.141, Pydantic 2.8→2.13, SQLAlchemy 2.0.31→2.0.51, pytest 8.2→8.4, Playwright 1.44→1.52
  - ⚠️ React 19 is a major upgrade requiring `npm install` and potential code changes for new ref handling/context patterns

---

### ⚠️ Phase Rollback (2026-08-03) [agent]

**Phase 7 (Production Deploy) rolled back to Phase 6 (Full QA Pass).**

Development halted due to new defects discovered pre-Phase 7 deployment. Phase 6 DoD verification was premature.

- Reverted `CURRENT_PHASE.txt` from `7` to `6`
- Updated `TOXMAP_PROGRESS_TRACKER.md` with rollback status
- Created `docs/escalations/ROLLBACK_PHASE7_TO_PHASE6_20260803.md`
- Updated `README.md` to indicate development halt

**Required actions:** QA triage of new defects → bug fixes → Phase 6 DoD re-verification.

---

### ~~Milestone M6 — Feature Complete 🎉 (2026-07-31) [agent]~~ **REVOKED**

Phase 6 (Full QA Pass) complete. All acceptance criteria verified:
- API feature tests: 31/31 pass
- E2E Playwright tests: 41/41 pass
- Performance benchmarks: 5/5 SLAs pass
- Security regression tests: 15/15 pass
- Schemathesis schema conformance: 1604/1604 checks pass
- Semgrep OWASP-Top-Ten: 0 High/Critical findings

Bug fixes shipped (6.BUG.1–6.BUG.16):
- Fixed "Both" mode drawer selection (TRI vs Superfund)
- Fixed US zip code geocoding to Mexico (Photon bias)
- Simplified state filter UX (Option C)
- Fixed nationwide chemical search error
- Fixed Superfund sites missing from nationwide search
- Added "Continental US" filter option
- Fixed nationwide search viewport filtering
- Fixed Superfund markers shown when not relevant
- Fixed auto-zoom to facility on new search
- Improved Superfund iconography visibility (3-way NPL status)
- Added zoom-based marker scaling
- Added marker opacity for overlapping visibility
- Updated TRI color scheme (deep stoplight colors)
- Added green tier seed data for color_band coverage
- Added color band regression tests
- Fixed legend consistency

Phase 7 (Production Deploy) commenced.

### Phase 7 Bug Fixes (2026-07-31) [agent]

Bug fixes shipped during pre-production validation (7.BUG.1–7.BUG.9):
- **7.BUG.1:** Fixed results count flickering — results table now uses API-constrained
  results (`triAllResults`) instead of viewport-filtered data that changed on scroll
- **7.BUG.2:** Added TRI hover tooltip — hovering results table row now shows popup
  on map with facility name
- **7.BUG.3:** Fixed overlapping popups — hover tooltip skipped when facility is
  already selected to prevent duplicate popups
- **7.BUG.4:** Added Superfund hover parity — Superfund results now zoom map and show
  tooltip on hover, matching TRI behavior
- **7.BUG.5:** Added progressive TRI circle sizing — circles now sized by release
  tier (red=100%, orange=83%, yellow=67%, green=50%) to reduce visual clutter
  when zoomed out; legend updated with proportional circle sizes
- **7.BUG.6:** Added Superfund contaminants ingestion — integrated EPA SEMS
  Envirofacts API for bulk contaminant fetching (72,569 records, 88% site coverage)
- **7.BUG.7:** Fixed Superfund "in view" count — now shows viewport-filtered count
  instead of total (1,816). Added `superfundInViewCount` memo filtering by `mapBbox`
- **7.BUG.8:** Fixed results table limited to 10 items — removed `.slice(0, 10)` limit;
  all results now render and are scrollable
- **7.BUG.9:** Fixed map not filtering by search criteria — map now shows only
  facilities/sites matching active search filters (CONUS, chemical). Added
  `triFacilitiesForMap` memo; POGO MINE (AK) no longer shows when CONUS filter active

### ADR-007: Chemical Families Implementation (2026-07-31) [agent]

Chemical family expansion for transparent right-to-know compliance:
- Added `chemical_families` and `chemical_family_members` tables (Alembic migration)
- Seeded 18 families with 35 member chemicals (lead, mercury, chromium, etc.)
- API auto-expands family chemicals (e.g., "lead" → "LEAD", "LEAD COMPOUNDS", etc.)
- Added `exact_match` query parameter to disable expansion for researchers
- Added `ChemicalFamilyBanner.tsx` disclosure banner with "Search exact term only" option

Bug fixes shipped (7.BUG.9–7.BUG.19):
- **7.BUG.9:** Fixed seed script import error — changed `async_session_factory` to
  `AsyncSessionLocal` in `seed_chemical_families.py`
- **7.BUG.10:** Fixed exact match not narrowing results — `exact_match=true` now uses
  `func.upper(Chemical.name) == chemical.upper()` for strict equality instead of ILIKE
- **7.BUG.11:** Fixed SearchPanel scroll in small windows — wrapped form in scrollable
  container with `minHeight: 0`
- **7.BUG.12:** Fixed chemical family banner padding — added 8px/12px padding wrapper
- **7.BUG.13:** Added sidebar resize handle — drag to adjust width 200–600px; uses
  direct DOM manipulation + capture-phase events for smooth performance
- **7.BUG.14:** Fixed PostCSS config ESM error — converted to CommonJS syntax
- **7.BUG.15:** Fixed MERCURY family not expanding — added whitespace normalization to
  seed script; fixed chemical names for MERCURY, CHROMIUM, ZINC, etc. families
- **7.BUG.16:** Fixed Superfund contaminants missing PubChem links — added `pubchem_url`
  field to `SuperfundContaminant` schema and service query; updated frontend drawer
  to display PubChem links alongside ATSDR links for matched chemicals
- **7.BUG.17:** Added comprehensive Superfund CAS lookup (180+ chemicals: PAHs, PCBs,
  chlorinated solvents, pesticides, explosives, PFAS, radionuclides) + redesigned
  SuperfundDrawer UI with chemical names as PubChem links, inline CAS numbers
- **7.BUG.18:** **CRITICAL** Fixed ATSDR ToxFAQs links pointing to wrong chemicals —
  MANGANESE incorrectly linked to Methylene Chloride (toxid=42 instead of 23). Rebuilt
  `_ATSDR` dict in `superfund_cas_lookup.py` using verified URLs from scraped CDC data
  (`scripts/atsdr_toxid_map.csv`). Corrected ~15 toxid mappings and added 80+ missing
  chemicals (CFCs, alkylbenzenes, metal oxides, petroleum fractions, nitrosamines).
- **7.BUG.19:** ATSDR external links now display as "ToxFAQs™" instead of "ATSDR" for
  transparency — users know they're accessing the CDC/ATSDR ToxFAQs chemical database
- **7.BUG.20:** Fixed TRI chemicals missing ATSDR ToxFAQs links — "ZINC COMPOUNDS",
  "LEAD AND LEAD COMPOUNDS", and other chemical family members had no ToxFAQs despite
  parent element (ZINC, LEAD) having ATSDR URL. Root cause: (1) `tri_ingest.py` never
  populated `atsdr_url` — only `pubchem_url`; (2) backfill only did exact name match.
  Fix: Updated `tri_ingest.py` to populate `atsdr_url` on ingest; updated backfill
  script to inherit ATSDR URL from chemical family parent per ADR-007. Results: 61
  exact matches + 19 family inheritance = 80 chemicals with ATSDR URLs.
  (2026-08-03) [agent]
- **7.BUG.21:** Fixed Superfund contaminants missing PubChem links for petroleum
  mixtures — TPH, JP-5, JP-8, Fuel Oil had broken `/compound/` URLs that either
  returned 404 or redirected to wrong compounds. Root cause: PubChem `/compound/`
  URLs don't work for complex mixtures (e.g., `/compound/JP-5` redirects to an
  organic molecule CID 156012505, not jet fuel). Fix: Updated `superfund_cas_lookup.py`
  to use 3-tuple format `(CAS, ATSDR, PUBCHEM)` with explicit PubChem URLs:
  TPH→`/substance/135312467`, JP-5→`/substance/135356845`, JP-8→`/substance/505788256`,
  Fuel Oils→`/compound/Fuel-Oils`. Updated `superfund_service.py` to handle both
  2-tuple and 3-tuple lookups. Regression tests added to `test_superfund_cas_lookup.py`.
  (2026-08-03) [agent]
- **7.BUG.22 (CRITICAL):** Fixed TRI chemical categories with broken PubChem URLs —
  34 chemicals used EPA Form R category codes (N010, N090, N100, etc.) as CAS numbers,
  generating 404 URLs like `/compound/N090`. Root cause: EPA TRI data uses N### codes
  for compound families (ANTIMONY COMPOUNDS=N010, COPPER COMPOUNDS=N100, etc.) — these
  are NOT CAS numbers. Fix: (1) Updated `_pubchem_url()` in `tri_ingest.py` to validate
  CAS format (`^\d{2,7}-\d{2}-\d$`) and detect N### codes; (2) Added `_TRI_CATEGORY_PUBCHEM`
  mapping all 34 codes to correct URLs: metals→`/element/{Element}` (Copper, Lead, Mercury),
  compounds→`/compound/{CID}` (Cyanide, Warfarin), classes→`/#query={term}` searches
  (diisocyanates, dioxin); (3) Created `scripts/fix_tri_category_pubchem_urls.py` migration;
  (4) Added 79 regression tests in `test_tri_ingest.py`. (2026-08-03) [agent]
- **7.BUG.23:** Fixed dioxin compound classes missing PubChem links + filtered "NOT PROVIDED"
  from Superfund contaminants. Two issues: (1) DIOXINS (CHLORINATED DIBENZODIOXINS) and
  similar compound classes had no PubChem URL because CAS was "N/A"; (2) 26 Superfund sites
  had "NOT PROVIDED" as a contaminant. Fix: (1) Updated `superfund_cas_lookup.py` dioxin
  entries to use 3-tuple format with explicit PubChem URLs — specific dioxins→`/compound/{CID}`
  (2,3,7,8-TCDD→CID 15625), dioxin classes→`/#query={term}` search URLs; (2) Added placeholder
  filtering in `superfund_service.py` to exclude "NOT PROVIDED", "UNKNOWN", "N/A" values.
  F.E. Warren AFB now shows 39 contaminants instead of 40. 8 regression tests in
  `TestDioxinPubChemUrls`. (2026-08-03) [agent]
- **7.BUG.24:** Fixed popup cutoff at screen edges — TRI/Superfund popups were clipped when
  clicking markers near right or top viewport boundaries. Extended `MapContainer.tsx` auto-pan
  logic to check all edges (right edge: `panBy(+offset, 0)`; top edge: `panBy(0, -offset)`).
  Combined offsets applied for corner cases. (2026-08-04) [agent]
- **7.BUG.25 (ADR-008):** Implemented geocoding confidence scoring — Photon geocoder now scores
  multiple candidates using 6 weighted signals: house number (+0.35), street name similarity
  (+0.25), city/state/postal (+0.30), proximity to viewport (+0.10). Added confidence levels
  (exact ≥0.85, high ≥0.65, approximate ≥0.40, low <0.40) with UI feedback badge (green/yellow/
  orange/red). Fixes "100 Mill Rd, Port Townsend, WA" returning Mexico instead of Washington.
  5 regression tests in `ux_invariants.feature`. See [ADR-008](docs/adr/ADR-008-geocoding-confidence-scoring.md). (2026-08-04) [agent]
- **7.BUG.26:** Fixed Hanford nuclear site radionuclides missing contaminant links —
  CARBON-14, CESIUM (elemental), COBALT-60, EUROPIUM (and -152/-154/-155), NICKEL-63,
  STRONTIUM, TECHNETIUM-99, TRITIUM, IODINE-129, NEPTUNIUM, PLUTONIUM-240, PLUTONIUM-239/240,
  THORIUM-228, URANIUM-233 had no PubChem/ToxFAQs links. Added 25+ radionuclides to
  `superfund_cas_lookup.py` with verified CAS numbers. Also added Hanford-specific TPH
  variants ("TOTAL PETROLEUM HYDROCARBON -DIESEL/-GASOLINE"). (2026-08-04) [agent]
- **7.BUG.27 (CRITICAL):** Fixed 15-year trend chart data loss — per-chemical releases were
  overwritten instead of aggregated. For 2017, Arlington Plating has 6 chemicals totaling
  12,916 lbs, but chart showed only 12,636 lbs (the last chemical processed). Also fixed:
  x-axis gaps for missing years, 15-year range now relative to selected year filter (or
  current year if default), heading shows year range, tooltip shows "Reporting Year: YYYY".
  Added 4 E2E regression tests in `ux_invariants.feature` to catch this data loss.
  (2026-08-05) [agent]
- **7.BUG.28:** Fixed Top Chemicals table missing time range disclosure per original Fig 11
  design. Table now shows: (1) "Release Amount (lbs./all years)" header clarifying time
  range; (2) "%" column showing each chemical's percentage of total; (3) "TOTAL" footer row
  with aggregate sum; (4) numbered ranks (1), 2), etc.) per original. Example: Lyondell
  Chemical Co in Fig 11 shows 83,353,728 lbs total across 5 chemicals + "Other chemicals".
  (2026-08-05) [agent]
- **7.BUG.29 (CRITICAL):** Fixed "All years" search returning single-year data instead of
  all-years aggregate. LYONDELL CHEMICAL CO showed 2,976,441 lbs (just 2024) but should
  show 94,575,561 lbs (all years 1987-2024). Root cause: `_resolve_year()` converted
  `year=None` to latest year instead of keeping it as "aggregate all". Also fixed:
  `get_facility_detail()` top_chemicals now aggregates all years; added `total_release_lbs`
  field for correct TOTAL row; added "Other chemicals" row for difference between facility
  total and top 5 sum. Backend + frontend + schema changes. (2026-08-05) [agent]
- **7.BUG.38:** TRI medium discrepancy display with per-year breakdown (Option A + B). Changes:
  1. "By Medium" tab now shows "Aggregate Discrepancy (all years)" with warning that +/− discrepancies
     may cancel out across years — footnote directs users to 15-Year Trend tab for details.
  2. 15-Year Trend tab now includes per-year discrepancy in tooltip (EPA total, medium sum, discrepancy %).
  3. Red ring indicator around chart dots for years with ≥5% discrepancy.
  4. Legend explaining discrepancy indicators added below Trend chart.
  5. **Option B follow-up:** Tooltip now always shows Medium Sum and Discrepancy for years with data,
     even when discrepancy is ~0 (e.g., "Discrepancy: +0 lbs (0.0%)"). Previously, discrepancy < 1 lb was
     hidden, which confused users who couldn't tell if data was missing or consistent.
  6. **Terminology fix:** Renamed "variance" → "discrepancy" throughout — "variance" is a statistical
     term (σ²); "discrepancy" correctly describes the arithmetic difference between EPA total and
     computed medium sum that should match but don't due to data quality issues.
  Root cause: EPA TRI Field 65 does not always equal sum of Fields 51-64 due to self-reporting
  errors. This prevents aggregation from masking year-over-year data quality issues.
  Added `data-testid` values: `medium-discrepancy-section`, `medium-epa-total`, `medium-discrepancy-value`,
  `medium-discrepancy-footnote`, `trend-tooltip`, `trend-tooltip-discrepancy`, `trend-discrepancy-legend`.
  Escalation docs: `ESCALATION_20260806_TRI_MEDIUM_TOTAL_VARIANCE.md`, 
  `ESCALATION_20260806_VARIANCE_AGGREGATION_MASKING.md`. 3 regression tests. (2026-08-06) [agent]

### Fixed

<!-- Pre-deployment validation (2026-07-31) [agent] -->
- **CRITICAL:** `superfund_ingest.py` — EPA semspub.epa.gov document source (HQ/100001259)
  is defunct (301 redirect to error page). Migrated to EPA ArcGIS Feature Service
  (`FAC_Superfund_Site_Boundaries_EPA_Public`). Now loads 1,816 real NPL sites
  (Final, Proposed, Deleted) with polygon centroids as point coordinates.
  (2026-07-31) [agent]
- **Superfund contaminants data:** Integrated EPA Envirofacts SEMS API
  (`sems.envirofacts_site` + `sems.envirofacts_contaminants`) to fetch contaminant
  lists for each NPL site. Bulk query approach retrieves 72,569 contaminant records
  in <1 minute. 1,594 of 1,816 sites (88%) now have contaminant data with
  ~21 contaminants per site on average. (2026-07-31) [agent]

### Added

<!-- Phase 5 — Demographics Overlay (2026-07-29) [agent] -->
- `components/Demographics/CensusHealthPanel.tsx` — "US Census & Health Data" panel
  with year tabs (Census 2000/2020), category tabs (Population/Income/Mortality),
  sub-layer buttons, and gender radio for mortality; Census 2020 shows "Coming soon"
  (stories 5.1.1–5.1.5, 2026-07-29) [agent]
- `components/Demographics/InlineLegend.tsx` — always-visible color-coded legend
  with values, units from `meta.units`, and "Clear layer" button; UX Invariant 5
  (stories 5.3.1–5.3.3, 2026-07-29) [agent]
- `components/Demographics/colorUtils.ts` — color scale definitions for choropleth:
  blue (percentage), green (income), red (mortality), purple (total population)
  (story 5.2.1, 2026-07-29) [agent]
- `components/Demographics/ZoomNotice.tsx` — "Zoom out to see more counties" notice
  when zoom > 8 (story 5.2.2, 2026-07-29) [agent]
- `hooks/useDemographics.ts` — demographics data hook with AbortController support;
  fetches county polygons from `GET /api/v1/demographics/county?state={state}`
  (story 5.2.1, 2026-07-29) [agent]
- `api/demographics.ts` — typed API client for demographics endpoint
  (story 5.2.1, 2026-07-29) [agent]
- Co-occurrence disclaimer on mortality tabs only; UX Invariant 10
  (story 5.4.1, 2026-07-29) [agent]
- E2E step definitions for T-05, T-06, T-09 scenarios and UX Invariants 5, 10
  in `tests/steps/e2e_steps.py` (QA story, 2026-07-29) [agent]

### Changed

<!-- Phase 5 — Demographics Overlay (2026-07-29) [agent] -->
- `api/geocode.ts` — geocoder now extracts US state code from Photon response
  and returns it in `GeocodeResult.state`; enables demographics API call with
  correct state parameter (fix for 422 error, 2026-07-29) [agent]
- `App.tsx` — integrated demographics panel, inline legend, and zoom notice;
  `useDemographics` now receives state from geocoded search location
  (stories 5.2.1–5.4.2, 2026-07-29) [agent]

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

