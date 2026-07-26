# Test Plan
## Service: `toxmap`

- **Author(s):** Victor Cannestro
- **Maintained By:** Quality Engineering Team
- **Version:** 1.0
- **Last Updated:** 2026-07-17
- **Test Type:** E2E / UI Acceptance Tests (with real browser, full stack — FastAPI + PostGIS + React/MapLibre GL interactions)

---

## Table of Contents
1. [Scope & Objectives](#1-scope--objectives)
2. [Test Architecture](#2-test-architecture)
3. [Test Data](#3-test-data)
4. [Test Scenarios](#4-test-scenarios)
5. [Entry & Exit Criteria](#5-entry--exit-criteria)
6. [Out of Scope](#6-out-of-scope)
7. [Appendix A — Automation Traceability](#appendix-a--automation-traceability)
8. [Appendix B — Page Object Model Reference](#appendix-b--page-object-model-reference)
9. [Appendix C — Run Commands](#appendix-c--run-commands)

---

## 1. Scope & Objectives

### Scope
This plan covers end-to-end browser testing of the full TOXMAP application stack (React + FastAPI + PostGIS) using `pytest-playwright` (Python). Tests verify two categories of requirements:

1. **UCD 2011 Task Scenarios (T-01 through T-09):** The 9 realistic user tasks from the User-Centered Design Inc. usability study commissioned by NLM. These constitute the authoritative acceptance criteria for TOXMAP clone fidelity.

2. **UX Design Invariants (Invariants 1–11):** Non-negotiable design constraints derived from the usability study's critical findings, enforced across all application states.

All tests drive a real browser (Chromium by default, Firefox and WebKit also supported) against a React dev server and seeded FastAPI/PostGIS backend. No mocking of any layer.

### Functionality Under Test

**UCD 2011 Task Scenarios**

| Task | Name | Smoke? |
|------|------|--------|
| T-01 | Lead compound TRI facility near Sparrows Point MD | ✅ |
| T-02 | Superfund-reportable chemical list accessible in ≤ 2 clicks | — |
| T-03 | Copper releases > 8,000 lbs in eastern Nevada | ✅ |
| T-04 | Styrene Superfund site near Front Royal VA | — |
| T-05 | TRI styrene sites with % Under 18 demographic overlay | — |
| T-06 | Median household income overlay with $ units and clear-layer | — |
| T-07 | Largest chlorine release SC vs. nationwide | — |
| T-08 | CDC ToxFAQ link for ammonia — new tab without losing map state | ✅ |
| T-09 | Benzene releases and cancer mortality co-occurrence | — |

**UX Design Invariants**

| # | Invariant | Smoke? |
|---|-----------|--------|
| 1 | Map Contents and Search Results panels never simultaneously visible | ✅ |
| 2 | Results table never contains empty placeholder rows | ✅ |
| 3 | State restriction checkbox actually filters to selected state | ✅ |
| 4 | Search panel labeled "Search Chemical Releases by Location" (not "Quick Search") | ✅ |
| 5 | Demographic legend values visible without mouse interaction | — |
| 6 | TRI (circle) and Superfund (diamond) icons are visually distinct | — |
| 7 | Most recent year toggle includes "(latest year)" label | ✅ |
| 8 | All release quantities display with comma formatting | ✅ |
| 9 | Facility popup always has a close link at the BOTTOM | ✅ |
| 10 | Co-occurrence disclaimer appears only on mortality demographic tab | — |
| 11 | Data vintage label visible and non-empty on page load | ✅ |

**Smoke subset** (every PR): T-01, T-03, T-08 + Invariants 1–4, 7–9, 11.

### Three-Phase Test Flow

```
Phase 1: User Input          Phase 2: Browser Renders       Phase 3: Assert Visible State
┌───────────────────┐        ┌──────────────────────┐       ┌──────────────────────────┐
│  Playwright page  │        │  React renders map   │       │  DOM text content        │
│  actions:         │───────▶│  + calls FastAPI     │──────▶│  Element visibility      │
│  fill, click,     │        │  + renders results   │       │  data-testid presence    │
│  select, navigate │        │  + updates sidebar   │       │  Comma formatting regex  │
└───────────────────┘        └──────────────────────┘       └──────────────────────────┘
     │                               │                               │
  Page Object                  MapLibre GL renders             Playwright expect()
  Model methods                 + HTTPX calls FastAPI          assertions on DOM
```

---

## 2. Test Architecture

### Approach
Tests use `pytest-playwright` with Python Page Object Model (POM) classes. All selectors use `data-testid` attributes from [TEST_ID_REGISTRY.md](TEST_ID_REGISTRY.md). BDD Gherkin feature files drive the UCD task scenarios; imperative pytest functions drive the UX invariants.

```
[ tests/features/e2e/*.feature ]
│  Gherkin steps parsed by pytest-bdd
│
▼
[ tests/steps/e2e_steps.py ]
│  Steps import POM classes from tests/e2e/pages/
│  page: Page fixture injected by pytest-playwright
│
▼
[ Page Object Model ]──────▶[ Playwright: fill(), click(), wait_for_selector() ]
│                                        │
│                              [ React dev server — http://localhost:3000 ]
│                                        │ HTTP
│                              [ FastAPI — http://localhost:8000 ]
│                                        │ asyncpg
│                              [ PostgreSQL + PostGIS — toxmap_test ]
▼
[ Playwright: expect() assertions on DOM ]
  - visible text: "12,485 lbs" (comma-formatted)
  - data-testid: "facility-detail-panel"
  - element count: [data-active="true"] == 1
```

### Test Infrastructure

| Component | Strategy |
|-----------|----------|
| Browser automation | `pytest-playwright` ≥ 0.5; `playwright.sync_api.Page` — **Python only, no TypeScript runner** |
| React dev server | `npm run dev` (port 3000) — must be running before E2E suite |
| FastAPI backend | `uvicorn app.main:create_app --factory --port 8000` — must be running |
| PostGIS database | `postgis/postgis:16-3.4` Docker container |
| Seed data | `tests/fixtures/seed.sql` — `seed_db` fixture before each test |
| Parallel execution | **Disabled** (`-p no:xdist`) — TRUNCATE races corrupt seed state |
| Browser selection | `--browser chromium` (default) / `--browser firefox` / `--browser webkit` |
| CI retry | `pytest-rerunfailures` (`--reruns 2 --reruns-delay 1`) |
| Tracing | Enabled via `conftest.py` context override; trace saved on failure |

### Test Execution Lifecycle

```
BEFORE_EACH
├─ seed_db fixture: TRUNCATE + load seed.sql
├─ Playwright context: new_context(base_url, record_video_dir)
│    ctx.tracing.start(screenshots=True, snapshots=True)
└─ POM fixtures instantiated (map_page, search_panel, etc.)

TEST
├─ Navigate to http://localhost:3000
├─ Wait for [data-testid="map-container"]
├─ Execute user workflow via POM methods
└─ Assert DOM state via Playwright expect()

AFTER_EACH
├─ ctx.tracing.stop(path="test-results/trace.zip")  (on failure)
├─ video saved if CI=true
└─ TRUNCATE all tables
```

### Key `data-testid` Attributes Used for Assertions

All selectors are defined in [TEST_ID_REGISTRY.md](TEST_ID_REGISTRY.md). This table lists the critical assertions by invariant/task:

| Scenario | `data-testid` | Assertion Type |
|----------|--------------|----------------|
| Invariant 1 | `[data-testid="sidebar-panel"][data-active="true"]` | Count == 1 |
| Invariant 2 | `[data-testid="results-row"]` | All have non-empty children |
| Invariant 4 | `[data-testid="search-panel"]` | Text contains "Search Chemical Releases by Location" |
| Invariant 7 | `[data-testid="layer-toggle-tri-latest"]` | Text contains "(latest year)" |
| Invariant 8 | `[data-testid="facility-release-amount"]` | Matches `/\d{1,3}(,\d{3})+/` |
| Invariant 9 | `[data-testid="popup-close-bottom"]` | Visible and clickable after scroll |
| Invariant 11 | `[data-testid="data-vintage-label"]` | Visible; non-empty; not "null"/"undefined" |
| T-01 | `[data-testid="facility-detail-panel"]` | Contains "12,485" |
| T-04 | `[data-testid="superfund-detail-panel"]` | EPA ID "VAD070358684"; contaminants include "STYRENE" |
| T-08 | `[data-testid="atsdr-link"]` | New tab with URL containing "atsdr.cdc.gov" |

---

## 3. Test Data

All E2E tests use seed data from `tests/fixtures/seed.sql`. Tests **must not** insert their own data. For complete fixture values, see [TOXMAP_TEST_SEED_DATA.md §9 Known Good Assertion Values](TOXMAP_TEST_SEED_DATA.md).

| Scenario | Seed Facility | Key UI Assertion Value | Source |
|----------|-------------|----------------------|--------|
| T-01 | Bethlehem Steel MD | `"12,485 lbs"` | Seed |
| T-03 | Robinson NV | `"8,205 lbs"` | **UCD 2011 exact** |
| T-04 | AVTEX FIBERS VA | EPA ID `VAD070358684`, contaminant `STYRENE` | **UCD 2011 exact** |
| T-05 | Warren County VA | `"24.7%"` under-18 | Seed (Census 2000) |
| T-07 | Borden SC + Enterprise LA | `"85,000 lbs"` (SC), `"342,500 lbs"` (national) | Seed |

> ⚠️ **Date Maintenance:** Seed release years are 2006–2008. If the `year` picker default changes to "latest year", confirm the displayed default year still resolves to seed data years. Review before each sprint.

---

## 4. Test Scenarios

### 4.1 UCD 2011 Task Scenarios — Smoke (T-01, T-03, T-08)

These scenarios run on every PR. Full Gherkin in [TOXMAP_ACCEPTANCE_TESTS.md §Feature 7](TOXMAP_ACCEPTANCE_TESTS.md).

**T-01: Lead compounds near Sparrows Point MD**

| Step | Action | Assertion |
|------|--------|-----------|
| Setup | Navigate to map | `[data-testid="map-container"]` visible |
| Input | Type "Sparrows Point, MD"; type "LEAD COMPOUNDS"; select year "2008" | — |
| Search | Click Search | Results sidebar shows "BETHLEHEM STEEL CORP - SPARROWS POINT" |
| Detail | Click facility | `facility-detail-panel` opens; shows `"12,485 lbs"` |
| Format | Inspect numbers | Comma formatting applied: `"12,485"` not `"12485"` |

**T-03: Copper > 8,000 lbs near Ely NV**

| Step | Action | Assertion |
|------|--------|-----------|
| Search | "Ruth, NV" + "COPPER" + 2008 | Results show "ROBINSON NEVADA MINING CO" |
| Detail | Click facility | Detail panel shows `"8,205 lbs"` total |
| Chart | View release by medium | Land bar is largest; Air bar absent or zero |

**T-08: CDC ToxFAQ for ammonia**

| Step | Action | Assertion |
|------|--------|-----------|
| State | Navigate to Houston TX; note coordinates and zoom | Map state captured |
| Link | Click "Chemical Information" for AMMONIA | New browser tab opens |
| Tab | Check new tab URL | Contains `"atsdr.cdc.gov"` or `"ammonia"` |
| Original | Check original tab | Same coordinates and zoom preserved; search state intact |

### 4.2 UCD 2011 Task Scenarios — Full (T-02, T-04–T-09)

Run on `main`/tags only. Full Gherkin in [TOXMAP_ACCEPTANCE_TESTS.md §Feature 7](TOXMAP_ACCEPTANCE_TESTS.md).

| Task | Key Assertions |
|------|---------------|
| T-02 | Superfund chemical list visible within ≤ 2 clicks from map page; contains "STYRENE" |
| T-04 | Diamond Superfund marker; AVTEX detail shows `VAD070358684`, `STYRENE` in contaminants, EPA progress link |
| T-05 | TRI markers visible while choropleth active; legend shows `"24.7%"` for Warren County; sidebar not duplicated |
| T-06 | Income choropleth shows `$` in legend entries; "Clear layer" removes shading and legend |
| T-07 | SC search with state restrict: top result `"85,000 lbs"` from "BORDEN CHEMICALS AND PLASTICS INC"; uncheck state → national top shows `> 85,000 lbs` |
| T-09 | Benzene markers near Houston; mortality choropleth shows "Correlation does not imply causation" disclaimer |

### 4.3 UX Invariants — Smoke (Invariants 1–4, 7–9, 11)

| # | Invariant | Selector | Assertion |
|---|-----------|---------|-----------|
| 1 | Single sidebar | `[data-testid="sidebar-panel"][data-active="true"]` | Count exactly 1 at all times |
| 2 | No empty rows | `[data-testid="results-row"]` | All rows have non-empty `results-row-name` and `results-row-release` |
| 3 | State checkbox filters | After checking "Limit to state" | All markers on map are in selected state |
| 4 | Correct panel labels | Full page text scan | "Search Chemical Releases by Location" visible; "Quick Search" absent |
| 7 | "(latest year)" label | `[data-testid="layer-toggle-tri-latest"]` | Text includes `"(latest year)"` |
| 8 | Comma formatting | `[data-testid="facility-release-amount"]` | Matches `/\d{1,3}(,\d{3})+/` |
| 9 | Bottom close link | `[data-testid="popup-close-bottom"]` | Visible after scroll; clicking dismisses popup |
| 11 | Vintage label on load | `[data-testid="data-vintage-label"]` | Visible; text not empty, not `"null"`, not `"undefined"` |

### 4.4 UX Invariants — Full (Invariants 5, 6, 10)

Run on `main`/tags only.

| # | Invariant | Assertion |
|---|-----------|-----------|
| 5 | Inline legend | `demographic-legend-entry` elements show numeric values + unit `%` without any `hover()` interaction |
| 6 | Distinct icons | TRI facility markers use circle SVG shape; Superfund NPL markers use diamond shape; no collision |
| 10 | Disclaimer scope | `cooccurrence-disclaimer` visible on mortality tab; NOT visible on population or income tabs |

### 4.5 Cross-Cutting E2E Scenarios (CC-*)

| ID | Concern | Assertion |
|----|---------|-----------|
| CC-01 | Accessibility: map page | `axe.run()` — 0 critical/serious violations (WCAG 2.1 AA) |
| CC-02 | Visual regression: map initial load | Pixel diff ≤ 2% vs. committed baseline |
| CC-03 | Visual regression: facility detail panel (T-01) | Pixel diff ≤ 2% vs. committed baseline |
| CC-04 | Visual regression: choropleth overlay (T-05) | Pixel diff ≤ 2% vs. committed baseline |
| CC-05 | Production smoke (T-01) | `BASE_URL=https://toxmap.pages.dev` — ≥ 1 facility marker for lead near Baltimore |
| CC-06 | Production smoke (T-03) | `BASE_URL=https://toxmap.pages.dev` — ≥ 1 facility marker for copper near Ely NV |
| CC-07 | Production smoke (T-08) | `BASE_URL=https://toxmap.pages.dev` — new tab with CDC ATSDR URL opens |

---

## 5. Entry & Exit Criteria

### Entry Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | Layer 4 contract tests passing | CI green |
| 2 | React app builds without errors | `npm run build` succeeds |
| 3 | React dev server starts | `npm run dev` serves `http://localhost:3000` |
| 4 | FastAPI starts | `uvicorn ... --port 8000` returns 200 on `/api/v1/meta` |
| 5 | PostGIS container running | `docker compose ps postgres` shows healthy |
| 6 | `playwright install chromium` completed | `playwright --version` returns version |
| 7 | All `data-testid` attributes in TEST_ID_REGISTRY.md present in React components | UI renders; `page.query_selector_all("[data-testid]")` > 0 |
| 8 | `seed.sql` loads without error | `psql -f seed.sql` returns 0 |

### Exit Criteria

| # | Criterion | Evidence |
|---|-----------|---------|
| 1 | All 3 smoke task scenarios (T-01, T-03, T-08) passing | `pytest tests/features/e2e/ -m smoke` — 0 failures |
| 2 | All 8 smoke invariants (1–4, 7–9, 11) passing | Same run |
| 3 | All 9 UCD task scenarios passing (Full) | `pytest tests/features/e2e/` — 0 failures on `main` |
| 4 | All 10 canonical UX invariants passing (Full) — item 11 in Feature 8 is a Phase 3 gate DoD item, not a standing invariant | Same run |
| 5 | Comma formatting confirmed: `"12,485"` and `"8,205"` | T-01 and T-03 passing |
| 6 | T-03 land-only medium assertion passes | T-03 chart bar assertion green |
| 7 | T-04 AVTEX EPA ID `VAD070358684` confirmed | T-04 Superfund detail assertion green |
| 8 | 0 critical/serious accessibility violations | CC-01 passing |
| 9 | Visual regression baselines committed | CC-02–CC-04 have snapshots in `tests/visual/snapshots/` |
| 10 | Tests deterministic across 3 consecutive runs | CI evidence |

### Deferred Scenarios

| Scenario | Reason | Target Phase |
|----------|--------|-------------|
| T-02 | Requires Superfund layer UI implementation | Phase 4 |
| T-04 | Same | Phase 4 |
| Invariant 6 | Requires distinct SVG markers for TRI vs. Superfund | Phase 4 |
| T-05, T-06, T-09 | Requires Demographics panel UI implementation | Phase 5 |
| T-07 | Requires state-restrict checkbox full implementation | Phase 5 |
| Invariants 5, 10 | Requires Demographics panel UI | Phase 5 |
| CC-01 (A11y) | Full axe scan requires complete UI | Phase 5 |
| CC-05–CC-07 (prod smoke) | Requires Cloudflare Pages deployment | Phase 5 |

---

## 6. Out of Scope

| Area | Reason |
|------|--------|
| Backend logic | Covered by Layer 3 Integration and Layer 4 Contract tests |
| MapLibre GL canvas pixel-level rendering | WebGL canvas is not testable via DOM assertions; visual regression (CC-02–04) covers static snapshots |
| Network throttling / slow 3G simulation | Separate performance test plan |
| Load testing | Separate performance test plan |
| Application log inspection | DOM state and response content are sufficient; log analysis is a developer concern |

---

## Appendix A — Automation Traceability

| Test ID | Scenario | Gherkin Section | File | Status |
|---------|----------|----------------|------|--------|
| E2E-01 | T-01: Lead near Sparrows Point | §Feature 7 T-01 | `ucd_task_scenarios.feature` | ❌ Phase 3 |
| E2E-02 | T-02: Superfund chemical list | §Feature 7 T-02 | `ucd_task_scenarios.feature` | ❌ Phase 4 |
| E2E-03 | T-03: Copper near Ely NV | §Feature 7 T-03 | `ucd_task_scenarios.feature` | ❌ Phase 3 |
| E2E-04 | T-04: AVTEX FIBERS Superfund | §Feature 7 T-04 | `ucd_task_scenarios.feature` | ❌ Phase 4 |
| E2E-05 | T-05: TRI + under-18 overlay | §Feature 7 T-05 | `ucd_task_scenarios.feature` | ❌ Phase 5 |
| E2E-06 | T-06: Income overlay | §Feature 7 T-06 | `ucd_task_scenarios.feature` | ❌ Phase 5 |
| E2E-07 | T-07: SC vs. national chlorine | §Feature 7 T-07 | `ucd_task_scenarios.feature` | ❌ Phase 5 |
| E2E-08 | T-08: ToxFAQ link | §Feature 7 T-08 | `ucd_task_scenarios.feature` | ❌ Phase 3 |
| E2E-09 | T-09: Benzene + cancer mortality | §Feature 7 T-09 | `ucd_task_scenarios.feature` | ❌ Phase 5 |
| E2E-10 | Invariant 1: Single sidebar | §Feature 8 Invariant 1 | `ux_invariants.feature` | ❌ Phase 3 |
| E2E-11 | Invariant 2: No empty rows | §Feature 8 Invariant 2 | `ux_invariants.feature` | ❌ Phase 3 |
| E2E-12 | Invariant 3: State restriction | §Feature 8 Invariant 3 | `ux_invariants.feature` | ❌ Phase 3 |
| E2E-13 | Invariant 4: Panel labels | §Feature 8 Invariant 4 | `ux_invariants.feature` | ❌ Phase 3 |
| E2E-14 | Invariant 5: Inline legend | §Feature 8 Invariant 5 | `ux_invariants.feature` | ❌ Phase 5 |
| E2E-15 | Invariant 6: Distinct icons | §Feature 8 Invariant 6 | `ux_invariants.feature` | ❌ Phase 4 |
| E2E-16 | Invariant 7: Latest year label | §Feature 8 Invariant 7 | `ux_invariants.feature` | ❌ Phase 3 |
| E2E-17 | Invariant 8: Comma formatting | §Feature 8 Invariant 8 | `ux_invariants.feature` | ❌ Phase 3 |
| E2E-18 | Invariant 9: Bottom close link | §Feature 8 Invariant 9 | `ux_invariants.feature` | ❌ Phase 3 |
| E2E-19 | Invariant 10: Disclaimer scope | §Feature 8 Invariant 10 | `ux_invariants.feature` | ❌ Phase 5 |
| E2E-20 | Invariant 11: Vintage label | §Feature 8 Invariant 11 | `ux_invariants.feature` | ❌ Phase 3 |
| E2E-21 | CC-01: A11y map page | — | `tests/a11y/test_wcag_compliance.py` | ❌ Phase 5 |
| E2E-22–24 | CC-02–04: Visual regression | — | `tests/visual/test_visual_regression.py` | ❌ Phase 5 |
| E2E-25–27 | CC-05–07: Production smoke | — | `tests/e2e_prod/test_smoke_prod.py` | ❌ Phase 5 |

---

## Appendix B — Page Object Model Reference

All POM classes live in `tests/e2e/pages/`. Full implementations in `e2e_steps.py`.

| Class | File | Key Methods |
|-------|------|------------|
| `MapPage` | `map_page.py` | `goto()`, `wait_for_map_load()`, `get_current_bounds()` |
| `SearchPanel` | `search_panel.py` | `fill_location(text)`, `fill_chemical(text)`, `select_year(year)`, `select_dataset(dataset)`, `submit()`, `check_limit_to_state()` |
| `ResultsTable` | `results_table.py` | `get_rows()`, `get_row_by_name(name)`, `click_row(name)`, `assert_no_empty_rows()` |
| `FacilityDetail` | `facility_detail.py` | `wait_for_open()`, `get_release_amount()`, `click_close_bottom()`, `get_atsdr_link()` |
| `SuperfundDetail` | `superfund_detail.py` | `wait_for_open()`, `get_epa_id()`, `get_contaminants()`, `get_epa_progress_link()` |
| `DemographicsPanel` | `demographics_panel.py` | `open()`, `select_layer(tab, sublayer)`, `clear_layer()`, `get_legend_entries()` |

---

## Appendix C — Run Commands

```bash
# Prerequisites: all services running (see §2 Test Architecture)
docker compose up -d postgres
uvicorn app.main:create_app --factory --port 8000 &
npm run dev &

# Install browsers (once)
playwright install chromium firefox webkit

# Smoke suite (every PR — T-01, T-03, T-08 + Invariants 1–4, 7–9, 11)
pytest tests/features/e2e/ -m smoke -v --browser chromium

# Full E2E suite (main branch)
pytest tests/features/e2e/ -v --browser chromium

# Specific task scenario
pytest tests/features/e2e/ -k "T_01" -v --browser chromium

# Cross-browser (sequential)
pytest tests/features/e2e/ -v --browser chromium --browser firefox

# Accessibility
pytest tests/a11y/ -v --browser chromium

# Production smoke (Cloudflare Pages)
TEST_MODE=prod BASE_URL=https://toxmap.pages.dev \
  pytest tests/e2e_prod/test_smoke_prod.py -m smoke -v --browser chromium

# With retry on flaky assertions
pytest tests/features/e2e/ -m smoke -v --browser chromium \
  --reruns 2 --reruns-delay 1
```

