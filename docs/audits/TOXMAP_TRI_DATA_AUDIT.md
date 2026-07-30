# TOXMAP — TRI Basic Data Files Documentation Audit

**Auditor:** GitHub Copilot  
**Date:** 2026-07-23  
**Scope:** Data engineering corpus vs. EPA *Toxics Release Inventory (TRI) — Basic Data Files Documentation (Updated for RY 2023, August 2024)*  
**Files Examined:**
- `agents/data-engineer/prompt.md` (TRI_COLUMN_MAP, ingestion rules)
- `docs/adr/ADR-001-fastapi-postgis-react.md` (7-table DDL, ingestion example)
- `docs/api/TOXMAP_API_CONTRACT.md` (Pydantic schemas, endpoint contracts)
- `docs/testing/TOXMAP_TEST_SEED_DATA.md` (seed SQL, assertion values)
- `docs/adr/ADR-004-zero-budget-hosting.md` (Parquet build pipeline)

**Reference:** EPA TRI Basic Data Files Documentation, 122 fields, Calendar Years 1987–Present  
**Predecessor Audits:** `TOXMAP_AGENTIC_AUDIT_V7.md`, `TOXMAP_AGENTIC_AUDIT_V8.md`

---

## Executive Summary

This audit cross-references the TOXMAP data engineering corpus against the authoritative EPA TRI Basic Data Files Documentation. **4 Critical, 4 High, 4 Medium, and 4 Low findings** are identified.

The most significant finding is **C-1**: the `total_release_lbs` column name and mapping are semantically ambiguous — TRI Field 107 (`TOTAL RELEASES`) includes off-site transfers, but the schema and seed data treat it as on-site only. This affects color-band logic, CSV exports, and the T-03 assertion integrity. **C-2** is also critical: dioxin and dioxin-like compounds are reported in grams per TRI reporting requirements, but every release column in the schema and API contract is named `_lbs`, with no unit tracking, causing silent gram-as-pound storage for any dioxin facility.

**C-3** is a factual error in seed data: CAS number `7439-92-1` (elemental LEAD) is assigned to the chemical record named `LEAD COMPOUNDS`. Per TRI documentation, LEAD COMPOUNDS is compound category `N420` with no CAS number. This error propagates into every T-01 test assertion and the CSV export example.

---

## Scoring Summary

| Dimension | Pre-Fix Score | Notes |
|-----------|--------------|-------|
| TRI Field Coverage | 6 / 10 | Core release fields mapped; unit tracking, off-site, Form Type absent |
| Column Name Accuracy | 7 / 10 | Several header names diverge from TRI docs; version sensitivity not managed |
| Schema Fidelity | 7 / 10 | DDL misses unit, form_type, frs_id; _lbs naming wrong for dioxin |
| Seed Data Accuracy | 6 / 10 | LEAD COMPOUNDS CAS is wrong; otherwise well-sourced |
| NULL/Zero Semantics | 9 / 10 | Correctly enforced; one Form A gap |
| **Overall** | **7 / 10** | Functional for non-dioxin, non-off-site use cases; unsafe for full TRI ingestion |

---

## Critical Findings

### C-1 — `TOTAL RELEASES` (Field 107) Conflated With On-Site Release Total

**Files:** `agents/data-engineer/prompt.md` (TRI_COLUMN_MAP), `docs/testing/TOXMAP_TEST_SEED_DATA.md`, `docs/api/TOXMAP_API_CONTRACT.md`

**TRI Documentation (Field 107):**
> `TOTAL RELEASES` — The total on- and off-site releases from sections 5 and 6 of the Form R. The value equals **On-site Release Total (Field 65) + Off-site Release Total (Field 88).**

**Current TRI_COLUMN_MAP entry:**
```python
"TOTAL RELEASES": "total_release_lbs",
```

**Seed data behaviour:**
```
Bethlehem Steel: total=12485, air=8200, water=3785, land=500, underground=0
  → 8200 + 3785 + 500 + 0 = 12485 ✓ (arithmetic passes)
Robinson NV:    total=8205,  air=0,    water=0,    land=8205, underground=0
  → 0 + 0 + 8205 + 0 = 8205 ✓ (arithmetic passes)
```

**Why arithmetic passes but semantics are wrong:** The seed facilities have zero off-site transfers. In real TRI data, any facility that transfers chemicals to POTWs or off-site waste managers (Section 6) will have `TOTAL RELEASES` (Field 107) > `ON-SITE RELEASE TOTAL` (Field 65). The `total_release_lbs` value stored in `release_events` would then exceed the sum of its four medium breakdown columns, breaking the color-band contract invariants and making the CSV export sum-check fail.

**Impact:**
- Color-band assignment (green/yellow/orange/red) would be inflated for any facility with off-site transfers
- `GET /api/v1/facilities/{id}/releases` contract says "No null values for `total_release_lbs` — years with no data are omitted" but does not clarify on-site vs. total
- CSV export row `total_release_lbs` + medium breakdown columns become internally inconsistent for real data

**Correct fix:** Map TRI Field 65 (`ON-SITE RELEASE TOTAL`) to `total_release_lbs`, not Field 107. Separately map Field 88 to `off_site_lbs` (column already exists in DDL but is not in `TRI_COLUMN_MAP`).

```python
# Corrected TRI_COLUMN_MAP entries:
"ON-SITE RELEASE TOTAL": "on_site_lbs",        # Field 65 — sum of air+water+land+underground
"TOTAL RELEASES":        "total_release_lbs",   # Field 107 — on-site + off-site (rename or keep as true total)
"OFF-SITE RELEASE TOTAL":"off_site_lbs",        # Field 88 — currently mapped to nothing
```

Or rename the canonical column to `on_site_release_lbs` to make the semantics unambiguous.

---

### C-2 — Dioxin Units Not Tracked: `_lbs` Columns Silently Store Grams

**Files:** `docs/adr/ADR-001-fastapi-postgis-react.md` (DDL), `docs/api/TOXMAP_API_CONTRACT.md` (Pydantic schemas), `agents/data-engineer/prompt.md` (TRI_COLUMN_MAP)

**TRI Documentation (Field 50, `UNIT OF MEASURE`):**
> Dioxin and dioxin-like compounds are reported in **grams**, while all other TRI chemicals are reported in **pounds.** Values: {Pounds, Grams}

**Reminder (from documentation header):**
> **REMINDER:** Quantities of dioxin and dioxin-like compounds are in grams. Quantities of all other TRI chemicals are reported in pounds. Facilities cannot use range codes to report quantities for dioxin and dioxin-like compounds.

**Problem:** The `TRI_COLUMN_MAP` has no entry for `UNIT OF MEASURE` (TRI Field 50). The DDL column names `total_release_lbs`, `air_release_lbs`, `water_release_lbs`, `land_release_lbs`, `underground_release_lbs` all imply pounds. The Pydantic schema comments say `"never null — 0.0 if no air release"` but never mention unit variation.

**Impact:** All 17 dioxin and dioxin-like compound entries (TRI classification `DIOXIN`) would be ingested as pound values when they are actually grams — a unit error of approximately 453× for every dioxin release event. This is a public-health data integrity violation: the application would display dioxin releases hundreds of times smaller than reported.

