# TOXMAP Test Seed Data

**Date:** 2026-07-15  
**Last Updated:** 2026-07-29 — Added Alaska facility (`99501ANCHO0001`) for Continental US filter regression testing  
**Purpose:** Deterministic fixture data that makes every Gherkin scenario in [TOXMAP_ACCEPTANCE_TESTS.md](TOXMAP_ACCEPTANCE_TESTS.md) pass without hitting the real EPA dataset.  
**Usage:** Load via `psql -f tests/fixtures/seed.sql` or the `seed_db` pytest fixture in `conftest.py`.

> All TRI facility IDs, EPA Superfund IDs, coordinates, and release quantities that are **cited from the UCD 2011 study** use the exact values from the source document. Remaining facilities use realistic but fictional data.

---

## Seed Reference Table

| Seed ID           | Real / Fictional                                    | Source Citation                |
|-------------------|-----------------------------------------------------|--------------------------------|
| `21219BTHLS3RD`   | Realistic (Bethlehem Steel site, Sparrows Point MD) | T-01 scenario                  |
| `89319BHPCP7MILE` | **Real** TRI Facility ID                            | UCD 2011 study, Task 3 (exact) |
| `22630FRTRY0001`  | Fictional                                           | T-05 scenario                  |
| `29801DSTLR0001`  | Fictional                                           | T-07 scenario                  |
| `70663ENTGR0001`  | Fictional                                           | T-07 scenario                  |
| `77536EXXO00001`  | Fictional                                           | T-09 scenario                  |
| `77536LYND00001`  | Fictional                                           | T-09 scenario                  |
| `99501ANCHO0001`  | Fictional                                           | CONUS filter test (Alaska)     |
| `VAD070358684`    | **Real** EPA Superfund ID                           | UCD 2011 study, Task 4 (exact) |
| `51187`           | Real FIPS (Warren County VA)                        | T-05 scenario                  |
| `48201`           | Real FIPS (Harris County TX)                        | T-09 scenario                  |
| `45003`           | Real FIPS (Aiken County SC)                         | T-07 scenario                  |

---

## Section 1: Chemicals

### 1.1 Seed Records

> **DDL note:** `chemicals.cas_number` is nullable (no `NOT NULL` constraint). TRI compound
> categories such as LEAD COMPOUNDS (TRI ID N420) and COPPER COMPOUNDS (TRI ID N100) do not
> have CAS numbers assigned by the Chemical Abstracts Service. Their `cas_number` is `NULL`.
> A partial unique index prevents duplicate non-null CAS values. Elemental chemicals (COPPER,
> LEAD, BENZENE, etc.) do have CAS numbers and are stored as normal.

| id | cas_number  | name             | category                     | atsdr_url                                         | pubchem_url                                         |
|----|-------------|------------------|------------------------------|---------------------------------------------------|-----------------------------------------------------|
| 1  | `NULL`      | `LEAD COMPOUNDS` | `Heavy Metals`               | `https://www.atsdr.cdc.gov/toxfaqs/tfacts13.pdf`  | `https://pubchem.ncbi.nlm.nih.gov/compound/5352425` |
| 2  | `7440-50-8` | `COPPER`         | `Heavy Metals`               | `https://www.atsdr.cdc.gov/toxfaqs/tfacts132.pdf` | `https://pubchem.ncbi.nlm.nih.gov/compound/23978`   |
| 3  | `100-42-5`  | `STYRENE`        | `Volatile Organic Compounds` | `https://www.atsdr.cdc.gov/toxfaqs/tfacts53.pdf`  | `https://pubchem.ncbi.nlm.nih.gov/compound/7501`    |
| 4  | `7782-50-5` | `CHLORINE`       | `Halogens`                   | `https://www.atsdr.cdc.gov/toxfaqs/tfacts172.pdf` | `https://pubchem.ncbi.nlm.nih.gov/compound/24526`   |
| 5  | `71-43-2`   | `BENZENE`        | `Volatile Organic Compounds` | `https://www.atsdr.cdc.gov/toxfaqs/tfacts3.pdf`   | `https://pubchem.ncbi.nlm.nih.gov/compound/241`     |
| 6  | `7664-41-7` | `AMMONIA`        | `Inorganic Compounds`        | `https://www.atsdr.cdc.gov/toxfaqs/tfacts126.pdf` | `https://pubchem.ncbi.nlm.nih.gov/compound/222`     |

> **Why LEAD COMPOUNDS has NULL cas_number:** The UCD 2011 usability study (Task 1) and TRI
> documentation both confirm LEAD COMPOUNDS is TRI compound category N420, not elemental LEAD
> (CAS 7439-92-1). Bethlehem Steel Sparrows Point reported under LEAD COMPOUNDS (a mixed-compounds
> category), not under elemental lead. In real TRI data, the `CAS #` column is blank for
> compound categories. Using 7439-92-1 here would cause PubChem/ATSDR lookups to resolve to
> the wrong entry (elemental lead, not lead compound mixtures).

### 1.2 SQL

