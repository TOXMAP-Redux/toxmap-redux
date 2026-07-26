# Test Plan
## Service: `toxmap`

- **Author(s):** Victor Cannestro
- **Maintained By:** Quality Engineering Team
- **Version:** 1.0
- **Last Updated:** 2026-07-17
- **Test Type:** Contract Test (with real Event Hub analogue — HTTP as the event stream — DB, and OpenAPI schema interactions)

---

## Table of Contents
1. [Scope & Objectives](#1-scope--objectives)
2. [Test Architecture](#2-test-architecture)
3. [Test Data](#3-test-data)
4. [Test Scenarios](#4-test-scenarios)
5. [Test Data Variants](#5-test-data-variants)
6. [Entry & Exit Criteria](#6-entry--exit-criteria)
7. [Out of Scope](#7-out-of-scope)
8. [Appendix — Feature File Index](#appendix--feature-file-index)

---

## 1. Scope & Objectives

### Scope
This plan covers contract-level testing of all 17 TOXMAP API endpoints against three verification axes: (1) Gherkin BDD scenarios that assert exact response content, (2) Schemathesis property-based fuzzing that auto-generates edge-case requests and validates schema conformance, and (3) supplemental assertions on response headers, GeoJSON RFC 7946 compliance, performance SLAs, and OpenAPI spec freshness.

Tests treat each HTTP request as an "event" consumed by the API. The API's response is the observable output — analogous to a DB state change in an event-consumer pattern.

### Functionality Under Test

| Contract Axis          | Tool                            | Coverage                                                                        |
|------------------------|---------------------------------|---------------------------------------------------------------------------------|
| Explicit BDD scenarios | `pytest-bdd` + Gherkin features | 41 scenarios across 7 feature files (Features 1–9)                              |
| Property-based fuzzing | `schemathesis`                  | All 17 endpoints × all documented status codes; boundary values; type coercion  |
| Response headers       | Custom pytest suite             | `Content-Type`, `Content-Disposition`, error body structure                     |
| GeoJSON RFC 7946       | Custom pytest suite             | Coordinate order `[lon,lat]`, geometry non-null, `meta` envelope always present |
| Performance SLA        | `pytest-benchmark`              | p95 latency for key endpoints                                                   |
| OpenAPI drift          | `test_openapi_drift.py`         | Committed `openapi.json` matches live `/openapi.json`                           |

### Event-Consumer Analogy

```
"Event Published"                "Event Consumed"            "Outcome Asserted"
┌──────────────────┐            ┌─────────────────────┐     ┌──────────────────┐
│  HTTP Request    │            │  FastAPI endpoint   │     │  Response body   │
│  (pytest-bdd /   │───────────▶│  + PostGIS query    │────▶│  + status code   │
│   Schemathesis)  │            │  + service logic    │     │  + headers       │
└──────────────────┘            └─────────────────────┘     └──────────────────┘
     │                                     │                          │
  GET/POST + params               Business logic                JSON schema
  headers + body                  spatial queries               conformance
  (from feature files             color band, units             BDD assertions
   or auto-generated)
```

### Process Status Codes (HTTP)

| Code | Meaning          | Expected for                                             |
|------|------------------|----------------------------------------------------------|
| 200  | Success          | All valid requests that match seed data                  |
| 400  | Bad request      | `radius_miles > 500`; other business rule violations     |
| 404  | Not found        | Unknown `tri_facility_id` or `epa_id`                    |
| 422  | Validation error | Missing required params; type errors; enum violations    |
| 500  | Server error     | Must NEVER occur for any valid or boundary-value request |

---

## 2. Test Architecture

### Approach

Two complementary approaches run against the same seeded `toxmap_test` database:

**A. Gherkin BDD Scenarios (`pytest-bdd`)**
Step definitions in `tests/steps/api_steps.py` send requests via `FastAPI TestClient` and assert on response fields, matching the explicit scenarios defined in `TOXMAP_ACCEPTANCE_TESTS.md`.

**B. Schemathesis Fuzzing**
Reads `openapi.json` and generates hundreds of request combinations automatically. Validates that every response conforms to the declared OpenAPI schema.

```
[ tests/features/api/*.feature ]          [ openapi.json ]
│  Gherkin scenario parameters            │  Schemathesis reads spec
│                                         │  auto-generates edge cases
▼                                         ▼
[ FastAPI TestClient ]──────────────────▶[ FastAPI App ]
         │                                      │
         │  HTTP request                        │  Handles request
         ▼                                      ▼
[ API response ]                      [ /api/v1/* endpoints ]
         │                                      │
         ▼                                      ▼
[ BDD step assertions ]              [ Schemathesis schema validation ]
  status code, body fields,           response body conforms to
  content type, meta envelope         declared response schema
```

### Test Infrastructure

| Component            | Strategy                                                                              |
|----------------------|---------------------------------------------------------------------------------------|
| PostgreSQL + PostGIS | `postgis/postgis:16-3.4` — same as Layer 3                                            |
| Seed data            | `tests/fixtures/seed.sql` — loaded by `seed_db` fixture                               |
| API client           | `FastAPI TestClient` (BDD) + `schemathesis` HTTPX client (fuzzing)                    |
| OpenAPI spec         | Committed `openapi.json` at repo root; validated for drift by `test_openapi_drift.py` |
| Parallel execution   | **Disabled** (`-p no:xdist`) — seed data shared across function-scoped tests          |

### Polling & Timing
TOXMAP's API is synchronous — no polling required. Tests assert on the immediate HTTP response.

### Key Response Fields for Assertion

#### GeoJSON FeatureCollection Envelope (all spatial endpoints)

| Field                          | Assertion                                                     |
|--------------------------------|---------------------------------------------------------------|
| `type`                         | `"FeatureCollection"`                                         |
| `features`                     | JSON array (may be empty)                                     |
| `meta.total_count`             | Non-negative integer                                          |
| `meta.query`                   | Echo of request parameters                                    |
| Feature `geometry.coordinates` | `[longitude, latitude]` order per RFC 7946 — NOT `[lat, lon]` |
| Feature `geometry`             | Never `null` — null-geometry rows filtered server-side        |

#### Error Response (all 4xx/5xx)

| Field    | Assertion                                |
|----------|------------------------------------------|
| `detail` | Human-readable string                    |
| `code`   | Machine-readable code (where applicable) |

---

## 3. Test Data

BDD scenarios use the same `seed_db` fixture as Layer 3 Integration Tests. Fixture values are pulled from [TOXMAP_TEST_SEED_DATA.md §9 Known Good Assertion Values](TOXMAP_TEST_SEED_DATA.md).

Schemathesis fuzzing runs against the same seeded database; it generates its own request parameters from the OpenAPI spec and validates response schema conformance (not data correctness).

> ⚠️ **Date Maintenance:** If `year` parameter default is changed to "latest year dynamically", BDD fixtures using `year=2008` must be reviewed to ensure the seed remains current.

---

## 4. Test Scenarios

### 4.1 TRI Facility Search BDD — Feature 1 (14 scenarios)

**File:** `tests/features/api/facility_search.feature`  
**Step file:** `tests/steps/api_steps.py`  
**Full Gherkin:** [TOXMAP_ACCEPTANCE_TESTS.md §Feature 1](TOXMAP_ACCEPTANCE_TESTS.md)

| ID    | Scenario                                         | Key Assertion                                                             |
|-------|--------------------------------------------------|---------------------------------------------------------------------------|
| FS-01 | Radius search returns facilities within distance | `tri_facility_id="21219BTHLS3RD"` in features; `color_band` in valid enum |
| FS-02 | Radius excludes outside-radius facility          | `tri_facility_id="89319BHPCP7MILE"` NOT in 1-mile results                 |
| FS-03 | Chemical filter returns matching facilities      | `tri_facility_id="21219BTHLS3RD"`, `meta.chemical="LEAD COMPOUNDS"`       |
| FS-04 | Chemical filter no match — empty collection      | `features == []`; HTTP 200                                                |
| FS-05 | Medium filter land includes Robinson             | `tri_facility_id="89319BHPCP7MILE"` in features                           |
| FS-06 | Medium filter air excludes Robinson              | `tri_facility_id="89319BHPCP7MILE"` NOT in features                       |
| FS-07 | BBox scoping — all features within bbox          | Every feature coordinates within `[-76.6, 39.1, -76.3, 39.4]`             |
| FS-08 | No null names in result                          | Every feature has non-null `name` property                                |
| FS-09 | State restrict=true — VA only                    | Every feature `state_code=="VA"`                                          |
| FS-10 | State restrict=false — may include others        | Features from states other than VA possible                               |
| FS-11 | Facility detail — known ID                       | All required fields; `state_code=="MD"`, `naics_code=="331110"`           |
| FS-12 | Facility detail — unknown ID                     | HTTP 404; `"not found"` in `detail`                                       |
| FS-13 | Missing lat/lon                                  | HTTP 422                                                                  |
| FS-14 | `radius_miles` > 500                             | HTTP 400; `"radius"` in `detail`                                          |

### 4.2 Release Time Series BDD — Feature 2 (5 scenarios)

**File:** `tests/features/api/release_trends.feature`

| ID    | Scenario                               | Key Assertion                                                       |
|-------|----------------------------------------|---------------------------------------------------------------------|
| RT-01 | 15-year time series for Bethlehem      | Array; item with `reporting_year=2008`, `total_release_lbs=12485.0` |
| RT-02 | Medium filter — land only for Robinson | `land_release_lbs=8205.0` in 2008 item                              |
| RT-03 | Sparse years — no nulls                | No item has `total_release_lbs==null`                               |
| RT-04 | Largest release — SC chlorine          | `state_code="SC"`, `total_release_lbs=85000.0`                      |
| RT-05 | Largest release — nationwide chlorine  | `total_release_lbs>=85000.0`, `tri_facility_id="70663ENTGR0001"`    |

### 4.3 Chemical Search BDD — Feature 3 (5 scenarios)

**File:** `tests/features/api/chemicals.feature`

| ID    | Scenario                   | Key Assertion                                                                               |
|-------|----------------------------|---------------------------------------------------------------------------------------------|
| CH-01 | Full chemical list         | Contains items with `cas_number="71-43-2"` (BENZENE) and `cas_number="7664-41-7"` (AMMONIA) |
| CH-02 | Autocomplete partial match | `q=benz` → array with `name="BENZENE"`; count ≤ 10                                          |
| CH-03 | Autocomplete 1-char        | HTTP 422                                                                                    |
| CH-04 | Autocomplete no match      | `q=ZZZNOTACHEMICAL` → `[]`                                                                  |
| CH-05 | Autocomplete SLA           | Response time < 100ms                                                                       |

### 4.4 Superfund BDD — Feature 4 (5 scenarios)

**File:** `tests/features/api/superfund.feature`

| ID    | Scenario                    | Key Assertion                                                                                          |
|-------|-----------------------------|--------------------------------------------------------------------------------------------------------|
| SF-01 | Radius includes AVTEX       | `epa_id="VAD070358684"` in features                                                                    |
| SF-02 | Feature required properties | Every feature has `epa_id`, `name`, `hrs_score`, `status`, `contaminants`; `geometry.type=="Point"`    |
| SF-03 | Site detail — all fields    | `name="AVTEX FIBERS INC"`, `city="FRONT ROYAL"`, `contaminants` non-empty, `epa_progress_url` non-null |
| SF-04 | Chemical filter match       | `chemical=STYRENE` → includes AVTEX                                                                    |
| SF-05 | Outside radius — empty      | Remote coordinates → `features==[]`                                                                    |

### 4.5 Demographics BDD — Feature 5 (5 scenarios)

**File:** `tests/features/api/demographics.feature`

| ID    | Scenario                | Key Assertion                                                                        |
|-------|-------------------------|--------------------------------------------------------------------------------------|
| DM-01 | County GeoJSON for VA   | `FeatureCollection`; all features `Polygon` or `MultiPolygon`                        |
| DM-02 | Warren County under-18  | FIPS `51187` has `pct_under_18==24.7`; `meta.units.pct_under_18=="%"`                |
| DM-03 | Harris County income    | FIPS `48201` has `median_income > 0`; `meta.units.median_income=="$"`                |
| DM-04 | Census tract sub-county | All features FIPS starts with `"51187"`                                              |
| DM-05 | All units metadata keys | `meta.units` contains `pct_under_18`, `median_income`, `pct_over_65`, `pct_nonwhite`, `cancer_mortality_female_per_100k` |

### 4.6 CSV Export BDD — Feature 6 (3 scenarios)

**File:** `tests/features/api/export.feature`

| ID    | Scenario                       | Key Assertion                                                                       |
|-------|--------------------------------|-------------------------------------------------------------------------------------|
| EX-01 | Valid CSV with correct headers | `Content-Type: text/csv`; `Content-Disposition: attachment`; headers match contract |
| EX-02 | CSV contains correct data      | Row with `tri_facility_id="21219BTHLS3RD"` and `total_release_lbs=12485.0`          |
| EX-03 | Streaming response             | `Transfer-Encoding: chunked` OR `Content-Length` present                            |

### 4.7 Data Vintage BDD — Feature 9 (4 scenarios)

**File:** `tests/features/api/metadata.feature`

| ID    | Scenario                  | Key Assertion                                              |
|-------|---------------------------|------------------------------------------------------------|
| MT-01 | Valid schema              | All 6 required fields present; `source=="fastapi-dev"`     |
| MT-02 | Available years from seed | Contains `2006`, `2007`, `2008`                            |
| MT-03 | Latest year               | `latest_year==2008`                                        |
| MT-04 | Vintage fallback          | `vintage_label=="unknown"` (no ingestion metadata in seed) |

### 4.8 Schemathesis Fuzzing (SC-*)

**File:** `tests/contract/test_openapi_schema.py`

Schemathesis auto-generates test cases; these are enumerated categories, not individual scenario IDs.

| Category | What Schemathesis Generates                                                                 |
|----------|---------------------------------------------------------------------------------------------|
| SC-01    | All 17 endpoints × all documented status codes                                              |
| SC-02    | Required vs. optional parameter combinations                                                |
| SC-03    | Boundary values (min/max for numeric params: `radius_miles`, `year`, `limit`)               |
| SC-04    | Type coercion edge cases (string-as-number, empty string, special characters in `chemical`) |
| SC-05    | Response schema conformance — no extra/missing required fields                              |

### 4.9 Supplemental Contract Assertions (CA-*)

**Files:** `tests/contract/test_response_headers.py`, `test_geojson_rfc7946.py`, `test_performance_sla.py`, `test_openapi_drift.py`

| ID    | Concern                                 | Assertion                                                                     |
|-------|-----------------------------------------|-------------------------------------------------------------------------------|
| CA-01 | All non-export endpoints                | `Content-Type: application/json`                                              |
| CA-02 | CSV export endpoint                     | `Content-Type: text/csv`; `Content-Disposition: attachment; filename=...`     |
| CA-03 | All 4xx responses                       | `Content-Type: application/json`; body has `detail` key                       |
| CA-04 | All 5xx responses                       | Must not occur for any valid or boundary request                              |
| CA-05 | Coordinate order                        | All spatial endpoints return `[lon, lat]` per RFC 7946                        |
| CA-06 | GeoJSON structure                       | Every `Feature` has `type`, `geometry`, `properties`; `geometry` never `null` |
| CA-07 | `FeatureCollection.meta` always present | `meta` key in all spatial responses                                           |
| CA-08 | Facilities search SLA (radius)          | p95 < 500ms (10 repeated calls, `radius_miles=50`)                            |
| CA-09 | Chemical autocomplete SLA               | p95 < 100ms                                                                   |
| CA-10 | Viewport bbox re-fetch SLA              | p95 < 200ms (`bbox=` param on `GET /api/v1/facilities` — API contract SLA #2) |
| CA-11 | Superfund search SLA                    | p95 < 300ms (`GET /api/v1/superfund` radius ≤ 50mi)                           |
| CA-12 | CSV export first-byte SLA               | p95 < 1,000ms (`GET /api/v1/export/csv` time-to-first-byte)                   |
| CA-13 | Demographics county SLA                 | p95 < 400ms (`GET /api/v1/demographics/county?state=VA`)                      |
| CA-14 | OpenAPI drift                           | Committed `openapi.json` == `GET /openapi.json` live response                 |

---

## 5. Test Data Variants

The feature files in `tests/features/api/` represent the fixture variants for BDD contract testing. Each is a self-contained Gherkin scenario with inline fixture values.

| Feature File              | Scenarios | Date-Sensitive Fields                               |
|---------------------------|-----------|-----------------------------------------------------|
| `facility_search.feature` | 14        | `year=2008` parameter — update if seed years change |
| `release_trends.feature`  | 5         | `from_year`/`to_year` ranges — static 2006–2008     |
| `chemicals.feature`       | 5         | None                                                |
| `superfund.feature`       | 5         | None                                                |
| `demographics.feature`    | 5         | `census_year=2000` — static                         |
| `export.feature`          | 3         | `year=2008` — update if seed years change           |
| `metadata.feature`        | 4         | `latest_year=2008` assertion — derived from seed    |

> ⚠️ **Date Maintenance:** If seed data is updated to include newer TRI reporting years, the `year=2008` fixture parameters and `latest_year==2008` assertion in Feature 9 must be updated to match.

---

## 6. Entry & Exit Criteria

### Entry Criteria

| # | Criterion                                 | Verification                                                          |
|---|-------------------------------------------|-----------------------------------------------------------------------|
| 1 | Layer 3 integration tests passing         | CI green                                                              |
| 2 | FastAPI app starts without errors         | `uvicorn app.main:create_app --factory` returns 200 on `/api/v1/meta` |
| 3 | `openapi.json` committed to repo root     | `git ls-files openapi.json` returns file                              |
| 4 | `schemathesis` installed                  | `schemathesis --version` returns version                              |
| 5 | All 7 feature files present and parseable | `pytest --collect-only tests/features/api/` shows 41 scenarios        |

### Exit Criteria

| # | Criterion                                         | Evidence                                                            |
|---|---------------------------------------------------|---------------------------------------------------------------------|
| 1 | All 41 BDD API scenarios passing                  | `pytest tests/features/api/` — 0 failures                           |
| 2 | Schemathesis fuzzing produces 0 violations        | `schemathesis run http://localhost:8000/openapi.json` — exit code 0 |
| 3 | All supplemental contract assertions passing      | `pytest tests/contract/` — 0 failures (CA-01 through CA-14)              |
| 4 | OpenAPI drift check passing                       | `test_openapi_drift.py` green — CA-14                                      |
| 5 | Performance SLAs met for all 6 SLA-tested endpoints (CA-08 through CA-13) | `pytest-benchmark` report                                           |
| 6 | No `500 Internal Server Error` for any request    | Schemathesis output confirms                                        |

---

## 7. Out of Scope

| Area                                                                                      | Reason                                                                      |
|-------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| Browser-level rendering                                                                   | Covered by Layer 5 E2E Tests                                                |
| Load and stress testing                                                                   | Separate performance test plan                                              |
| Authentication / authorization                                                            | Not implemented in TOXMAP (open API)                                        |
| Production DuckDB WASM endpoints                                                          | No server-side endpoints in production; covered by Layer 5 production smoke |
| `/api/v1/layers/nuclear`, `/api/v1/layers/npri`, `/api/v1/layers/congressional-districts` | Optional layers — deferred until data pipeline implemented                  |
| `GET /api/v1/geocode` (endpoint 16)                                                       | Dev-only Nominatim proxy; SLA (< 500ms) tested implicitly in Layer 5 E2E via location-field input steps; isolated contract test is out of scope for Phase 2 |
| `GET /api/v1/export/map-metadata` (endpoint 15)                                          | Returns serialized filter state for map snapshot; no seed-state-independent assertions possible; delivered in Phase 3 alongside the search UI; verify in Phase 3 integration test |

---

## Appendix — Feature File Index

Full Gherkin text for all scenarios is in [TOXMAP_ACCEPTANCE_TESTS.md](TOXMAP_ACCEPTANCE_TESTS.md). Step implementation status by phase is in [test-step-coverage.md](test-step-coverage.md).

| Feature File              | Gherkin Section | Phase   | Step Status    |
|---------------------------|-----------------|---------|----------------|
| `facility_search.feature` | §Feature 1      | Phase 2 | 🔧 Stubs exist |
| `release_trends.feature`  | §Feature 2      | Phase 2 | ❌ Not started  |
| `chemicals.feature`       | §Feature 3      | Phase 2 | ❌ Not started  |
| `metadata.feature`        | §Feature 9      | Phase 2 | ❌ Not started  |
| `superfund.feature`       | §Feature 4      | Phase 4 | ❌ Not started  |
| `demographics.feature`    | §Feature 5      | Phase 5 | ❌ Not started  |
| `export.feature`          | §Feature 6      | Phase 3 | ❌ Not started  |