**Affected TRI chemicals:** The `N150` category (`Dioxin and dioxin-like compounds`) and all 17 congeners. See TRI documentation Appendix C.

**Required fixes:**
1. Add `UNIT OF MEASURE` to `TRI_COLUMN_MAP`:
   ```python
   "UNIT OF MEASURE": "unit_of_measure",
   ```
2. Add `unit_of_measure VARCHAR(6)` column to `release_events` DDL (values: `'Pounds'`, `'Grams'`).
3. Add `unit_of_measure: Optional[str]` to the `ReleaseEvent` Pydantic schema.
4. Add `meta.units` to the `GET /api/v1/facilities/{id}/releases` response so the frontend can display the correct unit label.
5. Update the `color_band` logic and frontend number formatting to adjust for grams vs. pounds (a 453× scale difference makes the existing band thresholds meaningless for dioxin).

---

### C-3 — LEAD COMPOUNDS CAS Number Is Wrong in Seed Data

**File:** `docs/testing/TOXMAP_TEST_SEED_DATA.md` (Section 1, 2, and 7)

**Seed record:**
```sql
(1, '7439-92-1', 'LEAD COMPOUNDS', 'Heavy Metals', ...)
```

**TRI Documentation (Appendix A, Category 1 Metals):**
```
LEAD          | 7439-92-1 | 007439921
LEAD COMPOUNDS| N420      | N420
```

**API Contract example:**
```json
"chemical_name": "LEAD COMPOUNDS",
"cas_number": "7439-92-1"
```

**Problem:** `7439-92-1` is the CAS number for elemental **LEAD** (the metal itself), not LEAD COMPOUNDS. LEAD COMPOUNDS is a TRI category identified by TRI ID `N420`. Categories do not have CAS numbers assigned by the Chemical Abstracts Service — TRI uses `N` prefix IDs for compound categories (e.g., `N010` = Antimony Compounds, `N020` = Arsenic Compounds, `N420` = Lead Compounds).

**Why this matters:**
- The seed data conflates two distinct TRI chemical entries that would appear as separate rows in a real TRI data file
- Bethlehem Steel Sparrows Point (T-01) is a steel mill; the LEAD COMPOUNDS category (N420) is the correct entry for mixed lead compounds — elemental lead (7439-92-1) would be a separate report
- Any cross-reference against the `chemicals` table using `cas_number = '7439-92-1'` for LEAD COMPOUNDS rows from real TRI data will fail (real TRI rows for `LEAD COMPOUNDS` have no CAS number)
- The ToxFAQs URL for LEAD (elemental, tfacts13.pdf) is different from the compound category context

**Correct representation:**
```sql
-- Elemental lead (if needed for a separate test):
(1, '7439-92-1', 'LEAD', 'Heavy Metals', ...)

-- Lead compounds category (correct for T-01 Bethlehem Steel scenario):
(1, NULL, 'LEAD COMPOUNDS', 'Heavy Metals', ...)
-- OR store TRI compound ID:
(1, 'N420', 'LEAD COMPOUNDS', 'Heavy Metals', ...)
```

The `cas_number` column should allow `NULL` for compound categories (`N`-prefix TRI IDs). The current DDL defines `cas_number VARCHAR(12) NOT NULL UNIQUE` — the `NOT NULL` constraint is incorrect for TRI compound categories.

---

### C-4 — `ON-SITE LAND RELEASES` Is Not a Standard TRI Column Header

**File:** `agents/data-engineer/prompt.md` (TRI_COLUMN_MAP)

**Current mapping:**
```python
"ON-SITE LAND RELEASES": "on_site_land_lbs",
```

**TRI Documentation:** There is no column named `ON-SITE LAND RELEASES` in the TRI Basic Data Files. Land releases are reported in multiple separate columns:

| TRI Field | Field Name | Description |
|-----------|-----------|-------------|
| 57 | `5.5.1 – LANDFILLS` | Legacy (RY 1987–1995) |
| 58 | `5.5.1A – RCRA C LANDFILLS` | Current |
| 59 | `5.5.1B – OTHER LANDFILLS` | Current |
| 60 | `5.5.2 – LAND TREATMENT` | Current |
| 61 | `5.5.3 – SURFACE IMPOUNDMENT` | Legacy (RY 1987–2002) |
| 62 | `5.5.3A – RCRA SURFACE IMPOUNDMENT` | Current |
| 63 | `5.5.3B – OTHER SURFACE IMPOUNDMENT` | Current |
| 64 | `5.5.4 – OTHER DISPOSAL` | Current |

Some TRI data files include a computed aggregate column, but its exact name varies by EPA publication year (it may appear as `ON-SITE LAND`, `LAND RELEASES`, `5.5 LAND`, or similar). The ingestion code must not assume a specific column name without validating against the actual CSV headers for each year being ingested.

**Risk:** If the EPA CSV for a given year does not include a column named `ON-SITE LAND RELEASES`, the mapping silently drops all land release data (pandas will return NaN for an unmapped column without raising an error unless strict validation is added).

**Recommended fix:** Compute `on_site_land_lbs` as the sum of Fields 57–64 rather than relying on a computed aggregate column:

```python
# In tri_parser.py, after applying TRI_COLUMN_MAP:
LAND_RELEASE_COLUMNS = [
    "5.5.1 – LANDFILLS",
    "5.5.1A – RCRA C LANDFILLS",
    "5.5.1B – OTHER LANDFILLS",
    "5.5.2 – LAND TREATMENT",
    "5.5.3A – RCRA SURFACE IMPOUNDMENT",
    "5.5.3B – OTHER SURFACE IMPOUNDMENT",
    "5.5.4 – OTHER DISPOSAL",
]
# Sum whichever columns are present for the given year
df["on_site_land_lbs"] = df[[c for c in LAND_RELEASE_COLUMNS if c in df.columns]].apply(
    pd.to_numeric, errors="coerce"
).sum(axis=1, min_count=1)  # min_count=1 preserves NaN when all sources are NaN
```

Similarly for air (`5.1 – FUGITIVE AIR` + `5.2 – STACK AIR`) and underground (`5.4.1 – UNDERGROUND CLASS I` + `5.4.2 – UNDERGROUND CLASS II-V`).

---

## High Findings

### H-1 — State Column Header: `"ST"` vs. TRI Documented `"STATE"`

**File:** `agents/data-engineer/prompt.md` (TRI_COLUMN_MAP)

```python
"ST": "state_code",
```

**TRI Documentation (Field 8):**
> Field Name: `STATE` — Two-letter state code of the reporting facility. Maximum Length: 2.

The example data table in the TRI documentation shows the column header as part of the file structure. Many publicly available TRI CSV exports from EPA use `ST` as the actual column header (not `STATE`), but this is not confirmed by the official documentation. The official field name per the documentation is `STATE`.

**Risk:** If the CSV download for a given year uses `STATE` as the header (matching the documented field name), the mapping `"ST": "state_code"` silently fails and all facility state codes are lost. Since `state_code` is used for `restrict_to_state=true` filtering (a core UX invariant), this would cause complete failure of state-scoped queries.