```sql
INSERT INTO chemicals (id, cas_number, name, category, atsdr_url, pubchem_url) VALUES
  (1, NULL,         'LEAD COMPOUNDS',  'Heavy Metals',               'https://www.atsdr.cdc.gov/toxfaqs/tfacts13.pdf',  'https://pubchem.ncbi.nlm.nih.gov/compound/5352425'),
  (2, '7440-50-8',  'COPPER',          'Heavy Metals',               'https://www.atsdr.cdc.gov/toxfaqs/tfacts132.pdf', 'https://pubchem.ncbi.nlm.nih.gov/compound/23978'),
  (3, '100-42-5',   'STYRENE',         'Volatile Organic Compounds', 'https://www.atsdr.cdc.gov/toxfaqs/tfacts53.pdf',  'https://pubchem.ncbi.nlm.nih.gov/compound/7501'),
  (4, '7782-50-5',  'CHLORINE',        'Halogens',                   'https://www.atsdr.cdc.gov/toxfaqs/tfacts172.pdf', 'https://pubchem.ncbi.nlm.nih.gov/compound/24526'),
  (5, '71-43-2',    'BENZENE',         'Volatile Organic Compounds', 'https://www.atsdr.cdc.gov/toxfaqs/tfacts3.pdf',   'https://pubchem.ncbi.nlm.nih.gov/compound/241'),
  (6, '7664-41-7',  'AMMONIA',         'Inorganic Compounds',        'https://www.atsdr.cdc.gov/toxfaqs/tfacts126.pdf', 'https://pubchem.ncbi.nlm.nih.gov/compound/222');
```

---

## Section 2: TRI Facilities

### 2.1 Seed Records

| id | tri_facility_id   | name                                    | city             | state | zip     | naics    | lat       | lon         | Scenario    |
|----|-------------------|-----------------------------------------|------------------|-------|---------|----------|-----------|-------------|-------------|
| 1  | `21219BTHLS3RD`   | `BETHLEHEM STEEL CORP - SPARROWS POINT` | `SPARROWS POINT` | `MD`  | `21219` | `331110` | `39.2197` | `-76.4785`  | T-01        |
| 2  | `89319BHPCP7MILE` | `ROBINSON NEVADA MINING CO`             | `RUTH`           | `NV`  | `89319` | `212234` | `39.2919` | `-115.0319` | T-03        |
| 3  | `22630FRTRY0001`  | `FRONT ROYAL PLASTICS INC`              | `FRONT ROYAL`    | `VA`  | `22630` | `326130` | `38.9241` | `-78.1856`  | T-05        |
| 4  | `29801DSTLR0001`  | `BORDEN CHEMICALS AND PLASTICS INC`     | `AIKEN`          | `SC`  | `29801` | `325211` | `33.5601` | `-81.7198`  | T-07        |
| 5  | `70663ENTGR0001`  | `ENTERPRISE GAS PROCESSING LLC`         | `SULPHUR`        | `LA`  | `70663` | `486210` | `30.1944` | `-93.2044`  | T-07        |
| 6  | `77536EXXO00001`  | `EXXONMOBIL CHEMICAL PLANT`             | `BAYTOWN`        | `TX`  | `77536` | `324110` | `29.7424` | `-95.0215`  | T-09        |
| 7  | `77536LYND00001`  | `LYONDELLBASELL REFINERY`               | `HOUSTON`        | `TX`  | `77536` | `324110` | `29.7380` | `-95.2100`  | T-09        |
| 8  | `99501ANCHO0001`  | `ALASKA MINING CO`                      | `ANCHORAGE`      | `AK`  | `99501` | `212234` | `61.2181` | `-149.9003` | CONUS test  |
| 9  | `22630SMRLG0001`  | `SMALL RELEASE FACILITY`                | `FRONT ROYAL`    | `VA`  | `22630` | `325199` | `38.9150` | `-78.1900`  | Green tier  |

### 2.2 SQL

