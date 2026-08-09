# Export Feature Plan

**Version:** 1.0 · **Date:** 2026-08-08 · **Status:** Planning

> **Context:** This document outlines the full scope of data export functionality for TOXMAP Redux.
> The original NLM TOXMAP (2013–2019) supported CSV export and map image screenshots. This plan
> implements equivalent functionality using the modern stack (React + FastAPI + DuckDB WASM).

---

## 1. Current State

### 1.1 What Exists ✅

| Component | Status | Story | Notes |
|-----------|--------|-------|-------|
| `GET /api/v1/export/csv` | ✅ Shipped | 2.6.2 | Streaming CSV, chunked transfer, correct headers |
| `GET /api/v1/export/map-metadata` | ✅ Shipped | 2.6.3 | JSON with `export_filename` + query state |
| API tests | ✅ Passing | — | `tests/features/api/export.feature` |
| DuckDB WASM CSV export hook | 🔲 Placeholder | 7.1.7 | Story exists but frontend hook not implemented |

### 1.2 What's Missing ❌

| Feature | Why It's Needed | Priority |
|---------|----------------|----------|
| **Search results "Download CSV" button** | Users can't trigger CSV export from UI | P1 |
| **Facility detail export (single facility)** | Export one facility's release data | P2 |
| **Map image screenshot** | Print/share map view | P3 |
| **Superfund contaminant list export** | Export contaminants for a site | P3 |

---

## 2. Proposed Phase: Phase X.EXPORT

> **Recommended placement:** After Phase 7 (DuckDB WASM production deployment), as a Phase 8+ enhancement.
> The DuckDB WASM path (story 7.1.7) already plans CSV export; this phase completes the UI.

**Duration:** ~1 week  
**Team:** FE (lead), QA, SEC

### 2.1 User Stories (Product Perspective)

| ID | As a... | I want to... | So that... |
|----|---------|-------------|------------|
| EXP-01 | Concerned citizen | Download my search results as a CSV | I can analyze the data in Excel/Sheets |
| EXP-02 | Public health researcher | Export a single facility's release history | I can cite specific release data |
| EXP-03 | Community organizer | Save a screenshot of my current map view | I can share it in presentations |
| EXP-04 | Environmental journalist | Export a Superfund site's contaminant list | I can reference specific hazardous substances |

---

## 3. Stories by Agent Role

### 3.1 Frontend Engineer (FE)

**Epic X.1 — Search Results Export UI**

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| X.1.1 | Add "Download CSV" button below ResultsTable | 2 | Button appears when results exist; disabled when no results; `data-testid="export-csv-btn"` |
| X.1.2 | Wire button to `GET /api/v1/export/csv` with current search params | 2 | Click triggers browser download; filename matches pattern `toxmap-{chemical}-{year}-{date}.csv` |
| X.1.3 | DuckDB WASM export path: client-side CSV generation from Parquet | 3 | When `VITE_DATA_SOURCE=duckdb`, CSV generated client-side; same column headers as API contract §14 |
| X.1.4 | Loading state: button shows spinner while generating large CSV | 1 | No double-click; spinner visible during async operation |
| X.1.5 | Error handling: toast message if export fails | 1 | User sees "Export failed" toast; console logs full error |

**Epic X.2 — Facility Detail Export**

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| X.2.1 | Add "Export" icon button to FacilityDrawer header | 1 | Icon button (download icon) next to facility name; `data-testid="facility-export-btn"` |
| X.2.2 | Export single facility: CSV with all release years for that TRI ID | 2 | Downloads `toxmap-{tri_id}-{date}.csv` with columns: `year,chemical,total_lbs,air_lbs,water_lbs,land_lbs` |
| X.2.3 | Include chart data in export: top chemicals, medium breakdown, trend | 3 | Single CSV with three sections separated by blank rows; or offer "Export which chart?" dropdown |

**Epic X.3 — Superfund Export**

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| X.3.1 | Add "Export Contaminants" button to SuperfundDrawer | 1 | Button below contaminant list; `data-testid="superfund-export-btn"` |
| X.3.2 | CSV export: site name, EPA ID, contaminant name, CAS number, ATSDR URL | 2 | Downloads `superfund-{epa_id}-contaminants-{date}.csv` |