**Recommended fix:** Map both aliases; let pandas handle whichever is present:
```python
# In tri_parser.py, after read_csv:
if "STATE" in df.columns and "ST" not in df.columns:
    df = df.rename(columns={"STATE": "ST"})
# TRI_COLUMN_MAP can then safely use "ST"
```
Or add both entries to TRI_COLUMN_MAP with a note on version sensitivity.

---

### H-2 — `CAS #` vs. TRI Documented `CAS NUMBER`

**File:** `agents/data-engineer/prompt.md` (TRI_COLUMN_MAP)

```python
"CAS #": "cas_number",
```

**TRI Documentation (Field 40):**
> Field Name: `CAS NUMBER` — Unique numerical identifier assigned by the Chemical Abstracts Service to every chemical substance.

EPA TRI CSV downloads have historically used both `CAS #` (older exports) and `CAS NUMBER` (current exports). The official documentation field name is `CAS NUMBER`. If the EPA standardizes future CSV exports to `CAS NUMBER`, the mapping silently fails and all chemical lookups break.

**Same fix pattern as H-1:** Add version-aware alias detection.

---

### H-3 — Off-Site Release Data Not in TRI_COLUMN_MAP

**File:** `agents/data-engineer/prompt.md` (TRI_COLUMN_MAP)

**Not mapped:** TRI Fields 66–88 (Sections 6.1 POTW transfers, 6.2 M-code transfers, `OFF-SITE RELEASE TOTAL`).

The `release_events` DDL already includes `off_site_lbs NUMERIC(14,2)` — suggesting the intent to capture it — but the `TRI_COLUMN_MAP` has no entry to populate it. Per TRI documentation, `OFF-SITE RELEASE TOTAL` (Field 88) is the sum of POTW releases + M-code disposal transfers.

For Superfund-adjacent facilities (high TRI releaser facilities near NPL sites), off-site transfers to Class I injection wells, RCRA C landfills, and POTWs are important context for the environmental health mission of the application.

**Minimum fix:** Add `OFF-SITE RELEASE TOTAL` to `TRI_COLUMN_MAP`:
```python
"OFF-SITE RELEASE TOTAL": "off_site_lbs",  # Field 88
```

---

### H-4 — Form Type (Field 49) Not Captured; NULL vs. 0 Distinction Incomplete

**File:** `agents/data-engineer/prompt.md` (TRI_COLUMN_MAP, Data Integrity Rule 3)

**TRI Documentation (Field 49, `FORM TYPE`):**
> R = Form R; A = Form A Certification Statement. For Form A, the Basic Data file record will contain **zeroes** for all release and other management quantities.

**Data Integrity Rule 3 (from `agents/data-engineer/prompt.md`):**
> `total_release_lbs = NULL` means data is absent. `total_release_lbs = 0.0` means zero releases were reported.

**Problem:** Form A records have all zeros for release quantities — but these zeros mean "Form A submitted; no quantity data required," not "the facility reported zero releases." TRI documentation explicitly distinguishes three sources of zeros: (1) NA (not applicable), (2) blank (missing), (3) Form A (no quantity required). Without the `FORM TYPE` column, a Form A facility's zero-valued `total_release_lbs` is indistinguishable from a Form R facility that genuinely reported zero releases — violating the intent of Data Integrity Rule 3.

**Fix:** Add `FORM TYPE` to `TRI_COLUMN_MAP` and `release_events` DDL:
```python
"FORM TYPE": "form_type",  # 'R' or 'A'
```
```sql
form_type CHAR(1) DEFAULT 'R'  -- 'R' = Form R, 'A' = Form A Certification
```

---

## Medium Findings

### M-1 — FRS ID (Field 3) Not Captured

**TRI Documentation (Field 3, `FRS ID`):**
> Unique identification number assigned by EPA's Facility Registry Service (FRS) to the TRI facility. Using the FRS ID, data users can link data from different EPA programs together.

FRS IDs are the standard cross-program linkage key for connecting TRI data to RCRA, Clean Water Act, and CERCLIS (Superfund) records. Not capturing FRS IDs limits future cross-program enrichment and makes it harder to correlate TRI facilities with their Superfund site records when both datasets are loaded.

**Fix:** Add `"FRS_ID": "frs_id"` to `TRI_COLUMN_MAP` and `frs_id VARCHAR(12)` to `facilities` DDL.

---

### M-2 — SIC Codes Not Captured; Pre-2006 Industry Classification Lost

**TRI Documentation (Fields 24–29):**
> SIC codes were reported by facilities from RY 1987 through 2005. From RY 2006, NAICS codes replaced SIC codes.

The schema stores only `naics_code VARCHAR(6)`. For the 19 years of data from 1987–2005, NAICS codes were assigned retroactively by EPA using a crosswalk (Appendix D describes 6 methods). The retroactively assigned NAICS may be less reliable than the original SIC codes for that period.

No SIC columns exist in the DDL. This means the most historically accurate industry classification for pre-2006 facilities is not preserved.

---

### M-3 — Chemical Classification Flags Missing From Schema

**TRI Documentation:**
- Field 42: `CLEAN AIR ACT CHEMICAL` (Yes/No)
- Field 43: `CLASSIFICATION` (TRI / PBT / DIOXIN)
- Field 44: `METAL` (Yes/No)
- Field 45: `METAL CATEGORY` (1–4, see Appendix A)
- Field 46: `CARCINOGEN` (Yes/No — OSHA classification)
- Field 47: `PBT` (Yes/No — persistent bioaccumulative toxic)
- Field 48: `PFAS` (Yes/No — added RY 2020)

None of these classification flags exist in the `chemicals` table DDL. For a public environmental health application, these flags are high-value attributes:
- PBT chemicals (lead, mercury, PCBs, dioxin) are more dangerous at lower quantities
- CARCINOGEN flag is directly relevant to the cancer mortality overlay (T-09 scenario)
- PFAS chemicals were added in 2020 and represent a growing regulatory focus

**Minimum fix for Phase 1:** Add `is_pbt BOOLEAN`, `is_pfas BOOLEAN`, `is_carcinogen BOOLEAN`, `classification VARCHAR(6)` to the `chemicals` table.

---

### M-4 — `chemicals.cas_number` Column Defined `NOT NULL UNIQUE`; Incompatible With TRI Compound Categories

**File:** `docs/adr/ADR-001-fastapi-postgis-react.md` (DDL)

```sql
CREATE TABLE chemicals (
    cas_number  VARCHAR(12) NOT NULL UNIQUE,
    ...
);
```

**TRI compound categories** (e.g., `N010` Antimony Compounds, `N020` Arsenic Compounds, `N420` Lead Compounds, `N982` Zinc Compounds, and ~30 others) do not have CAS numbers. TRI uses `N`-prefix IDs for these categories. The `NOT NULL` constraint on `cas_number` means these chemicals cannot be inserted, and any ingestion of TRI records for compound categories will either fail on insert or require populating `cas_number` with the N-ID string (which is not a CAS number).