```sql
INSERT INTO facilities (id, tri_facility_id, name, address, city, state_code, zip_code, county, naics_code, naics_desc, location) VALUES
  (1, '21219BTHLS3RD',  'BETHLEHEM STEEL CORP - SPARROWS POINT', '3200 SPARROWS POINT RD',          'SPARROWS POINT', 'MD', '21219', 'BALTIMORE',  '331110', 'Iron and Steel Mills',                     ST_GeomFromText('POINT(-76.4785 39.2197)', 4326)),
  (2, '89319BHPCP7MILE','ROBINSON NEVADA MINING CO',             '7 MILES W OF ELY ON HWY 50',      'RUTH',           'NV', '89319', 'WHITE PINE', '212234', 'Copper Ore and Nickel Ore Mining',         ST_GeomFromText('POINT(-115.0319 39.2919)', 4326)),
  (3, '22630FRTRY0001', 'FRONT ROYAL PLASTICS INC',             '450 KENDRICK LN',                  'FRONT ROYAL',    'VA', '22630', 'WARREN',     '326130', 'Laminated Plastics Plate Manufacturing',   ST_GeomFromText('POINT(-78.1856 38.9241)', 4326)),
  (4, '29801DSTLR0001', 'BORDEN CHEMICALS AND PLASTICS INC',    '1000 BORDEN DR',                   'AIKEN',          'SC', '29801', 'AIKEN',      '325211', 'Plastics Material Manufacturing',          ST_GeomFromText('POINT(-81.7198 33.5601)', 4326)),
  (5, '70663ENTGR0001', 'ENTERPRISE GAS PROCESSING LLC',        '4500 ENTERPRISE BLVD',             'SULPHUR',        'LA', '70663', 'CALCASIEU',  '486210', 'Pipeline Transportation of Natural Gas',   ST_GeomFromText('POINT(-93.2044 30.1944)', 4326)),
  (6, '77536EXXO00001', 'EXXONMOBIL CHEMICAL PLANT',           '5200 BAYWAY DR',                   'BAYTOWN',        'TX', '77536', 'HARRIS',     '324110', 'Petroleum Refineries',                     ST_GeomFromText('POINT(-95.0215 29.7424)', 4326)),
  (7, '77536LYND00001', 'LYONDELLBASELL REFINERY',             '12000 LAWNDALE ST',                'HOUSTON',        'TX', '77536', 'HARRIS',     '324110', 'Petroleum Refineries',                     ST_GeomFromText('POINT(-95.2100 29.7380)', 4326)),
  (8, '99501ANCHO0001', 'ALASKA MINING CO',                    '100 NORTHERN BLVD',                'ANCHORAGE',      'AK', '99501', 'ANCHORAGE',  '212234', 'Copper Ore and Nickel Ore Mining',         ST_GeomFromText('POINT(-149.9003 61.2181)', 4326)),
  (9, '22630SMRLG0001', 'SMALL RELEASE FACILITY',              '200 GREEN TIER WAY',               'FRONT ROYAL',    'VA', '22630', 'WARREN',     '325199', 'All Other Basic Organic Chemical Mfg',     ST_GeomFromText('POINT(-78.1900 38.9150)', 4326));
```

---

## Section 3: Release Events

> Release quantities sourced from: UCD 2011 study (T-03 exact values), realistic EPA TRI ranges for all others.

> **`total_release_lbs` semantics (A-047):** This column maps to TRI Field 65 (`ON-SITE RELEASE TOTAL`) — the sum of air + water + land + underground releases at the reporting facility. It does **not** include off-site transfers (TRI Field 107 `TOTAL RELEASES`). All seed records satisfy the invariant `total_release_lbs = air + water + land + underground`. The seed facilities have zero off-site transfers, so Field 65 and Field 107 are equal in these specific records, but the mapping is intentionally to Field 65.

> **`unit_of_measure` column (C-2):** Added per TRI Data Audit. TRI Field 50 (`UNIT OF MEASURE`) distinguishes pounds from grams. All seed chemicals are non-dioxin, so all records use `'Pounds'`. A DuckDB WASM consumer or CSV exporter **must** read this field before displaying quantities; dioxin facilities (not in seed) would have `'Grams'`.

> **`form_type` column (H-4):** Added per TRI Data Audit. TRI Field 49 (`FORM TYPE`) is `'R'` (Form R — with quantities) or `'A'` (Form A Certification — all zeros, no quantity data). All seed records use `'R'`. A `form_type = 'A'` record with `total_release_lbs = 0.0` means no quantity reported, not a genuine zero-release measurement.

### 3.1 Seed Records

| facility_id           | chemical_id  | year | total_lbs   | air_lbs | water_lbs | land_lbs  | underground_lbs | Scenario                          |
|-----------------------|--------------|------|-------------|---------|-----------|-----------|-----------------|-----------------------------------|
| 1 (Bethlehem)         | 1 (Lead)     | 2008 | **12,485**  | 8,200   | 3,785     | 500       | 0               | T-01 assert                       |
| 1 (Bethlehem)         | 1 (Lead)     | 2007 | 14,210      | 9,100   | 4,610     | 500       | 0               | T-01 trend                        |
| 1 (Bethlehem)         | 1 (Lead)     | 2006 | 15,830      | 10,400  | 4,930     | 500       | 0               | T-01 trend                        |
| 2 (Robinson)          | 2 (Copper)   | 2008 | **8,205**   | 0       | 0         | **8,205** | 0               | T-03 assert (exact from UCD 2011) |
| 2 (Robinson)          | 2 (Copper)   | 2007 | 7,890       | 0       | 0         | 7,890     | 0               | T-03 trend                        |
| 2 (Robinson)          | 2 (Copper)   | 2006 | 9,100       | 0       | 0         | 9,100     | 0               | T-03 trend                        |
| 3 (Front Royal)       | 3 (Styrene)  | 2008 | 4,750       | 4,200   | 0         | 550       | 0               | T-05                              |
| 3 (Front Royal)       | 3 (Styrene)  | 2007 | 5,100       | 4,600   | 0         | 500       | 0               | T-05 trend                        |
| 4 (Borden SC)         | 4 (Chlorine) | 2008 | **85,000**  | 85,000  | 0         | 0         | 0               | T-07 SC assert                    |
| 5 (Enterprise LA)     | 4 (Chlorine) | 2008 | **342,500** | 340,000 | 0         | 2,500     | 0               | T-07 national assert              |
| 6 (ExxonMobil TX)     | 5 (Benzene)  | 2008 | 28,400      | 27,100  | 900       | 400       | 0               | T-09                              |
| 7 (LyondellBasell TX) | 5 (Benzene)  | 2008 | 19,750      | 18,900  | 0         | 850       | 0               | T-09                              |
| 6 (ExxonMobil TX)     | 5 (Benzene)  | 2007 | 31,200      | 30,000  | 800       | 400       | 0               | T-09 trend                        |
| 6 (ExxonMobil TX)     | 5 (Benzene)  | 2006 | 35,600      | 34,100  | 1,000     | 500       | 0               | T-09 trend                        |
| 8 (Alaska Mining AK)  | 2 (Copper)   | 2008 | 3,500       | 0       | 0         | 3,500     | 0               | CONUS filter exclusion test       |
| 9 (Small Release VA)  | 6 (Ammonia)  | 2008 | **450**     | 400     | 50        | 0         | 0               | Green tier test (< 1,000 lbs)     |

