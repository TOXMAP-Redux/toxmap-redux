# Test Plan
## Service: `toxmap`

- **Author(s):** Victor Cannestro
- **Maintained By:** Quality Engineering Team
- **Version:** 1.0
- **Last Updated:** 2026-07-17
- **Test Type:** Component Test (mocked repositories and network — no real database or browser)

---

## Table of Contents
1. [Scope & Objectives](#1-scope--objectives)
2. [Test Architecture](#2-test-architecture)
3. [Test Data](#3-test-data)
4. [Test Scenarios](#4-test-scenarios)
5. [Entry & Exit Criteria](#5-entry--exit-criteria)
6. [Out of Scope](#6-out-of-scope)
7. [Appendix A — Automation Traceability](#appendix-a--automation-traceability)

---

## 1. Scope & Objectives

### Scope
This plan covers component-level testing of TOXMAP's service layer (Python) and React component library (TypeScript). External dependencies — PostgreSQL, HTTP network calls, MapLibre GL canvas — are replaced with in-memory fakes or mock return values. Tests verify service contract behavior and component rendering contracts without requiring any running infrastructure.

### Functionality Under Test

**Backend Services (Python / `tests/component/backend/`)**

| Service | File | What is Tested |
|---------|------|----------------|
| `FacilityService` | `test_facility_service.py` | Color band assignment, bbox scoping, null geometry exclusion, state filter routing, truncation flag |
| `ChemicalService` | `test_chemical_service.py` | Autocomplete min-length guard, 10-result cap, case-insensitivity, sorted list |
| `ReleaseService` | `test_release_service.py` | Sparse-year omission, medium filter routing, state vs. nationwide query routing |
| `ExportService` | `test_export_service.py` | CSV header contract, row count, float precision, streaming response type |
| `MetaService` | `test_meta_service.py` | Vintage fallback, available years derivation, latest year, facility count |

**Frontend Components (TypeScript / `src/__tests__/component/`)**

| Component | File | What is Tested |
|-----------|------|----------------|
| `<SearchPanel>` | `SearchPanel.test.tsx` | Labels, submit state, autocomplete debounce, year label, dataset radio |
| `<Sidebar>` | `Sidebar.test.tsx` | Mutual-exclusion panel visibility, `data-active` toggle |
| `<ResultsTable>` | `ResultsTable.test.tsx` | Comma formatting, no empty rows, `data-facility-id` attribute |
| `<FacilityDetailPanel>` | `FacilityDetailPanel.test.tsx` | Comma formatting, bottom close link, ATSDR link presence |
| `<DemographicLegend>` | `DemographicLegend.test.tsx` | Inline legend (no hover), unit symbols, ≥3 entries |
| `<CoOccurrenceDisclaimer>` | `CoOccurrenceDisclaimer.test.tsx` | Visibility scoped to mortality tab only |
| `<DataVintageLabel>` | `DataVintageLabel.test.tsx` | Non-null, non-empty, `"unknown"` fallback |

### Two-Phase Test Flow

```
Phase 1: Mock Setup + Invoke            Phase 2: Assert
┌──────────────────────────┐           ┌──────────────────────────┐
│  AsyncMock / vi.mock()   │           │  Return object fields    │
│  configure return values │──────────▶│  DOM element presence    │
│  service.method() /      │           │  Rendered text content   │
│  React render(props)     │           │  Event handler calls     │
└──────────────────────────┘           └──────────────────────────┘
```

---

## 2. Test Architecture

### Backend Approach
Mock `*Repository` classes using `unittest.mock.AsyncMock` to return pre-built dataclass objects. Call the service method directly. Assert on the returned object.

```
[ AsyncMock(FacilityRepository) ]
│  returns: [FacilityRow(id=1, location=POINT(...), ...)]
│
│  (call service method)
▼
[ FacilityService.search(params) ]
│
│  (returns GeoJSON FeatureCollection)
▼
[ assert features[0].properties["color_band"] == "orange" ]
```

### Frontend Approach
Use `@testing-library/react` `render()` with controlled props. Mock HTTP calls via MSW (Mock Service Worker). Assert on DOM via `screen.getBy*` queries.

```
[ msw server: GET /api/v1/chemicals/search → mock JSON ]
│
│  render(<SearchPanel availableYears={[2006,2007,2008]} />)
▼
[ DOM: [data-testid="year-select"] ]
│
│  assert option text contains "(latest year)"
▼
[ test passes ]
```

### Test Infrastructure

| Component | Strategy |
|-----------|----------|
| Backend repository mocking | `unittest.mock.AsyncMock` for async repo methods |
| Frontend HTTP mocking | `msw` (Mock Service Worker) — intercepts `fetch` calls in JSDOM |
| Frontend DOM environment | `Vitest` with `environment: "jsdom"` |
| No real DB or network | All external calls are intercepted |

### Test Execution Lifecycle

```
BEFORE_EACH (backend)
└─ Instantiate service with AsyncMock repository

BEFORE_EACH (frontend)
└─ msw server.resetHandlers() to clear per-test overrides

TEST
├─ Setup: configure mock return values / render component with props
├─ Act: call service method / fire user events
└─ Assert: inspect return value / query DOM

AFTER_EACH (frontend)
└─ cleanup() (automatic via @testing-library/react)
```

---

## 3. Test Data

### Backend Mock Data
Mock repositories return in-memory `FacilityRow`, `ReleaseRow`, `ChemicalRow` objects. Values are chosen to exercise specific code paths (e.g., `total_release_lbs=12485.0` to assert `color_band=="orange"`).

### Frontend Mock Responses
MSW handlers return minimal JSON matching the shapes in [TOXMAP_API_CONTRACT.md](../api/TOXMAP_API_CONTRACT.md). Fixture values reference [TOXMAP_TEST_SEED_DATA.md §9](TOXMAP_TEST_SEED_DATA.md) for known-good assertion values.

> ⚠️ **Date Maintenance:** Not applicable — component tests contain no date-sensitive SQL fixtures.

---

## 4. Test Scenarios

### 4.1 FacilityService — Mocked Repository

**File:** `tests/component/backend/test_facility_service.py`
**Prefix:** `FSV` (FacilityService)

| ID     | Scenario                | Mock Setup                                         | Assertion                                          |
|--------|-------------------------|----------------------------------------------------|----------------------------------------------------|
| FSV-01 | Color band assignment   | Repo returns row with `total_release_lbs=12485.0`  | `feature.properties["color_band"] == "orange"`     |
| FSV-02 | BBox scoping            | Repo returns features; service applies bbox filter | Only features within bbox in result                |
| FSV-03 | Null geometry exclusion | Repo returns mix of rows with and without location | Null-geometry rows absent from GeoJSON output      |
| FSV-04 | State restrict = `True` | —                                                  | Repo called with `state` parameter                 |
| FSV-05 | State restrict = `False`| —                                                  | Repo called without `state` parameter              |
| FSV-06 | Truncation flag         | Repo returns `limit+1` rows                        | `meta.truncated == True`, result capped at `limit` |
| FSV-07 | Empty result            | Repo returns `[]`                                  | `{"type":"FeatureCollection","features":[]}`       |

### 4.2 ChemicalService — Mocked Repository

**File:** `tests/component/backend/test_chemical_service.py`
**Prefix:** `CSV` (Chemical SerVice)

> ⚠️ **Naming note for agents:** The `CSV` prefix here stands for **Chemical SerVice**, NOT comma-separated values. CSV export tests live in §4.4 (prefix `XSV`). Do not confuse the two.

| ID     | Scenario                    | Mock Setup                 | Assertion                                                     |
|--------|-----------------------------|----------------------------|---------------------------------------------------------------|
| CSV-01 | Autocomplete returns max 10 | Repo returns 15 items      | Service result has ≤ 10 items                                 |
| CSV-02 | Case-insensitive match      | Query `"lead"`             | Repo called with normalized query; returns `"LEAD COMPOUNDS"` |
| CSV-03 | Full list sorted            | Repo returns unsorted list | Service result is alphabetically sorted                       |
| CSV-04 | Min-length guard            | Query `"b"` (1 char)       | `ValueError` raised before repo is called                     |

### 4.3 ReleaseService — Mocked Repository

**File:** `tests/component/backend/test_release_service.py`
**Prefix:** `RSV` (ReleaseSerVice)

| ID     | Scenario              | Mock Setup                        | Assertion                                                   |
|--------|-----------------------|-----------------------------------|-------------------------------------------------------------|
| RSV-01 | Sparse-year omission  | Repo returns only years with data | No zero-filled entries in result                            |
| RSV-02 | Medium filter routing | `medium="land"` parameter         | Repo called with land-only filter; total reflects land only |
| RSV-03 | State filter routing  | `state="SC"`                      | Repo called with state parameter                            |
| RSV-04 | Nationwide query      | No `state` parameter              | Repo called without state filter                            |

### 4.4 ExportService — Mocked Repository, In-Memory CSV

**File:** `tests/component/backend/test_export_service.py`
**Prefix:** `XSV` (eXport SerVice)

| ID     | Scenario                   | Mock Setup                          | Assertion                                                                        |
|--------|----------------------------|-------------------------------------|----------------------------------------------------------------------------------|
| XSV-01 | CSV headers match contract | Repo returns 1 row                  | First line == column list from [API Contract §15](../api/TOXMAP_API_CONTRACT.md) |
| XSV-02 | Row count                  | Repo returns N rows                 | N data rows in CSV (excluding header)                                            |
| XSV-03 | Float precision            | Row with `total_release_lbs=12485.0`| `"12485.0"` in CSV (not `"12484.9999..."`)                                       |
| XSV-04 | Streaming response type    | Any repo result                     | Returns `StreamingResponse`, not `Response`                                      |

### 4.5 MetaService — Mocked Query Result

**File:** `tests/component/backend/test_meta_service.py`
**Prefix:** `MSV` (MetaSerVice)

| ID     | Scenario               | Mock Setup                              | Assertion                                              |
|--------|------------------------|-----------------------------------------|--------------------------------------------------------|
| MSV-01 | Vintage fallback       | No ingestion record in mock             | `vintage_label == "unknown"`                           |
| MSV-02 | Available years sorted | Mock returns years `[2008, 2006, 2007]` | `available_years == [2006, 2007, 2008]`                |
| MSV-03 | `latest_year` is max   | Mock years `[2006, 2007, 2008]`         | `latest_year == 2008`                                  |
| MSV-04 | Facility count         | Mock returns count `7`                  | `total_facility_count == 7`                            |

### 4.6 `<SearchPanel>` — UX Contract

**File:** `src/__tests__/component/SearchPanel.test.tsx`
**Prefix:** `SP` (Search Panel)

| ID    | Scenario                        | Assertion                                                                                           | UX Invariant |
|-------|---------------------------------|-----------------------------------------------------------------------------------------------------|--------------|
| SP-01 | Panel label                     | "Search Chemical Releases by Location" visible; "Quick Search" absent                               | Invariant 4  |
| SP-02 | Submit disabled without geocode | `search-submit-btn` is `disabled`                                                                   | —            |
| SP-03 | Autocomplete fires at ≥ 2 chars | `onChemicalSearch` called; 1-char input produces no call                                            | —            |
| SP-04 | Latest year label               | Option text includes `"(latest year)"`                                                              | Invariant 7  |
| SP-05 | Dataset switch                  | `onDatasetChange` called with `"superfund"`                                                         | —            |
| SP-06 | `data-testid` presence          | All interactive elements have correct `data-testid` per [TEST_ID_REGISTRY.md](TEST_ID_REGISTRY.md) | —            |

### 4.7 `<Sidebar>`

**File:** `src/__tests__/component/Sidebar.test.tsx`
**Prefix:** `SB` (SideBar)

| ID    | Scenario                              | Assertion                                | UX Invariant |
|-------|---------------------------------------|------------------------------------------|--------------|
| SB-01 | Single panel at mount                 | `[data-active="true"]` count == 1        | Invariant 1  |
| SB-02 | Search results hides map contents     | Map Contents panel `not.toBeVisible()`   | Invariant 1  |
| SB-03 | Map contents hides search results     | Search Results panel `not.toBeVisible()` | Invariant 1  |

### 4.8 `<ResultsTable>`

**File:** `src/__tests__/component/ResultsTable.test.tsx`
**Prefix:** `TBL` (TaBLe)

| ID     | Scenario                     | Assertion                                                  | UX Invariant |
|--------|------------------------------|------------------------------------------------------------|--------------|
| TBL-01 | Comma formatting             | `"12,485"` in `results-row-release` text                   | Invariant 8  |
| TBL-02 | No empty rows                | Zero `results-row` elements with empty children            | Invariant 2  |
| TBL-03 | `data-facility-id` attribute | Each row has correct `data-facility-id` value              | —            |
| TBL-04 | Empty state                  | Zero `results-row` elements + optional empty-state message | Invariant 2  |

### 4.9 `<FacilityDetailPanel>`

**File:** `src/__tests__/component/FacilityDetailPanel.test.tsx`
**Prefix:** `FDP` (Facility Detail Panel)

| ID     | Scenario             | Assertion                                                             | UX Invariant |
|--------|----------------------|-----------------------------------------------------------------------|--------------|
| FDP-01 | Comma formatting     | `"12,485"` in `facility-release-amount`                               | Invariant 8  |
| FDP-02 | Close link at bottom | `popup-close-bottom` is the last focusable element in DOM order       | Invariant 9  |
| FDP-03 | ATSDR link with URL  | `atsdr-link` present with correct `href` + `rel="noopener noreferrer"`| —            |
| FDP-04 | ATSDR link absent    | `atsdr-link` not in DOM when `atsdr_url == null`                      | —            |

### 4.10 `<DemographicLegend>`, `<CoOccurrenceDisclaimer>`, `<DataVintageLabel>`

**Files:** `DemographicLegend.test.tsx` · `CoOccurrenceDisclaimer.test.tsx` · `DataVintageLabel.test.tsx`
**Prefixes:** `DLG` (Demographic LeGend) · `COD` (CO-occurrence Disclaimer) · `DVL` (Data Vintage Label)

| ID     | Component                  | Scenario              | Assertion                                       | UX Invariant |
|--------|----------------------------|-----------------------|-------------------------------------------------|--------------|
| DLG-01 | `<DemographicLegend>`      | Inline entries (no hover) | `demographic-legend-entry` visible without `hover()` | Invariant 5 |
| DLG-02 | `<DemographicLegend>`      | Unit symbols          | `%` or `$` in every entry text                  | Invariant 5  |
| DLG-03 | `<DemographicLegend>`      | Minimum entries       | Count ≥ 3                                       | Invariant 5  |
| COD-01 | `<CoOccurrenceDisclaimer>` | Mortality tab         | `cooccurrence-disclaimer` visible               | Invariant 10 |
| COD-02 | `<CoOccurrenceDisclaimer>` | Population tab        | `cooccurrence-disclaimer` NOT in DOM            | Invariant 10 |
| COD-03 | `<CoOccurrenceDisclaimer>` | Income tab            | `cooccurrence-disclaimer` NOT in DOM            | Invariant 10 |
| COD-04 | `<CoOccurrenceDisclaimer>` | Text contract         | Contains "Correlation does not imply causation" | Invariant 10 |
| DVL-01 | `<DataVintageLabel>`       | Non-null text         | `data-vintage-label` visible, non-empty, not `"null"` | Invariant 11 |
| DVL-02 | `<DataVintageLabel>`       | `"unknown"` fallback  | No crash; shows fallback string                 | Invariant 11 |

---

## 5. Entry & Exit Criteria

### Entry Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | Layer 1 unit tests passing | CI green |
| 2 | Service code reviewed and merged | PR approved |
| 3 | React components rendered without console errors | `npm run lint` passes |
| 4 | `msw` handlers configured for mocked API routes | `src/mocks/handlers.ts` present |

### Exit Criteria

| # | Criterion | Evidence |
|---|-----------|---------|
| 1 | All backend service scenarios (FSV-*, CSV-*, RSV-*, XSV-*, MSV-*) passing | `pytest tests/component/` reports 0 failures |
| 2 | All React component scenarios passing | `npm run test:component` reports 0 failures |
| 3 | All UX invariants covered have corresponding component tests | §4.6–4.10 traceability complete |
| 4 | `app/services/` line coverage ≥ **90%** | `pytest-cov` report |
| 5 | `src/components/` line coverage ≥ **75%** | Vitest coverage report |
| 6 | No P1/P2 defects open | Defect tracker |

---

## 6. Out of Scope

| Area | Reason |
|------|--------|
| Real PostGIS queries | Covered by Layer 3 Integration Tests |
| HTTP routing and middleware | Covered by Layer 3 Integration Tests |
| Browser rendering of MapLibre GL | Covered by Layer 5 E2E Tests |
| Geocoding API calls | Covered by Layer 5 E2E Tests (real geocode) or Layer 3 (mocked) |
| `app/repositories/` query SQL | Covered by Layer 3 Integration Tests against real PostGIS |

---

## Appendix A — Automation Traceability

| Test ID | Scenario ID       | Description                                    | File                           | Status     |
|---------|-------------------|------------------------------------------------|--------------------------------|------------|
| CT-01   | FSV-01            | Color band applied in FacilityService          | `test_facility_service.py`     | ⚠️ Planned |
| CT-02   | FSV-02–FSV-03     | BBox scoping, null geometry exclusion          | `test_facility_service.py`     | ⚠️ Planned |
| CT-03   | FSV-04–FSV-05     | State filter routing                           | `test_facility_service.py`     | ⚠️ Planned |
| CT-04   | FSV-06–FSV-07     | Truncation flag, empty result                  | `test_facility_service.py`     | ⚠️ Planned |
| CT-05   | CSV-01–CSV-04     | ChemicalService scenarios                      | `test_chemical_service.py`     | ⚠️ Planned |
| CT-06   | RSV-01–RSV-04     | ReleaseService scenarios                       | `test_release_service.py`      | ⚠️ Planned |
| CT-07   | XSV-01–XSV-04     | ExportService scenarios                        | `test_export_service.py`       | ⚠️ Planned |
| CT-08   | MSV-01–MSV-04     | MetaService scenarios                          | `test_meta_service.py`         | ⚠️ Planned |
| CT-09   | SP-01–SP-06       | `<SearchPanel>` contract                       | `SearchPanel.test.tsx`         | ⚠️ Planned |
| CT-10   | SB-01–SB-03       | `<Sidebar>` mutual exclusion                   | `Sidebar.test.tsx`             | ⚠️ Planned |
| CT-11   | TBL-01–TBL-04     | `<ResultsTable>` formatting + empty state      | `ResultsTable.test.tsx`        | ⚠️ Planned |
| CT-12   | FDP-01–FDP-04     | `<FacilityDetailPanel>` formatting + close     | `FacilityDetailPanel.test.tsx` | ⚠️ Planned |
| CT-13   | DLG-01–DLG-03     | `<DemographicLegend>` inline legend            | `DemographicLegend.test.tsx`   | ⚠️ Planned |
| CT-14   | COD-01–COD-04     | `<CoOccurrenceDisclaimer>` scope               | `CoOccurrenceDisclaimer.test.tsx` | ⚠️ Planned |
| CT-15   | DVL-01–DVL-02     | `<DataVintageLabel>` fallback                  | `DataVintageLabel.test.tsx`    | ⚠️ Planned |