**Epic X.4 — Map Screenshot**

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| X.4.1 | Add "Save Map Image" button to map controls or toolbar | 2 | Button with camera/image icon; `data-testid="save-map-btn"` |
| X.4.2 | Use `map.getCanvas().toDataURL()` for PNG export | 2 | Downloads `toxmap-map-{timestamp}.png`; includes markers but NOT UI overlays |
| X.4.3 | Embed current search params in PNG metadata (optional) | 1 | EXIF/comment metadata includes lat, lon, radius, chemical |
| X.4.4 | Attribution watermark required by OpenStreetMap license | 2 | "© OpenStreetMap contributors" rendered on exported image |

**Points Total (FE):** 25 points

---

### 3.2 Backend Engineer (BE)

> **Note:** Backend export endpoints already exist (stories 2.6.2, 2.6.3). Additional BE work is only required if new endpoints are needed.

**Epic X.5 — Facility History Export Endpoint (Optional)**

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| X.5.1 | `GET /api/v1/facilities/{id}/export/csv`: all release years for one facility | 2 | Returns CSV with `year,chemical_name,total_release_lbs,...` for all years in DB |
| X.5.2 | Query params: `start_year`, `end_year` for filtering range | 1 | `?start_year=2010&end_year=2020` returns only those years |

**Epic X.6 — Superfund Contaminant Export Endpoint (Optional)**

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| X.6.1 | `GET /api/v1/superfund/{id}/contaminants/export/csv` | 2 | Returns CSV: `contaminant_name,cas_number,atsdr_url,pubchem_url` |

**Points Total (BE):** 5 points (optional — FE can construct client-side from existing data)

---

### 3.3 Quality Engineer (QA)

**Epic X.7 — Export Feature Tests**

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| X.7.1 | Gherkin scenario: CSV export button triggers download | 2 | `tests/features/e2e/export.feature` — Given results, When click Download CSV, Then file downloads |
| X.7.2 | Verify CSV headers match API contract §14 | 2 | Column order: `tri_facility_id,name,address,...` exactly as documented |
| X.7.3 | Verify CSV content: at least one row with `89319BHPCP7MILE` | 2 | Seed facility appears in export; validates data integrity |
| X.7.4 | Accessibility: button has `aria-label`, keyboard accessible | 1 | Tab to button, Enter triggers download |
| X.7.5 | Map screenshot E2E test | 2 | Verify PNG downloads; file size > 10KB (not empty) |
| X.7.6 | DuckDB WASM export parity test | 3 | CSV from `VITE_DATA_SOURCE=duckdb` has same columns/headers as API path |

**Points Total (QA):** 12 points

---

### 3.4 Security Engineer (SEC)

**Epic X.8 — Export Security Review**

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| X.8.1 | CSV injection audit: ensure no formula execution in Excel | 2 | Values starting with `=`, `+`, `-`, `@` prefixed with single quote; test with LibreOffice Calc |
| X.8.2 | Filename sanitization: `Content-Disposition` header uses safe filename | 1 | No path traversal (`../`); no special chars except `-_` |
| X.8.3 | Rate limiting applies to export endpoints | 1 | `/api/v1/export/csv` respects 60 req/min limit (story 2.8.2) |
| X.8.4 | No PII in exports | 1 | Verify CSV contains only facility/chemical data; no user IDs, IPs, session tokens |

**Points Total (SEC):** 5 points

---

### 3.5 DevOps Engineer (OPS)

**Epic X.9 — Export Infrastructure (if needed)**

| Story | Description | Points | Acceptance Criteria |
|-------|-------------|--------|---------------------|
| X.9.1 | Cloudflare Pages: verify large CSV downloads work via R2 | 1 | 50MB CSV downloads without timeout on Cloudflare free tier |
| X.9.2 | CDN cache headers: exports are not cached (dynamic data) | 1 | `Cache-Control: no-store` on `/api/v1/export/*` responses |

**Points Total (OPS):** 2 points

---

## 4. Technical Design Notes

### 4.1 CSV Generation (Two Paths)

**Path A — API Mode (dev, docker-compose):**
```
User clicks "Download CSV"
  → fetch(`/api/v1/export/csv?${searchParams}`)
  → StreamingResponse from FastAPI
  → Browser downloads file
```