### 3.2 SQL

```sql
INSERT INTO release_events (facility_id, chemical_id, reporting_year, total_release_lbs, air_release_lbs, water_release_lbs, land_release_lbs, underground_release_lbs, unit_of_measure, form_type) VALUES
  -- T-01: Bethlehem Steel lead compounds (2006-2008)
  (1, 1, 2008, 12485.0,  8200.0,  3785.0,  500.0, 0.0, 'Pounds', 'R'),
  (1, 1, 2007, 14210.0,  9100.0,  4610.0,  500.0, 0.0, 'Pounds', 'R'),
  (1, 1, 2006, 15830.0, 10400.0,  4930.0,  500.0, 0.0, 'Pounds', 'R'),
  -- T-03: Robinson NV copper to land (2006-2008) — 2008 exact from UCD 2011
  (2, 2, 2008,  8205.0,     0.0,     0.0, 8205.0, 0.0, 'Pounds', 'R'),
  (2, 2, 2007,  7890.0,     0.0,     0.0, 7890.0, 0.0, 'Pounds', 'R'),
  (2, 2, 2006,  9100.0,     0.0,     0.0, 9100.0, 0.0, 'Pounds', 'R'),
  -- T-05: Front Royal plastics styrene (2007-2008)
  (3, 3, 2008,  4750.0,  4200.0,     0.0,  550.0, 0.0, 'Pounds', 'R'),
  (3, 3, 2007,  5100.0,  4600.0,     0.0,  500.0, 0.0, 'Pounds', 'R'),
  -- T-07: SC chlorine (largest in state)
  (4, 4, 2008, 85000.0, 85000.0,     0.0,    0.0, 0.0, 'Pounds', 'R'),
  -- T-07: LA chlorine (largest nationwide)
  (5, 4, 2008, 342500.0, 340000.0,   0.0, 2500.0, 0.0, 'Pounds', 'R'),
  -- T-09: Houston benzene (2006-2008)
  (6, 5, 2008, 28400.0, 27100.0,   900.0,  400.0, 0.0, 'Pounds', 'R'),
  (6, 5, 2007, 31200.0, 30000.0,   800.0,  400.0, 0.0, 'Pounds', 'R'),
  (6, 5, 2006, 35600.0, 34100.0,  1000.0,  500.0, 0.0, 'Pounds', 'R'),
  (7, 5, 2008, 19750.0, 18900.0,     0.0,  850.0, 0.0, 'Pounds', 'R'),
  -- CONUS filter test: Alaska copper (non-continental US)
  (8, 2, 2008,  3500.0,     0.0,     0.0, 3500.0, 0.0, 'Pounds', 'R'),
  -- Green tier test: Small Release Facility ammonia (< 1,000 lbs)
  (9, 6, 2008,   450.0,   400.0,    50.0,    0.0, 0.0, 'Pounds', 'R');
```

---

## Section 4: Superfund Sites

### 4.1 Seed Records

| id | epa_id         | name                   | city          | state | zip     | hrs_score | status | contaminants                        | lat       | lon        | Scenario                   |
|----|----------------|------------------------|---------------|-------|---------|-----------|--------|-------------------------------------|-----------|------------|----------------------------|
| 1  | `VAD070358684` | `AVTEX FIBERS INC`     | `FRONT ROYAL` | `VA`  | `22630` | `50.51`   | `NPL`  | `{STYRENE, CARBON DISULFIDE, ZINC}` | `38.9179` | `-78.1942` | T-04 (exact from UCD 2011) |
| 2  | `VAD980554587` | `ARLINGTON SCRAP YARD` | `ARLINGTON`   | `VA`  | `22204` | `28.74`   | `NPL`  | `{LEAD COMPOUNDS, CADMIUM}`         | `38.8823` | `-77.1089` | VA list coverage           |

### 4.2 SQL