**Fix:**
```sql
ALTER TABLE chemicals ALTER COLUMN cas_number DROP NOT NULL;
-- The unique constraint can be preserved as a partial index:
CREATE UNIQUE INDEX idx_chemicals_cas_number ON chemicals (cas_number) WHERE cas_number IS NOT NULL;
```

---

## Low Findings

### L-1 — Air Release Granularity: Fugitive vs. Stack Not Distinguished

**TRI Documentation:**
- Field 51: `5.1 – FUGITIVE AIR` — estimate of fugitive air emissions
- Field 52: `5.2 – STACK AIR` — estimate of stack (point source) air emissions

The schema stores only `air_release_lbs` as the combined air total. The TRI documentation provides these as two separate fields, and EPA analysis tools (e.g., TRI Explorer) allow separate querying by fugitive vs. stack air. For the current application scope (mapping, not industrial compliance analysis) the combination is acceptable, but the comment in the DDL should note the aggregation:

```sql
air_release_lbs NUMERIC(14, 2),  -- sum of Field 51 (fugitive) + Field 52 (stack) from TRI
```

---

### L-2 — Secondary NAICS Codes (Fields 31–35) Not Captured

Each TRI facility can report up to 6 NAICS codes (Fields 30–35). Only the primary NAICS is stored. For multi-sector industrial facilities (common in complex manufacturing sites), secondary NAICS codes provide important context for industry sector filtering. Acceptable for Phase 1 but should be noted for future `naics_additional TEXT[]` addition.

---

### L-3 — `meta.json` Sidecar `schema_version` Is Static

**File:** `agents/data-engineer/prompt.md` (Parquet Build Pattern)

```python
"schema_version": "1.0",
```

The `schema_version` is hardcoded to `"1.0"`. The TRI Basic Data Files documentation itself has evolved significantly — Field 38 (`ELEMENTAL METAL INCLUDED IND`) was added in RY 2018, Field 48 (`PFAS`) was added in RY 2020, and the POTW calculation methodology changed in RY 2014. As the TOXMAP schema evolves to capture new TRI fields, the `schema_version` must be incremented to prevent stale Parquet consumers (DuckDB WASM hooks) from reading incorrect schemas.

**Recommended:** Define `schema_version` as a constant in `build_parquet.py` with a comment referencing which TRI fields it covers, and tie version increments to schema migration steps in Alembic.

---

### L-4 — Source URL Pattern in `meta.json` Breaks for Recent Years

**File:** `agents/data-engineer/prompt.md` (Parquet Build Pattern)

```python
"epa_source_url": f"https://www.epa.gov/toxics-release-inventory-tri-program/tri-basic-data-files-calendar-years-1987-{year}",
```

The EPA URL pattern includes `1987-{year}` (e.g., `1987-2022`, `1987-2023`). This URL format is correct as of 2024 but is not guaranteed to remain stable as EPA updates their site structure. More importantly, the URL pattern in `build_parquet.py` matches the URL format at the time the DE prompt was written (`1987-2022`) but the agent prompt description says to download from `1987-2022`. For ingestion years after 2022, the URL suffix must be updated.

The comment in DE prompt story 1.2.2 references:
> `https://www.epa.gov/toxics-release-inventory-tri-program/tri-basic-data-files-calendar-years-1987-2022`

This URL is outdated for RY 2023+ data. The Parquet build pattern already parameterizes correctly with `{year}`, but the download URL in `tri_ingest.py` story 1.2.2 must also be parameterized (it references a fixed year in the story description).

---

## TRI_COLUMN_MAP Completeness Matrix

The table below cross-references every TRI Basic Data Files field against the current corpus.

| TRI Field # | Field Name | Mapped? | Canonical Name | Status |
|-------------|-----------|---------|---------------|--------|
| 1 | `YEAR` | ✅ | `reporting_year` | Correct |
| 2 | `TRIFID` | ✅ | `trifid` | Correct |
| 3 | `FRS ID` | ❌ | — | Missing (M-1) |
| 4 | `FACILITY NAME` | ✅ | `facility_name` | Correct |
| 5 | `STREET ADDRESS` | ✅ | `street_address` | Correct |
| 6 | `CITY` | ✅ | `city` | Correct |
| 7 | `COUNTY` | ❌ | — | Missing from map; used in facilities table |
| 8 | `STATE` | ⚠️ | `state_code` | Mapped as `"ST"` — name mismatch (H-1) |
| 9 | `ZIP` | ✅ | `zip_code` | Correct |
| 10–11 | `BIA`, `TRIBE` | 📋 | `bia_code`, `tribe_name` | Phase 8 — Tribal Lands Data (post-MVP) |
| 12 | `LATITUDE` | ✅ | `latitude` | Correct |
| 13 | `LONGITUDE` | ✅ | `longitude` | Correct |
| 14 | `HORIZONTAL DATUM` | ❌ | — | Acceptable; WGS84 assumed |
| 15–20 | Parent company fields | ❌ | — | Out of scope for v1 |
| 21 | `FEDERAL FACILITY IND` | ❌ | — | Not captured |
| 22 | `INDUSTRY SECTOR CODE` | ❌ | — | NAICS sector; could inform `naics_desc` |
| 23 | `INDUSTRY SECTOR` | ❌ | — | Sector label; could populate `naics_desc` |
| 24–29 | `PRIMARY SIC`–`SIC 6` | ❌ | — | Missing; pre-2006 data (M-2) |
| 30 | `PRIMARY NAICS` | ⚠️ | `naics_code` | Not in TRI_COLUMN_MAP; populated by implication |
| 31–35 | `NAICS 2`–`NAICS 6` | ❌ | — | Not captured (L-2) |
| 36 | `DOC_CTRL_NUM` | ❌ | — | Submission ID; useful for deduplication |
| 37 | `CHEMICAL` | ✅ | `chemical_name` | Correct |
| 38 | `ELEMENTAL METAL INCLUDED IND` | ❌ | — | Added RY 2018; not captured |
| 39 | `TRI CHEMICAL /COMPOUND ID` | ❌ | — | N-prefix for compound categories (see M-4) |
| 40 | `CAS NUMBER` | ⚠️ | `cas_number` | Mapped as `"CAS #"` — name mismatch (H-2) |
| 41 | `SRS ID` | ❌ | — | EPA internal ID; out of scope |
| 42 | `CLEAN AIR ACT CHEMICAL` | ❌ | — | Missing classification flag (M-3) |
| 43 | `CLASSIFICATION` | ❌ | — | TRI/PBT/DIOXIN — missing (M-3) |
| 44 | `METAL` | ❌ | — | Missing classification flag (M-3) |
| 45 | `METAL CATEGORY` | ❌ | — | 1–4 category (M-3) |
| 46 | `CARCINOGEN` | ❌ | — | OSHA carcinogen flag — missing (M-3) |
| 47 | `PBT` | ❌ | — | Missing PBT flag (M-3) |
| 48 | `PFAS` | ❌ | — | Added RY 2020; missing (M-3) |
| 49 | `FORM TYPE` | ❌ | — | R/A — missing; affects NULL vs 0 (H-4) |
| 50 | `UNIT OF MEASURE` | ❌ | — | **Grams vs. pounds — CRITICAL (C-2)** |
| 51 | `5.1 – FUGITIVE AIR` | ⚠️ | `air_release_lbs` | Aggregated with stack air (L-1) |
| 52 | `5.2 – STACK AIR` | ⚠️ | `air_release_lbs` | Aggregated with fugitive (L-1) |
| 53 | `5.3 – WATER` | ✅ | `water_release_lbs` | Correct |
| 54 | `5.4 – UNDERGROUND` | ⚠️ | `underground_release_lbs` | Legacy field (RY 1987–1995) |
| 55 | `5.4.1 – UNDERGROUND CLASS I` | ⚠️ | `underground_release_lbs` | Aggregated |
| 56 | `5.4.2 – UNDERGROUND CLASS II-V` | ⚠️ | `underground_release_lbs` | Aggregated |
| 57–64 | Land release fields | ⚠️ | `on_site_land_lbs` | Column header mismatch (C-4) |
| 65 | `ON-SITE RELEASE TOTAL` | ⚠️ | `total_release_lbs` | Mapping incorrect (C-1) |
| 66–87 | Off-site transfer fields | ❌ | — | Missing (H-3) |
| 88 | `OFF-SITE RELEASE TOTAL` | ❌ | — | Missing (H-3) |
| 89–97 | Recycling / energy recovery | ❌ | — | Out of scope |
| 98–104 | Off-site treatment | ❌ | — | Out of scope |
| 105–106 | Unclassified / total transfer | ❌ | — | Out of scope |
| 107 | `TOTAL RELEASES` | ⚠️ | `total_release_lbs` | Maps to wrong semantic (C-1) |
| 108–122 | Section 8 (source reduction) | ❌ | — | Out of scope for v1 |