**Path B — DuckDB WASM Mode (production, Cloudflare):**
```
User clicks "Download CSV"
  → DuckDB WASM query against Parquet
  → JavaScript generates CSV string
  → Blob + URL.createObjectURL + anchor click
  → Browser downloads file
```

### 4.2 Map Screenshot Implementation

```typescript
// MapLibre GL JS canvas export
const canvas = map.getCanvas()
const dataUrl = canvas.toDataURL('image/png')

// Add attribution watermark (required by OSM license)
const withAttribution = await addWatermark(dataUrl, '© OpenStreetMap contributors')

// Trigger download
const link = document.createElement('a')
link.href = withAttribution
link.download = `toxmap-map-${Date.now()}.png`
link.click()
```

### 4.3 CSV Header Contract

Per API Contract §14, CSV columns MUST be in this exact order:

```
tri_facility_id,name,address,city,state_code,naics_code,chemical_name,cas_number,reporting_year,total_release_lbs,air_release_lbs,water_release_lbs,land_release_lbs,underground_release_lbs,unit_of_measure,form_type
```

Both API and DuckDB WASM paths MUST produce identical headers.

---

## 5. UI Mockup Guidance

### 5.1 Search Results Export Button

```
┌─────────────────────────────────────┐
│ Results (47 facilities)      [⬇️ CSV] │
├─────────────────────────────────────┤
│ BHP COPPER - 7 MILE        8,205 lbs │
│ KENNECOTT UTAH COPPER      5,432 lbs │
│ ...                                  │
└─────────────────────────────────────┘
```

- Button: outlined style, download icon + "CSV" text
- Position: right side of results header row
- State: disabled + grayed when `results.length === 0`

### 5.2 Facility Drawer Export

```
┌─────────────────────────────────────────┐
│ BHP COPPER - 7 MILE        [📥] [✕] │
├─────────────────────────────────────────┤
│ [Top Chemicals] [By Medium] [Trend]    │
│ ...                                     │
└─────────────────────────────────────────┘
```

- Icon button (📥 or similar) next to close button
- Tooltip: "Export facility data"

### 5.3 Map Screenshot Button

Position: Map controls cluster (top-right, near zoom buttons)

```
[+]
[−]
[🧭]  ← compass
[📷]  ← screenshot (new)
```

---

## 6. Definition of Done

- [ ] "Download CSV" button visible in ResultsTable header
- [ ] CSV downloads successfully with correct filename and headers
- [ ] DuckDB WASM export produces identical CSV structure
- [ ] Facility detail export works from drawer
- [ ] Map screenshot saves PNG with attribution
- [ ] All QA scenarios pass: `pytest tests/features/e2e/export.feature`
- [ ] SEC audit complete: no CSV injection, safe filenames
- [ ] Lighthouse accessibility score ≥ 90 with export buttons

---

## 7. Dependencies & Blockers

| Dependency | Status | Notes |
|------------|--------|-------|
| Phase 7 DuckDB WASM integration | ✅ Complete | Story 7.1.7 provides foundation |
| `/api/v1/export/csv` endpoint | ✅ Complete | Story 2.6.2 shipped |
| ResultsTable component | ✅ Complete | Story 3.5.x shipped |
| FacilityDrawer component | ✅ Complete | Story 3.4.x shipped |

**No blockers** — export UI can proceed independently.

---

## 8. Estimated Effort

| Role | Points | Estimated Days |
|------|--------|---------------|
| FE | 25 | 3–4 days |
| BE | 5 (optional) | 0.5 days |
| QA | 12 | 1.5 days |
| SEC | 5 | 0.5 days |
| OPS | 2 | 0.5 days |
| **Total** | **49** | **~6 days** |

---

## 9. Gherkin Scenarios (Draft)