```sql
INSERT INTO superfund_sites (id, epa_id, name, address, city, state_code, zip_code, county, status, hrs_score, npl_date, epa_progress_url, contaminants, location) VALUES
  (1, 'VAD070358684', 'AVTEX FIBERS INC',    'BOX 1169 KENDRICK LN', 'FRONT ROYAL', 'VA', '22630', 'WARREN',    'NPL', 50.51, '1983-09-08', 'https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.Cleanup&id=0302388', ARRAY['STYRENE','CARBON DISULFIDE','ZINC'],  ST_GeomFromText('POINT(-78.1942 38.9179)', 4326)),
  (2, 'VAD980554587', 'ARLINGTON SCRAP YARD', '4200 LEE HWY',        'ARLINGTON',   'VA', '22204', 'ARLINGTON', 'NPL', 28.74, '1989-02-21', 'https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.Cleanup&id=0304032', ARRAY['LEAD COMPOUNDS','CADMIUM'],           ST_GeomFromText('POINT(-77.1089 38.8823)', 4326));
```

---

## Section 5: Census County Demographics

### 5.1 Seed Records

| id | fips_code | name            | state | census_year | total_pop | median_income | pct_under_18 | pct_over_65 | pct_nonwhite | Scenario               |
|----|-----------|-----------------|-------|-------------|-----------|---------------|--------------|-------------|--------------|------------------------|
| 1  | `51187`   | `Warren County` | `VA`  | `2000`      | `31584`   | `41,246`      | `24.7`       | `11.2`      | `8.4`        | T-05 (under-18 assert) |
| 2  | `48201`   | `Harris County` | `TX`  | `2000`      | `3400578` | `42,890`      | `28.3`       | `7.9`       | `55.4`       | T-09 (benzene/cancer)  |
| 3  | `45003`   | `Aiken County`  | `SC`  | `2000`      | `142552`  | `38,100`      | `25.1`       | `13.6`      | `34.2`       | T-07 (chlorine/SC)     |

### 5.2 SQL

> Note: `boundary` geometry requires Census TIGER shapefile for real polygons. For test seed, use a simplified bounding-box polygon.

```sql
INSERT INTO census_county (id, fips_code, name, state_code, census_year, total_pop, median_income, pct_under_18, pct_over_65, pct_nonwhite, cancer_mortality_female_per_100k, boundary) VALUES
  (1, '51187', 'Warren County',  'VA', 2000,   31584,  41246.00, 24.7, 11.2,  8.4, 148.7,
      ST_GeomFromText('POLYGON((-78.40 38.76, -78.40 38.99, -78.00 38.99, -78.00 38.76, -78.40 38.76))', 4326)),
  (2, '48201', 'Harris County',  'TX', 2000, 3400578,  42890.00, 28.3,  7.9, 55.4, 162.4,
      ST_GeomFromText('POLYGON((-95.79 29.52, -95.79 30.11, -94.91 30.11, -94.91 29.52, -95.79 29.52))', 4326)),
  (3, '45003', 'Aiken County',   'SC', 2000,  142552,  38100.00, 25.1, 13.6, 34.2, NULL,
      ST_GeomFromText('POLYGON((-81.97 33.35, -81.97 33.84, -81.42 33.84, -81.42 33.35, -81.97 33.35))', 4326));
```

---

## Section 6: Cancer/Health Mortality Fields

The three mortality columns (`cancer_mortality_female_per_100k`, `cancer_mortality_male_per_100k`, `heart_disease_mortality_per_100k`) are defined in the `census_county` CREATE TABLE in ADR-001 and are populated in the Section 5.2 and Section 7 INSERT statements — no separate UPDATE statement is needed.

**Seeded values (for test assertions):**

| County           | FIPS    | `cancer_mortality_female_per_100k` | Scenario                               |
|------------------|---------|------------------------------------|----------------------------------------|
| Harris County TX | `48201` | `162.4`                            | T-09 benzene + mortality co-occurrence |
| Warren County VA | `51187` | `148.7`                            | T-09 / T-05 demographic overlay        |
| Aiken County SC  | `45003` | `NULL`                             | T-07 (not used in mortality tests)     |

`cancer_mortality_male_per_100k` and `heart_disease_mortality_per_100k` are `NULL` for all seed records — they are not required by any of the T-01 through T-09 scenarios.

---

## Section 7: Complete `seed.sql` File