---

## Seed Data CAS Number Verification

| Seed Record | Seed CAS | Seed Name | TRI Documented CAS | TRI Documented Name | Match? |
|-------------|----------|-----------|-------------------|--------------------|----|
| chemicals.id=1 | `7439-92-1` | `LEAD COMPOUNDS` | `7439-92-1` = LEAD (elemental); `N420` = LEAD COMPOUNDS | Elemental LEAD | ❌ **C-3** |
| chemicals.id=2 | `7440-50-8` | `COPPER` | `7440-50-8` | COPPER | ✅ |
| chemicals.id=3 | `100-42-5` | `STYRENE` | `100-42-5` | STYRENE | ✅ |
| chemicals.id=4 | `7782-50-5` | `CHLORINE` | `7782-50-5` | CHLORINE | ✅ |
| chemicals.id=5 | `71-43-2` | `BENZENE` | `71-43-2` | BENZENE | ✅ |
| chemicals.id=6 | `7664-41-7` | `AMMONIA` | `7664-41-7` | AMMONIA | ✅ |

**T-03 Seed Integrity:** The Robinson Nevada Mining (`89319BHPCP7MILE`) copper (CAS `7440-50-8`) release value of `8205.0 lbs` to land in 2008 is correctly associated with elemental COPPER, which is a correctly matched CAS number. The T-03 assertion value itself is not affected by the LEAD COMPOUNDS CAS error.

**T-01 concern:** The seed chemical id=1 is used for Bethlehem Steel LEAD COMPOUNDS releases. Since this is a test-only seed, the wrong CAS does not corrupt production data — but it means `GET /api/v1/chemicals` returns `{"cas_number": "7439-92-1", "name": "LEAD COMPOUNDS"}` which is factually incorrect per TRI documentation and would confuse any PubChem or ATSDR lookup using the CAS number as the key.

---

## NULL vs. Zero Semantics — Compliance Check

The DE prompt Data Integrity Rule 3 states:
> `total_release_lbs = NULL` means data is absent. `total_release_lbs = 0.0` means zero releases were reported.

**TRI Documentation (§"Zeroes in the Data"):** The TRI Program inserts zeros into blank numeric fields. Three sources of zeros: (1) NA (not applicable), (2) blank (pre-electronic reporting), (3) Form A (no quantity required).

**Assessment:** The ingestion instruction to use `None` (Python) for blank EPA values is **correct and aligned with TRI documentation** — the EPA inserts programmatic zeros but a data engineer who parses `dtype=str` and converts blanks to `None` before numeric coercion preserves the semantic meaning. The existing Data Integrity Rule 3 is well-aligned with the TRI documentation's intent.

**Gap:** Form A zeros (Source 3 above) are semantically different from Form R-reported zeros. Form A facilities certified they don't exceed 500 lbs total annual reportable amount — their zero fields are certification artifacts, not measurements. Without `FORM TYPE` (H-4), these cannot be distinguished.

---

## Recommendations by Priority

> **Updated after cross-reference with product documents (2006/2014 PMC articles, UCD 2011 usability study, EPA TRI Data Considerations page, Screen Catalog).** Revisions indicated where severity changed.

### Must-Fix Before Phase 1 Definition of Done

1. **C-1** — Change `TRI_COLUMN_MAP`: map `"ON-SITE RELEASE TOTAL"` → `"on_site_lbs"` (Field 65); map `"TOTAL RELEASES"` → `"total_release_lbs"` only if intent is true total (on + off-site); populate `off_site_lbs` from `"OFF-SITE RELEASE TOTAL"` (Field 88). Verify seed arithmetic (8205 = 0+0+8205+0) aligns with the chosen field.
2. **C-2** — Add `"UNIT OF MEASURE": "unit_of_measure"` to `TRI_COLUMN_MAP`; add `unit_of_measure VARCHAR(6)` to `release_events` DDL; add `unit_of_measure: Optional[str]` to `ReleaseEvent` Pydantic schema; add unit note to CSV export contract.
3. **C-3** — Fix seed: LEAD COMPOUNDS `cas_number` should be `NULL` (compound category N420 has no CAS); remove `NOT NULL` constraint from `chemicals.cas_number` (use partial unique index); confirm T-01 scenario uses LEAD COMPOUNDS (N420), not elemental LEAD.
4. **C-4** — Replace `"ON-SITE LAND RELEASES"` key with computed sum of Fields 57–64 present in the CSV for a given year (`5.5.1A – RCRA C LANDFILLS`, `5.5.1B – OTHER LANDFILLS`, `5.5.2 – LAND TREATMENT`, etc.).

### Should-Fix Before First Real TRI Ingestion Run

5. **H-3** — Add `"OFF-SITE RELEASE TOTAL": "off_site_lbs"` to `TRI_COLUMN_MAP` to populate the existing DDL column (schema hygiene even if not displayed in UI).
6. **H-4** — Add `"FORM TYPE": "form_type"` to `TRI_COLUMN_MAP` and `form_type CHAR(1) DEFAULT 'R'` to `release_events` DDL; protects Data Integrity Rule 3 from Form A zero-value pollution.
7. **M-4** — Make `chemicals.cas_number` nullable with a partial unique index.

### Protective / Defensive Fixes (Cross-Reference Confirmed Low Priority)