```gherkin
# tests/features/e2e/export.feature

Feature: Data Export
  As a user researching environmental data
  I want to export search results and facility details
  So that I can analyze the data offline

  @EXP-01
  Scenario: Download search results as CSV
    Given I have searched for "copper" near "Ruth, NV"
    And the results table shows at least 1 facility
    When I click the "Download CSV" button
    Then a file downloads with name matching "toxmap-copper-*.csv"
    And the CSV has header row starting with "tri_facility_id"
    And the CSV contains a row with "89319BHPCP7MILE"

  @EXP-02
  Scenario: Export single facility data
    Given I have opened the facility drawer for "BHP COPPER"
    When I click the facility export button
    Then a file downloads with name matching "toxmap-89319BHPCP7MILE-*.csv"
    And the CSV contains release data for multiple years

  @EXP-03
  Scenario: Save map screenshot
    Given I am viewing the map with facilities visible
    When I click the "Save Map Image" button
    Then a PNG file downloads
    And the file size is greater than 10KB
    And the filename matches "toxmap-map-*.png"

  @EXP-04
  Scenario: Export button disabled when no results
    Given I have not performed a search
    Then the "Download CSV" button is disabled
    And the button has aria-disabled="true"
```

---

## 10. Open Questions

1. **Multi-format export?** Should we offer JSON alongside CSV?
2. **Export limits?** Cap at 10,000 rows to prevent abuse?
3. **Superfund priority?** Is superfund export P2 or P3?
4. **Mobile screenshot?** Map screenshot on touch devices?

---

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-08-08 | 1.0 | Agent | Initial planning document |
| 2026-08-08 | 1.1 | Agent | Implementation complete; defect fixes documented |

---

## Appendix A: Implementation Notes (2026-08-08)

### A.1 What Was Implemented

**Frontend (`frontend/src/api/export.ts`):**
- `exportFacilitiesCsv(params)` — Search results CSV export
- `exportSingleFacilityCsv(triId)` — Single facility release history export
- `exportSuperfundContaminantsCsv(epaId, siteName)` — Superfund contaminant list export
- `exportMapImage(mapCanvas)` — Map PNG screenshot with attribution watermark
- `escapeCsvField(value)` — CSV injection protection utility
- `generateFilename(params)` — Safe filename generation

**UI Components:**
- `ResultsTable.tsx` — "Download CSV" button with `data-testid="export-csv-btn"`
- `FacilityDrawer.tsx` — Export button with `data-testid="facility-export-btn"`
- `SuperfundDrawer.tsx` — "CSV" button with `data-testid="superfund-export-btn"`
- `MapContainer.tsx` — Screenshot button with `data-testid="map-screenshot-btn"`

**Backend:**
- `GET /api/v1/export/csv` — Spatial search CSV export (existing)
- `GET /api/v1/export/csv/browse` — Nationwide browse CSV export (NEW)
- `get_export_rows_browse()` — Service function for non-spatial export

### A.2 Defects Found & Fixed During UAT

| Defect | Root Cause | Fix | Story |
|--------|------------|-----|-------|
| **Empty CSV for nationwide searches** | `/api/v1/export/csv` required lat/lon; frontend fell back to Kansas center with 500-mile radius, excluding distant states (e.g., NJ is 1,200 miles from Kansas) | Added `/api/v1/export/csv/browse` endpoint without spatial constraint; frontend detects `lat=null` and uses browse endpoint | 6.EXPORT.16 |
| **Blank map screenshot** | WebGL clears drawing buffer after each frame; `getCanvas().toDataURL()` captured empty buffer | Added `preserveDrawingBuffer={true}` to MapLibre `<Map>` component | 6.EXPORT.17 |

### A.3 Test Coverage

**Regression tests added:**
- `tests/features/e2e/export.feature` — 5 scenarios covering all export buttons
- `tests/unit/test_export_browse.py` — Backend browse endpoint tests (pending)
- CSV injection tests verify `escapeCsvField()` handles `=+-@` prefix attacks

**Manual UAT verified:**
- [x] Search "lead" + filter "NJ" → CSV downloads with NJ facilities
- [x] Screenshot button produces PNG with map content + watermark
- [x] Facility drawer export includes multi-year release data
- [x] Superfund contaminant export includes all contaminant fields

### A.4 Known Limitations

1. **DuckDB WASM export path not implemented** — Story 7.1.7 placeholder remains; production will use API path
2. **QA step implementations pending** — Stories 6.EXPORT.12 and 6.EXPORT.13 need Playwright download interception
3. **No export limit** — Large exports (>2000 rows) may hit backend limit; consider client-side warning