```sql
-- ============================================================
-- TOXMAP Test Seed Data
-- Load with: psql -U postgres -d toxmap_test -f tests/fixtures/seed.sql
-- ============================================================

BEGIN;

-- Clear existing test data (safe for test DB only)
TRUNCATE TABLE release_events, superfund_sites, census_county,
               facilities, chemicals RESTART IDENTITY CASCADE;

-- 1. Chemicals
INSERT INTO chemicals (id, cas_number, name, category, atsdr_url, pubchem_url) VALUES
  (1, NULL,         'LEAD COMPOUNDS',  'Heavy Metals',               'https://www.atsdr.cdc.gov/toxfaqs/tfacts13.pdf',  'https://pubchem.ncbi.nlm.nih.gov/compound/5352425'),
  (2, '7440-50-8',  'COPPER',          'Heavy Metals',               'https://www.atsdr.cdc.gov/toxfaqs/tfacts132.pdf', 'https://pubchem.ncbi.nlm.nih.gov/compound/23978'),
  (3, '100-42-5',   'STYRENE',         'Volatile Organic Compounds', 'https://www.atsdr.cdc.gov/toxfaqs/tfacts53.pdf',  'https://pubchem.ncbi.nlm.nih.gov/compound/7501'),
  (4, '7782-50-5',  'CHLORINE',        'Halogens',                   'https://www.atsdr.cdc.gov/toxfaqs/tfacts172.pdf', 'https://pubchem.ncbi.nlm.nih.gov/compound/24526'),
  (5, '71-43-2',    'BENZENE',         'Volatile Organic Compounds', 'https://www.atsdr.cdc.gov/toxfaqs/tfacts3.pdf',   'https://pubchem.ncbi.nlm.nih.gov/compound/241'),
  (6, '7664-41-7',  'AMMONIA',         'Inorganic Compounds',        'https://www.atsdr.cdc.gov/toxfaqs/tfacts126.pdf', 'https://pubchem.ncbi.nlm.nih.gov/compound/222');

-- 2. Facilities
INSERT INTO facilities (id, tri_facility_id, name, address, city, state_code, zip_code, county, naics_code, naics_desc, location) VALUES
  (1, '21219BTHLS3RD',   'BETHLEHEM STEEL CORP - SPARROWS POINT', '3200 SPARROWS POINT RD',     'SPARROWS POINT', 'MD', '21219', 'BALTIMORE',  '331110', 'Iron and Steel Mills',                    ST_GeomFromText('POINT(-76.4785 39.2197)', 4326)),
  (2, '89319BHPCP7MILE', 'ROBINSON NEVADA MINING CO',             '7 MILES W OF ELY ON HWY 50', 'RUTH',           'NV', '89319', 'WHITE PINE', '212234', 'Copper Ore and Nickel Ore Mining',        ST_GeomFromText('POINT(-115.0319 39.2919)', 4326)),
  (3, '22630FRTRY0001',  'FRONT ROYAL PLASTICS INC',              '450 KENDRICK LN',             'FRONT ROYAL',    'VA', '22630', 'WARREN',     '326130', 'Laminated Plastics Plate Manufacturing',  ST_GeomFromText('POINT(-78.1856 38.9241)', 4326)),
  (4, '29801DSTLR0001',  'BORDEN CHEMICALS AND PLASTICS INC',     '1000 BORDEN DR',              'AIKEN',          'SC', '29801', 'AIKEN',      '325211', 'Plastics Material Manufacturing',         ST_GeomFromText('POINT(-81.7198 33.5601)', 4326)),
  (5, '70663ENTGR0001',  'ENTERPRISE GAS PROCESSING LLC',         '4500 ENTERPRISE BLVD',        'SULPHUR',        'LA', '70663', 'CALCASIEU',  '486210', 'Pipeline Transportation of Natural Gas',  ST_GeomFromText('POINT(-93.2044 30.1944)', 4326)),
  (6, '77536EXXO00001',  'EXXONMOBIL CHEMICAL PLANT',             '5200 BAYWAY DR',              'BAYTOWN',        'TX', '77536', 'HARRIS',     '324110', 'Petroleum Refineries',                    ST_GeomFromText('POINT(-95.0215 29.7424)', 4326)),
  (7, '77536LYND00001',  'LYONDELLBASELL REFINERY',               '12000 LAWNDALE ST',           'HOUSTON',        'TX', '77536', 'HARRIS',     '324110', 'Petroleum Refineries',                    ST_GeomFromText('POINT(-95.2100 29.7380)', 4326)),
  (8, '99501ANCHO0001',  'ALASKA MINING CO',                      '100 NORTHERN BLVD',           'ANCHORAGE',      'AK', '99501', 'ANCHORAGE',  '212234', 'Copper Ore and Nickel Ore Mining',        ST_GeomFromText('POINT(-149.9003 61.2181)', 4326));

-- 3. Release events
INSERT INTO release_events (facility_id, chemical_id, reporting_year, total_release_lbs, air_release_lbs, water_release_lbs, land_release_lbs, underground_release_lbs, unit_of_measure, form_type) VALUES
  (1, 1, 2008, 12485.0,  8200.0,  3785.0,  500.0,    0.0, 'Pounds', 'R'),
  (1, 1, 2007, 14210.0,  9100.0,  4610.0,  500.0,    0.0, 'Pounds', 'R'),
  (1, 1, 2006, 15830.0, 10400.0,  4930.0,  500.0,    0.0, 'Pounds', 'R'),
  (2, 2, 2008,  8205.0,     0.0,     0.0, 8205.0,    0.0, 'Pounds', 'R'),
  (2, 2, 2007,  7890.0,     0.0,     0.0, 7890.0,    0.0, 'Pounds', 'R'),
  (2, 2, 2006,  9100.0,     0.0,     0.0, 9100.0,    0.0, 'Pounds', 'R'),
  (3, 3, 2008,  4750.0,  4200.0,     0.0,  550.0,    0.0, 'Pounds', 'R'),
  (3, 3, 2007,  5100.0,  4600.0,     0.0,  500.0,    0.0, 'Pounds', 'R'),
  (4, 4, 2008, 85000.0, 85000.0,     0.0,    0.0,    0.0, 'Pounds', 'R'),
  (5, 4, 2008, 342500.0,340000.0,    0.0, 2500.0,    0.0, 'Pounds', 'R'),
  (6, 5, 2008, 28400.0, 27100.0,   900.0,  400.0,    0.0, 'Pounds', 'R'),
  (6, 5, 2007, 31200.0, 30000.0,   800.0,  400.0,    0.0, 'Pounds', 'R'),
  (6, 5, 2006, 35600.0, 34100.0,  1000.0,  500.0,    0.0, 'Pounds', 'R'),
  (7, 5, 2008, 19750.0, 18900.0,     0.0,  850.0,    0.0, 'Pounds', 'R'),
  (8, 2, 2008,  3500.0,     0.0,     0.0, 3500.0,    0.0, 'Pounds', 'R');

-- 4. Superfund sites
INSERT INTO superfund_sites (id, epa_id, name, address, city, state_code, zip_code, county, status, hrs_score, npl_date, epa_progress_url, contaminants, location) VALUES
  (1, 'VAD070358684', 'AVTEX FIBERS INC',     'BOX 1169 KENDRICK LN', 'FRONT ROYAL', 'VA', '22630', 'WARREN',    'NPL', 50.51, '1983-09-08', 'https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.Cleanup&id=0302388', ARRAY['STYRENE','CARBON DISULFIDE','ZINC'],  ST_GeomFromText('POINT(-78.1942 38.9179)', 4326)),
  (2, 'VAD980554587', 'ARLINGTON SCRAP YARD', '4200 LEE HWY',         'ARLINGTON',   'VA', '22204', 'ARLINGTON', 'NPL', 28.74, '1989-02-21', 'https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.Cleanup&id=0304032', ARRAY['LEAD COMPOUNDS','CADMIUM'],           ST_GeomFromText('POINT(-77.1089 38.8823)', 4326));

-- 5. Census county demographics
INSERT INTO census_county (id, fips_code, name, state_code, census_year, total_pop, median_income, pct_under_18, pct_over_65, pct_nonwhite, cancer_mortality_female_per_100k, boundary) VALUES
  (1, '51187', 'Warren County', 'VA', 2000,   31584,  41246.00, 24.7, 11.2,  8.4, 148.7, ST_GeomFromText('POLYGON((-78.40 38.76, -78.40 38.99, -78.00 38.99, -78.00 38.76, -78.40 38.76))', 4326)),
  (2, '48201', 'Harris County', 'TX', 2000, 3400578,  42890.00, 28.3,  7.9, 55.4, 162.4, ST_GeomFromText('POLYGON((-95.79 29.52, -95.79 30.11, -94.91 30.11, -94.91 29.52, -95.79 29.52))', 4326)),
  (3, '45003', 'Aiken County',  'SC', 2000,  142552,  38100.00, 25.1, 13.6, 34.2,  NULL, ST_GeomFromText('POLYGON((-81.97 33.35, -81.97 33.84, -81.42 33.84, -81.42 33.35, -81.97 33.35))', 4326));

COMMIT;
```