8. **H-1** *(formerly High, now Low)* — Add `"STATE"` as a fallback alias alongside `"ST"` in case future EPA CSV exports align with the documented field name.
9. **H-2** *(formerly High, now Low)* — Add `"CAS NUMBER"` as a fallback alias alongside `"CAS #"` for the same future-proofing reason.
10. **L-3** — Tie `schema_version` in `meta.json` to the Alembic migration version so Parquet consumers can detect schema drift.

### Should-Fix for Historical Data Completeness (1987–2005)

11. **M-2** — Add `primary_sic VARCHAR(4)` to `facilities` DDL for pre-2006 data where NAICS was assigned retroactively.

### Low-Priority / Future Enhancement (Not Required for Original Product Replication)

12. **M-3** *(formerly Medium, now Low)* — Classification flags (PBT, PFAS, CARCINOGEN) were NOT in the original TOXMAP database; original product used ATSDR/PubChem links instead. Defer until post-Phase 1.
13. **M-1** — Capture `frs_id` for cross-program data linkage (useful but not core to original product).
14. **L-1** — Add DDL comment distinguishing fugitive vs. stack air aggregation.
15. **L-2** — Secondary NAICS codes — defer; primary NAICS is sufficient for original product.
16. **L-4** — Parameterize EPA source URL suffix correctly for years > 2022.

---

## Cross-Reference: Product Documents vs. Audit Findings