---

## Section 8: pytest `conftest.py` Fixture

```python
# tests/conftest.py

# ── Driver note (M-6) ─────────────────────────────────────────────────────────
# Tests use psycopg2 (SYNCHRONOUS) for fixture setup and teardown.
# The FastAPI application uses asyncpg (ASYNC) via SQLAlchemy 2.0 async engine.
# These are two independent connection pools — psycopg2 is used ONLY in conftest.py.
# Both drivers are needed: asyncpg cannot execute raw DDL-containing seed SQL blocks,
# and psycopg2 is not compatible with FastAPI's async context.
# See pyproject.toml [project.optional-dependencies] test group for psycopg2-binary.

# ── Thread safety (9.5) ───────────────────────────────────────────────────────
# Tests MUST run single-threaded. Do NOT use pytest-xdist (-n auto).
# The session-scoped db_connection is shared across function-scoped seed_db fixtures.
# Parallel execution would cause TRUNCATE races and corrupt test state.
# The pyproject.toml [tool.pytest.ini_options] addopts = "-p no:xdist" enforces this.
# ─────────────────────────────────────────────────────────────────────────────

import os
import pytest
import psycopg2
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import create_app

# M-4: use explicit env var instead of undefined get_db_url() function
DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://postgres:postgres@localhost:5432/toxmap_test"
)

SEED_SQL = Path(__file__).parent / "fixtures" / "seed.sql"

@pytest.fixture(scope="session")
def db_connection():
    conn = psycopg2.connect(DATABASE_URL_SYNC)
    yield conn
    conn.close()

@pytest.fixture(scope="function")
def seed_db(db_connection):
    """Load seed data before each test, truncate after."""
    with db_connection.cursor() as cur:
        cur.execute(SEED_SQL.read_text())
    db_connection.commit()
    yield
    with db_connection.cursor() as cur:
        cur.execute("""
            TRUNCATE TABLE release_events, superfund_sites, census_county,
                           facilities, chemicals RESTART IDENTITY CASCADE;
        """)
    db_connection.commit()

@pytest.fixture(scope="session")
def api_client():
    app = create_app()
    return TestClient(app)

@pytest.fixture(scope="session")
def browser_base_url():
    # NOTE: pytest-playwright injects its own `base_url` from --base-url (set in pyproject.toml).
    # This fixture is provided for step helpers that cannot use pytest-playwright's page fixture
    # directly. Prefer page.goto("/") in E2E step functions rather than page.goto(browser_base_url)
    # to avoid constructing a double-path URL when --base-url is already set.
    return os.getenv("TEST_BASE_URL", "http://localhost:3000")

@pytest.fixture
def context():
    """Shared mutable dict for passing response state between pytest-bdd step functions.
    Must be function-scoped (default) so each test scenario starts with a clean dict.
    Usage in steps: context["response"] = ...; assert context["response"].status_code == 200"""
    return {}
```

---

## Section 9: Known Good Assertion Values

Quick reference for test assertions — values that must match exactly.

| Scenario | Field                              | Expected Value                  | Source                        |
|----------|------------------------------------|---------------------------------|-------------------------------|
| T-01     | Bethlehem Steel 2008 total release | `12,485 lbs`                    | Seed (realistic; on-site Field 65) |
| T-01     | Bethlehem Steel chemical name      | `LEAD COMPOUNDS`                | Seed                          |
| T-01     | Bethlehem Steel chemical cas_number| `null`                          | TRI N420 compound (no CAS)    |
| T-01     | Bethlehem Steel unit_of_measure    | `Pounds`                        | TRI Field 50                  |
| T-01     | Bethlehem Steel form_type          | `R`                             | TRI Field 49 (Form R with quantities) |
| T-03     | Robinson NV copper total           | `8,205 lbs`                     | **UCD 2011 exact**            |
| T-03     | Robinson NV copper medium          | `land` (land_release_lbs=8205)  | **UCD 2011 exact**            |
| T-03     | Robinson NV facility ID            | `89319BHPCP7MILE`               | **UCD 2011 exact**            |
| T-03     | Robinson NV chemical name          | `COPPER` (NOT copper compounds) | **UCD 2011 facilitator note** |
| T-03     | Robinson NV unit_of_measure        | `Pounds`                        | TRI Field 50                  |
| T-03     | Robinson NV form_type              | `R`                             | TRI Field 49                  |
| T-04     | AVTEX FIBERS EPA ID                | `VAD070358684`                  | **UCD 2011 exact**            |
| T-04     | AVTEX FIBERS city                  | `FRONT ROYAL`                   | **UCD 2011 exact**            |
| T-05     | Warren County VA pct_under_18      | `24.7%`                         | Seed (Census 2000 approx.)    |
| T-07     | SC largest chlorine total          | `85,000 lbs`                    | Seed                          |
| T-07     | National largest chlorine total    | `342,500 lbs`                   | Seed                          |
| T-07     | National largest chlorine facility | `ENTERPRISE GAS PROCESSING LLC` | Seed                          |
| All      | Comma formatting: 8205             | Must render as `8,205`          | UCD 2011 §"Commas in Numbers" |
| All      | Comma formatting: 12485            | Must render as `12,485`         | UCD 2011 §"Commas in Numbers" |
| All      | unit_of_measure for all 14 seed events | `Pounds`                   | All seed chemicals are non-dioxin |
| All      | form_type for all 14 seed events   | `R`                             | All seed events are Form R (with quantities) |

---

## Section 10: `GET /api/v1/meta` Behavior Against Seed Data

The `GET /api/v1/meta` endpoint (added in [TOXMAP_API_CONTRACT.md §17](../api/TOXMAP_API_CONTRACT.md)) queries the live `release_events` and `facilities` tables. Against the seed data defined in this document, it returns:

```json
{
  "vintage_label": "unknown",
  "build_date": "unknown",
  "available_years": [2006, 2007, 2008],
  "latest_year": 2008,
  "total_facility_count": 7,
  "total_release_event_count": 14,
  "source": "fastapi-dev"
}
```

**Why `"unknown"` for `vintage_label` and `build_date`?**

The seed data does not insert an ingestion metadata record (there is no `ingestion_metadata` table in the test seed). The FastAPI `/api/v1/meta` implementation must fall back to `"unknown"` when no metadata record exists, per the contract invariant: *"return `"unknown"` if the ingestion metadata record is missing."*

This is intentional and acceptable for test execution. The `Feature 9` Gherkin scenarios assert only that `vintage_label` is a non-null string — not that it has a specific value — so all tests pass with `"unknown"`.

**In production / real ingestion runs**, the `vintage_label` is set by passing `--vintage "October 2024 freeze"` to the ingestion CLI, which writes the value to an `ingestion_metadata` table (or equivalent persistent store). The seed does not simulate this.

**Adding a known vintage to a specific test:** If a test needs to assert an exact `vintage_label`, use a `psql` statement in the test setup to insert a metadata record, or use a pytest fixture that sets the value directly. Do not add it to `seed.sql` — the fallback to `"unknown"` is the correct baseline behavior.