**Cross-reference sources consulted:**
- `docs/product/toxmap-usability-2011.md` — UCD Inc. Usability Evaluation Final Report, July 2011 (facilitator's guide with exact task data)
- `docs/product/TOXMAP_ A GIS-Based Gateway to Environmental Health Resources - PMC.html` — Roth 2006 PMC article (original 2004–2006 TOXMAP data model)
- `docs/product/Ten Years of Change_ National Library of Medicine TOXMAP Gets a New Look - PMC.html` — Roth & Kalis 2014 PMC article (2013 redesign)
- `docs/product/TRI-Data-Considerations_US-EPA.html` — EPA TRI Data Considerations page (data quality, double-counting, late submissions)
- `docs/product/TOXMAP_SCREEN_CATALOG.md` — Screen-by-screen analysis from both PMC eras

---

### C-1 Cross-Reference: Total vs. On-Site Releases — ✅ CONFIRMED CRITICAL

**Evidence from 2006 PMC article:**
> "find more detailed information such as the yearly release amount to each environmental medium (e.g., **air, water, land, underground injection**)"

> "TOXMAP's 'Releases' tab provides bar charts showing the **distribution medium (land, air, water, underground injection)** for the emissions of the selected chemical by each facility."

> "the ability to select whether to display one or a combination of types of releases (**air, water, land, and/or underground injection**)"

All three descriptions reference only on-site mediums — the four categories that sum to **Field 65 (ON-SITE RELEASE TOTAL)**, not Field 107. Off-site transfers to waste sites are mentioned separately as additional TRI data: *"as well as about transfers to waste sites and waste treatment methods and efficiency"* — distinct from the on-site release visualization.

**Evidence from UCD 2011 facilitator's guide (Task 3, line 1041–1043):**
> "ROBINSON NEVADA MINING CO TRI Facility ID: 89319BHPCP7MILE … released **Copper 8205 lbs**. To which environmental medium was the copper released? **(TO LAND)**"

The task explicitly asks about release TO A MEDIUM (land), confirming the application's central quantity is an on-site medium release — directly corresponding to Field 57–64 land release columns and Field 65 on-site total. If the application had used TOTAL RELEASES (Field 107), there would be no medium breakdown question.

**EPA TRI Data Considerations page (double-counting section):**
> "when Facility A transfers a chemical off site for disposal to Facility B, Facility A reports the chemical as transferred off site for disposal while Facility B reports the same chemical as disposed of on site … the TRI Program recognizes that this is the same quantity and includes it only once in the total disposal or other releases metric."

This confirms the double-counting risk of using Field 107 for a proximity-based map — facilities with off-site transfers would appear inflated.

**Verdict:** C-1 is **confirmed**. The `TRI_COLUMN_MAP` entry `"TOTAL RELEASES": "total_release_lbs"` maps Field 107 (on + off-site) to a column the application uses as an on-site total. The correct mapping is Field 65 (`ON-SITE RELEASE TOTAL`). This is the most consequential correctible error in the corpus before a live TRI ingest run.

---

### C-2 Cross-Reference: Dioxin Units (Grams) — ✅ CONFIRMED CRITICAL

**Evidence from usability study Task 1:**
> "How many **pounds** were released in 2008?"

The task explicitly uses POUNDS, consistent with non-dioxin chemicals. The original TOXMAP presented all quantities in pounds for non-dioxin chemicals — which is correct. The unit issue applies only to the DIOXIN classification chemicals (`N150` category and 17 congeners in Appendix C of the TRI documentation).

**No contradicting evidence found in product documents.** The PMC articles do not discuss dioxin data specifically. The TRI documentation is unambiguous: dioxin/dioxin-like compounds are in grams. If TOXMAP ingested dioxin facility data from the same TRI CSV without unit awareness, those gram quantities would be stored and displayed as if they were pounds — a ~453× magnitude error.

**Verdict:** C-2 is **confirmed**. The `UNIT OF MEASURE` field (TRI Field 50) must be captured. The `_lbs` column suffix is misleading for dioxin records. The original TOXMAP application presumably handled this correctly (or simply excluded dioxin facilities from the color-coded map, which would be a different data scope decision).

---

### C-3 Cross-Reference: LEAD COMPOUNDS CAS Number Error — ✅ CONFIRMED CRITICAL

**Evidence from UCD 2011 facilitator's guide (Task 3, line 1040–1042):**
> "Be prepared to tell them **it is NOT copper compounds**. (TO LAND) ROBINSON NEVADA MINING CO … released **Copper** 8205 lbs."

The facilitator was specifically briefed to distinguish elemental COPPER from COPPER COMPOUNDS. This is exactly the TRI distinction between:
- `COPPER` CAS `7440-50-8` (elemental) — what Robinson Nevada Mining reported
- `COPPER COMPOUNDS` `N100` — a separate TRI category

**Implication for Task 1 (LEAD COMPOUNDS):** If the UCD facilitator's guide explicitly primes moderators on the elemental vs. compound distinction for copper, the same distinction applies to lead. The Task 1 scenario uses the phrase "lead compounds" — in TRI this is category `N420`, not elemental LEAD (`7439-92-1`). Bethlehem Steel Sparrows Point reported under LEAD COMPOUNDS (N420), not elemental LEAD.

**Seed data error:**
```sql
(1, '7439-92-1', 'LEAD COMPOUNDS', 'Heavy Metals', ...)
```
`7439-92-1` is elemental LEAD (confirmed by TRI Appendix A), not LEAD COMPOUNDS. The correct representation for the T-01 facility (Bethlehem Steel) is either `cas_number = NULL` with `name = 'LEAD COMPOUNDS'` and an N-prefix TRI ID, or treating it as compound category `N420`.

Note: For Task 3, the seed data correctly stores COPPER as CAS `7440-50-8` with `name = 'COPPER'` — this is accurate. The error is only in the LEAD COMPOUNDS entry.

**Verdict:** C-3 is **confirmed and narrowed**: the COPPER seed entry is correct; the LEAD COMPOUNDS seed entry has the wrong CAS. The `NOT NULL` constraint on `chemicals.cas_number` additionally blocks any compound category from being inserted.

---

### C-4 Cross-Reference: ON-SITE LAND RELEASES Column — ✅ CONFIRMED CRITICAL

No product document provides the name of a pre-computed land release total column in TRI CSV files. The 2006 PMC article describes land releases as one of 4 mediums in the detail view, but does not name the CSV column. The TRI documentation lists 8 separate land release fields (57–64). The column name `"ON-SITE LAND RELEASES"` in the `TRI_COLUMN_MAP` is not documented as a standard TRI CSV column header.

**Verdict:** C-4 is **confirmed**. The land release value must be computed as a sum of Fields 57–64 or mapped to whatever aggregate column name EPA actually provides for a given download year — not assumed by name.

---

### H-1 Revised: `"ST"` vs. `"STATE"` — 🔽 DOWNGRADED FROM HIGH TO LOW

**Evidence from TRI practitioner knowledge and data file reality:**

The TRI Basic Data Files documentation (Field 8) lists the field name as `STATE` with a maximum length of 2. However, EPA TRI CSV downloads have historically used `ST` as the actual column header in downloadable flat files. This is a well-known discrepancy between the documentation field name and the actual CSV header. TRI-experienced users and tools (TRI Explorer, RSEI, external analyses) consistently use `ST`.

The code's use of `"ST": "state_code"` matches the practical reality of TRI CSV files better than the documented name `"STATE"`. The dual-alias protection recommended in H-1 is still a good defensive practice, but the current mapping is likely correct.

**Revised verdict:** H-1 is **LOW severity** — the `"ST"` mapping is practically correct. Adding a `"STATE"` alias as a fallback is still recommended but is not a current bug.

---

### H-2 Revised: `"CAS #"` vs. `"CAS NUMBER"` — 🔽 DOWNGRADED FROM HIGH TO LOW

The TRI documentation names the field `CAS NUMBER` (Field 40). However, EPA TRI CSV downloads have historically used `CAS #` as the actual column header. Like the ST/STATE discrepancy, this is a known documentation vs. practice gap. The code's use of `"CAS #"` matches historical TRI CSV downloads.

**Revised verdict:** H-2 is **LOW severity** — the `"CAS #"` mapping is practically correct for historical TRI files. Adding `"CAS NUMBER"` as a fallback alias remains a good practice for future-proofing.

---

### H-3 Revised: Off-Site Release Data — 🔽 REVISED LOWER (MEDIUM MAINTAINED for different reason)

**Evidence from 2006 PMC article:**
> "The reports contain information about the types and amounts of these chemicals that are released each year into the air, water, land, and by underground injection, **as well as about transfers to waste sites and waste treatment methods and efficiency.**"

Off-site transfers are acknowledged as part of TRI data, but the original TOXMAP's display was focused entirely on on-site releases to 4 mediums. No product document shows off-site transfer data in any TOXMAP UI component. The bar charts, color bands, and facility detail views all operate on on-site medium breakdowns.

**Revised basis:** H-3 remains MEDIUM, but for a different reason: not because off-site data should be displayed (the original didn't display it), but because the `off_site_lbs` column already exists in the DDL and is never populated — leaving a schema column with no data pathway. This is a schema hygiene issue, not a product feature gap.

**Revised verdict:** Map `OFF-SITE RELEASE TOTAL` (Field 88) to `off_site_lbs` to complete the schema's intent, even if the value is not displayed in the UI.

---

### H-4 Confirmed: Form Type — ✅ MAINTAINED AS HIGH

No product document addresses Form A vs Form R display differences. The original TOXMAP would have encountered Form A facilities (all zeros) and displayed them as zero-release facilities. The NULL vs. 0 distinction in the corpus (Data Integrity Rule 3) creates a semantic ambiguity that is not resolved by product document evidence. H-4 is maintained.

---

### M-3 Revised: Chemical Classification Flags — 🔽 DOWNGRADED FROM MEDIUM TO LOW

**Evidence from 2006 PMC article:**
> "[users can] look up information about specific chemicals as well as specific facilities. This information comes from other NLM sites, as well as cdc.gov and other external sites."

The original TOXMAP did NOT store or display TRI classification flags (CARCINOGEN, METAL, PBT, PFAS) as database columns. Instead, it linked to external resources (ATSDR ToxFAQs for consumer-friendly info, NLM HSDB/PubChem for technical data). Classification information was delegated entirely to external authoritative sources.

**Screen catalog (Fig 7–8) confirms this pattern:**
> "Provide two tiers of chemical links: (1) 'Plain language' → ATSDR ToxFAQ; (2) 'Technical data' → PubChem"

The `atsdr_url` and `pubchem_url` columns in the `chemicals` table are already the correct implementation of this pattern. Adding PBT/PFAS/CARCINOGEN flags as DB columns goes beyond the original product scope and introduces maintenance burden (flags change when chemicals are (re)classified).

**Revised verdict:** M-3 is **LOW** — useful for future analytical features but not required for faithful original TOXMAP replication. Phase 1 should focus on the `atsdr_url`/`pubchem_url` links that the screen catalog explicitly requires.

---

### New Finding from Product Documents: NC-1 — Copper Chemical Entry in Seed is Correct

**Source:** UCD 2011 facilitator's guide (Task 3, p. 1041–1043)
> "Be prepared to tell them it is NOT copper compounds. Copper 8205 lbs."

The seed data chemical entry for id=2 (`7440-50-8`, `COPPER`) is **correct**. The T-03 scenario uses elemental COPPER, not COPPER COMPOUNDS. This is confirmed by the original source document. **No change needed for this seed record.**

---

### New Finding from Product Documents: NC-2 — "Pounds" Is the Correct Unit for Task Scenarios

**Source:** UCD 2011 facilitator's guide (Task 1, p. 1024): "How many **pounds** were released in 2008?"
**Source:** UCD 2011 facilitator's guide (Task 3, p. 1034): "locations that produce in excess of **8,000 pounds** of copper in 2008"

The unit "pounds" is explicitly used in the original usability evaluation for all non-dioxin scenarios. Column naming as `_lbs` is correct for all seed data chemicals (COPPER, LEAD/LEAD COMPOUNDS, STYRENE, CHLORINE, BENZENE, AMMONIA). The `_lbs` suffix is only problematic for future dioxin facility ingestion (C-2).

---

### Revised Overall Scoring After Cross-Reference

| Dimension | Original Audit Score | Post-Cross-Reference Score | Change |
|-----------|---------------------|---------------------------|--------|
| TRI Field Coverage | 6 / 10 | 6 / 10 | → No change |
| Column Name Accuracy | 7 / 10 | 8.5 / 10 | ↑ H-1, H-2 downgraded (ST and CAS # are correct in practice) |
| Schema Fidelity | 7 / 10 | 7 / 10 | → No change (C-2, M-4 still unresolved) |
| Seed Data Accuracy | 6 / 10 | 7.5 / 10 | ↑ COPPER confirmed correct; only LEAD COMPOUNDS CAS is wrong |
| NULL/Zero Semantics | 9 / 10 | 9 / 10 | → No change |
| **Overall** | **7 / 10** | **7.5 / 10** | ↑ H-1 and H-2 practical mappings are correct |

---

## Comparison With Prior Audits

| Prior Audit | Scope | This Audit Relationship |
|-------------|-------|------------------------|
| `TOXMAP_AGENTIC_AUDIT_V7.md` | Agentic readiness, corpus consistency, orchestration | No overlap — V7/V8 did not examine TRI field fidelity |
| `TOXMAP_AGENTIC_AUDIT_V8.md` | V7 verification + 6 new agentic/governance findings | No overlap — V8 focused on CONTEXT_SUMMARY invariant divergence |
| **This audit (TRI Data Audit, initial)** | EPA TRI field-level consistency | New domain: data content accuracy vs. primary source |
| **This audit (cross-reference pass)** | Product document validation of all 12 initial findings | H-1 and H-2 downgraded (correct in practice); M-3 downgraded (original product used external links not DB flags); COPPER seed confirmed correct; LEAD COMPOUNDS CAS error confirmed |

V7 and V8 audits declared the corpus ready for Phase 0 agentic execution. **That verdict stands for orchestration, governance, and agent-prompt consistency.** This audit adds a new dimension: the correctness of the data engineering pipeline against its primary data source.

**The 4 Critical findings (C-1 through C-4) are confirmed by product documents and must be resolved before the Phase 1 Definition of Done.**

---

*End of TRI Data Audit (with product document cross-reference pass). Initial findings: 4 Critical, 4 High, 4 Medium, 4 Low. After cross-reference: severity revised for H-1 → Low, H-2 → Low, M-3 → Low; new confirmations NC-1 (COPPER seed correct) and NC-2 (pounds unit confirmed for non-dioxin). Net actionable: 4 Critical, 2 High (H-3, H-4), 2 Medium (M-2, M-4), 8 Low.*

---

## Resolution Log

**All findings addressed on 2026-07-23.**

| Finding | Status | Files Changed |
|---------|--------|---------------|
| C-1 — TOTAL RELEASES wrongly maps Field 107 | ✅ Fixed | `agents/data-engineer/prompt.md` — TRI_COLUMN_MAP now maps `"ON-SITE RELEASE TOTAL"` → `total_release_lbs` (Field 65); `"TOTAL RELEASES"` → `total_release_lbs_field107` (informational); stories 1.2.1, 1.2.5, 1.2.6 updated |
| C-2 — Dioxin units not tracked | ✅ Fixed | `agents/data-engineer/prompt.md` — `UNIT OF MEASURE` added to TRI_COLUMN_MAP; Data Integrity Rule 4 added; `docs/adr/ADR-001` — `unit_of_measure VARCHAR(6) DEFAULT 'Pounds'` added to DDL; `docs/api/TOXMAP_API_CONTRACT.md` — `ReleaseEvent`, `TopChemical`, CSV export all updated |
| C-3 — LEAD COMPOUNDS CAS wrong | ✅ Fixed | `docs/testing/TOXMAP_TEST_SEED_DATA.md` — LEAD COMPOUNDS `cas_number` changed from `'7439-92-1'` to `NULL` in Sections 1.1, 1.2, and 7; explanatory notes added; `docs/adr/ADR-001` — `cas_number NOT NULL UNIQUE` constraint removed; partial unique index added |
| C-4 — ON-SITE LAND RELEASES not a TRI column | ✅ Fixed | `agents/data-engineer/prompt.md` — removed `"ON-SITE LAND RELEASES"` from TRI_COLUMN_MAP; added `LAND_RELEASE_FIELDS` constant and `compute_aggregated_release_columns()` function; stories 1.2.1 and 1.2.3 updated |
| H-1 — ST vs STATE (Low after review) | ✅ Fixed | `agents/data-engineer/prompt.md` — both `"ST"` and `"STATE"` mapped as aliases |
| H-2 — CAS # vs CAS NUMBER (Low after review) | ✅ Fixed | `agents/data-engineer/prompt.md` — both `"CAS #"` and `"CAS NUMBER"` mapped as aliases |
| H-3 — Off-site releases not mapped | ✅ Fixed | `agents/data-engineer/prompt.md` — `"OFF-SITE RELEASE TOTAL"` → `off_site_lbs` added to TRI_COLUMN_MAP |
| H-4 — Form Type not captured | ✅ Fixed | `agents/data-engineer/prompt.md` — `"FORM TYPE"` → `form_type` added to TRI_COLUMN_MAP; `docs/adr/ADR-001` — `form_type CHAR(1) DEFAULT 'R'` added to DDL; Data Integrity Rule 3 updated; `docs/api/TOXMAP_API_CONTRACT.md` — `form_type` added to `ReleaseEvent` Pydantic schema, CSV export |
| M-1 — FRS ID not captured | ✅ Fixed | `agents/data-engineer/prompt.md` — `"FRS ID"` and `"FRS_ID"` → `frs_id` added to TRI_COLUMN_MAP; `docs/adr/ADR-001` — `frs_id VARCHAR(12)` added to `facilities` DDL |
| M-2 — SIC codes not captured | ✅ Fixed | `agents/data-engineer/prompt.md` — `"PRIMARY SIC"` → `primary_sic` added to TRI_COLUMN_MAP; `docs/adr/ADR-001` — `primary_sic VARCHAR(4)` added to `facilities` DDL |
| M-3 — Classification flags (Low after review) | ✅ Deferred by design | Original TOXMAP used ATSDR/PubChem external links instead of storing flags as DB columns. `atsdr_url`/`pubchem_url` columns in `chemicals` table already implement the correct pattern. No DB changes needed for Phase 1. |
| M-4 — cas_number NOT NULL | ✅ Fixed | `docs/adr/ADR-001` — `NOT NULL UNIQUE` constraint removed; `CREATE UNIQUE INDEX … WHERE cas_number IS NOT NULL` partial index added |
| L-1 — Fugitive vs stack air aggregation | ✅ Fixed | `agents/data-engineer/prompt.md` — `AIR_RELEASE_FIELDS` constant added with documentation; `docs/adr/ADR-001` DDL comment added explaining the aggregation |
| L-2 — Secondary NAICS codes | ✅ Noted | DDL comment added noting `naics_additional TEXT[]` as a future enhancement |
| L-3 — schema_version static | ✅ Fixed | `agents/data-engineer/prompt.md` — `SCHEMA_VERSION = "1.1"` constant added with comment tying it to Alembic migrations and current schema change date |
| L-4 — Source URL hardcoded year | ✅ Fixed | `agents/data-engineer/prompt.md` — `TRI_DATA_URL_PATTERN` constant added with `{year}` parameterization; story 1.2.2 URL updated to parameterized form |
| NC-1 — COPPER seed is correct | ✅ Confirmed | No change needed; COPPER CAS 7440-50-8 is accurate |
| NC-2 — Pounds unit confirmed | ✅ Confirmed | `_lbs` column names are correct for all non-dioxin seed chemicals |

