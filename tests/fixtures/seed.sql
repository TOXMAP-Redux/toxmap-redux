-- ============================================================
-- TOXMAP Test Seed Data
-- Load with: psql -U postgres -d toxmap -f tests/fixtures/seed.sql
-- Source: docs/testing/TOXMAP_TEST_SEED_DATA.md §7
--
-- CRITICAL: Do NOT modify the values in this file without human approval.
-- Two values are cited from a peer-reviewed NLM study and must stay exact:
--   89319BHPCP7MILE → COPPER → 8205.0 lbs → land → year 2008 (T-03)
--   VAD070358684 → AVTEX FIBERS INC → FRONT ROYAL, VA (T-04)
--
-- IDEMPOTENT: This script deletes ONLY the specific seed rows before inserting,
-- preserving any real ingested data. Safe to run multiple times.
-- ============================================================

BEGIN;

-- Delete only the specific seed rows (preserves real ingested data).
-- Order matters: delete child rows before parent rows (foreign key constraints).
-- This matches the conftest.py teardown logic exactly.

-- Release events for seed facilities
DELETE FROM release_events WHERE facility_id IN (
  SELECT id FROM facilities WHERE tri_facility_id IN (
    '21219BTHLS3RD',   -- Bethlehem Steel (T-01)
    '89319BHPCP7MILE', -- Robinson Nevada (T-03)
    '22630FRTRY0001',  -- Front Royal Plastics
    '29801DSTLR0001',  -- Borden Chemicals
    '70663ENTGR0001',  -- Enterprise Gas
    '77536EXXO00001',  -- ExxonMobil
    '77536LYND00001',  -- LyondellBasell
    '99501ANCHO0001',  -- Alaska Mining (CONUS filter test)
    '22630SMRLG0001'   -- Small Release Facility (green tier test)
  )
);

-- Seed facilities
DELETE FROM facilities WHERE tri_facility_id IN (
  '21219BTHLS3RD',
  '89319BHPCP7MILE',
  '22630FRTRY0001',
  '29801DSTLR0001',
  '70663ENTGR0001',
  '77536EXXO00001',
  '77536LYND00001',
  '99501ANCHO0001',
  '22630SMRLG0001'
);

-- Seed Superfund sites (UCD-17: all 3 status types for symbol regression tests)
DELETE FROM superfund_sites WHERE epa_id IN (
  'VAD070358684',  -- AVTEX FIBERS INC (NPL Final)
  'VAD980554587',  -- ARLINGTON SCRAP YARD (NPL Final)
  'VAD987654321',  -- TEST PROPOSED SITE (Proposed)
  'VAD123456789'   -- TEST DELETED SITE (Deleted)
);

-- Seed census counties
DELETE FROM census_county WHERE fips_code IN (
  '51187',  -- Warren County, VA
  '48201',  -- Harris County, TX
  '45003'   -- Aiken County, SC
);

-- Seed chemicals (only if no real data references them)
DELETE FROM chemicals WHERE id IN (1, 2, 3, 4, 5, 6)
  AND NOT EXISTS (
    SELECT 1 FROM release_events re
    JOIN facilities f ON re.facility_id = f.id
    WHERE re.chemical_id = chemicals.id
    AND f.tri_facility_id NOT IN (
      '21219BTHLS3RD', '89319BHPCP7MILE', '22630FRTRY0001',
      '29801DSTLR0001', '70663ENTGR0001', '77536EXXO00001', '77536LYND00001',
      '99501ANCHO0001', '22630SMRLG0001'
    )
  );

-- 1. Chemicals
-- atsdr_url format: wwwn.cdc.gov/TSP/substances/ToxSubstance.aspx?toxid=N
--   toxids verified against wwwn.cdc.gov/TSP/substances/SubstanceAZ.aspx
--   using the interactive A-Z index (JavaScript-rendered); verified 2026-07-27.
--   toxid values are opaque ATSDR database IDs — they do NOT follow CERCLA rank.
-- pubchem_url: /compound/<CAS> for all substances (CAS 7439-92-1 used for
--   LEAD COMPOUNDS since that entry has no single CAS number).
INSERT INTO chemicals (id, cas_number, name, category, atsdr_url, pubchem_url) VALUES
  (1, NULL,         'LEAD COMPOUNDS',  'Heavy Metals',               'https://wwwn.cdc.gov/TSP/substances/ToxSubstance.aspx?toxid=22',  'https://pubchem.ncbi.nlm.nih.gov/compound/7439-92-1'),
  (2, '7440-50-8',  'COPPER',          'Heavy Metals',               'https://wwwn.cdc.gov/TSP/substances/ToxSubstance.aspx?toxid=37',  'https://pubchem.ncbi.nlm.nih.gov/compound/7440-50-8'),
  (3, '100-42-5',   'STYRENE',         'Volatile Organic Compounds', 'https://wwwn.cdc.gov/TSP/substances/ToxSubstance.aspx?toxid=74',  'https://pubchem.ncbi.nlm.nih.gov/compound/7501'),
  (4, '7782-50-5',  'CHLORINE',        'Halogens',                   'https://wwwn.cdc.gov/TSP/substances/ToxSubstance.aspx?toxid=36',  'https://pubchem.ncbi.nlm.nih.gov/compound/24526'),
  (5, '71-43-2',    'BENZENE',         'Volatile Organic Compounds', 'https://wwwn.cdc.gov/TSP/substances/ToxSubstance.aspx?toxid=14',  'https://pubchem.ncbi.nlm.nih.gov/compound/241'),
  (6, '7664-41-7',  'AMMONIA',         'Inorganic Compounds',        'https://wwwn.cdc.gov/TSP/substances/ToxSubstance.aspx?toxid=2',   'https://pubchem.ncbi.nlm.nih.gov/compound/222')
ON CONFLICT (id) DO UPDATE SET
  cas_number = EXCLUDED.cas_number,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  atsdr_url = EXCLUDED.atsdr_url,
  pubchem_url = EXCLUDED.pubchem_url;

-- 2. Facilities
INSERT INTO facilities (id, tri_facility_id, name, address, city, state_code, zip_code, county, naics_code, naics_desc, location) VALUES
  (1, '21219BTHLS3RD',   'BETHLEHEM STEEL CORP - SPARROWS POINT', '3200 SPARROWS POINT RD',      'SPARROWS POINT', 'MD', '21219', 'BALTIMORE',  '331110', 'Iron and Steel Mills',                    ST_GeomFromText('POINT(-76.4785 39.2197)', 4326)),
  (2, '89319BHPCP7MILE', 'ROBINSON NEVADA MINING CO',             '7 MILES W OF ELY ON HWY 50',  'RUTH',           'NV', '89319', 'WHITE PINE', '212234', 'Copper Ore and Nickel Ore Mining',        ST_GeomFromText('POINT(-115.0319 39.2919)', 4326)),
  (3, '22630FRTRY0001',  'FRONT ROYAL PLASTICS INC',              '450 KENDRICK LN',              'FRONT ROYAL',    'VA', '22630', 'WARREN',     '326130', 'Laminated Plastics Plate Manufacturing',  ST_GeomFromText('POINT(-78.1856 38.9241)', 4326)),
  (4, '29801DSTLR0001',  'BORDEN CHEMICALS AND PLASTICS INC',     '1000 BORDEN DR',               'AIKEN',          'SC', '29801', 'AIKEN',      '325211', 'Plastics Material Manufacturing',         ST_GeomFromText('POINT(-81.7198 33.5601)', 4326)),
  (5, '70663ENTGR0001',  'ENTERPRISE GAS PROCESSING LLC',         '4500 ENTERPRISE BLVD',         'SULPHUR',        'LA', '70663', 'CALCASIEU',  '486210', 'Pipeline Transportation of Natural Gas',  ST_GeomFromText('POINT(-93.2044 30.1944)', 4326)),
  (6, '77536EXXO00001',  'EXXONMOBIL CHEMICAL PLANT',             '5200 BAYWAY DR',               'BAYTOWN',        'TX', '77536', 'HARRIS',     '324110', 'Petroleum Refineries',                    ST_GeomFromText('POINT(-95.0215 29.7424)', 4326)),
  (7, '77536LYND00001',  'LYONDELLBASELL REFINERY',               '12000 LAWNDALE ST',            'HOUSTON',        'TX', '77536', 'HARRIS',     '324110', 'Petroleum Refineries',                    ST_GeomFromText('POINT(-95.2100 29.7380)', 4326)),
  (8, '99501ANCHO0001',  'ALASKA MINING CO',                      '100 NORTHERN BLVD',            'ANCHORAGE',      'AK', '99501', 'ANCHORAGE',  '212234', 'Copper Ore and Nickel Ore Mining',        ST_GeomFromText('POINT(-149.9003 61.2181)', 4326)),
  (9, '22630SMRLG0001',  'SMALL RELEASE FACILITY',                '200 GREEN TIER WAY',           'FRONT ROYAL',    'VA', '22630', 'WARREN',     '325199', 'All Other Basic Organic Chemical Mfg',    ST_GeomFromText('POINT(-78.1900 38.9150)', 4326))
ON CONFLICT (id) DO UPDATE SET
  tri_facility_id = EXCLUDED.tri_facility_id,
  name = EXCLUDED.name,
  address = EXCLUDED.address,
  city = EXCLUDED.city,
  state_code = EXCLUDED.state_code,
  zip_code = EXCLUDED.zip_code,
  county = EXCLUDED.county,
  naics_code = EXCLUDED.naics_code,
  naics_desc = EXCLUDED.naics_desc,
  location = EXCLUDED.location;

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
  (8, 2, 2008,  3500.0,     0.0,     0.0, 3500.0,    0.0, 'Pounds', 'R'),
  (9, 6, 2008,   450.0,   400.0,    50.0,    0.0,    0.0, 'Pounds', 'R');

-- 4. Superfund sites (UCD-17: all 3 status types for symbol regression tests)
-- NPL = Final (filled red square), Proposed = pending NPL (red diamond), Deleted = removed from NPL (gray X-square)
INSERT INTO superfund_sites (id, epa_id, name, address, city, state_code, zip_code, county, status, hrs_score, npl_date, epa_progress_url, contaminants, location) VALUES
  (1, 'VAD070358684', 'AVTEX FIBERS INC',     'BOX 1169 KENDRICK LN', 'FRONT ROYAL', 'VA', '22630', 'WARREN',    'NPL',      50.51, '1983-09-08', 'https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.Cleanup&id=0302388', ARRAY['STYRENE','CARBON DISULFIDE','ZINC'],  ST_GeomFromText('POINT(-78.1942 38.9179)', 4326)),
  (2, 'VAD980554587', 'ARLINGTON SCRAP YARD', '4200 LEE HWY',         'ARLINGTON',   'VA', '22204', 'ARLINGTON', 'NPL',      28.74, '1989-02-21', 'https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.Cleanup&id=0304032', ARRAY['LEAD COMPOUNDS','CADMIUM'],           ST_GeomFromText('POINT(-77.1089 38.8823)', 4326)),
  (3, 'VAD987654321', 'TEST PROPOSED SITE',   '100 PROPOSED WAY',     'RICHMOND',    'VA', '23220', 'RICHMOND',  'Proposed', 32.50, NULL,         NULL,                                                                                            ARRAY['BENZENE','TOLUENE'],                  ST_GeomFromText('POINT(-77.4360 37.5407)', 4326)),
  (4, 'VAD123456789', 'TEST DELETED SITE',    '200 CLEANUP COMPLETE', 'NORFOLK',     'VA', '23510', 'NORFOLK',   'Deleted',  45.00, '1985-06-10', 'https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.Cleanup&id=0300001', ARRAY['ARSENIC','MERCURY'],                  ST_GeomFromText('POINT(-76.2859 36.8508)', 4326))
ON CONFLICT (id) DO UPDATE SET
  epa_id = EXCLUDED.epa_id,
  name = EXCLUDED.name,
  address = EXCLUDED.address,
  city = EXCLUDED.city,
  state_code = EXCLUDED.state_code,
  zip_code = EXCLUDED.zip_code,
  county = EXCLUDED.county,
  status = EXCLUDED.status,
  hrs_score = EXCLUDED.hrs_score,
  npl_date = EXCLUDED.npl_date,
  epa_progress_url = EXCLUDED.epa_progress_url,
  contaminants = EXCLUDED.contaminants,
  location = EXCLUDED.location;

-- 5. Census county demographics
INSERT INTO census_county (id, fips_code, name, state_code, census_year, total_pop, median_income, pct_under_18, pct_over_65, pct_nonwhite, cancer_mortality_female_per_100k, cancer_mortality_male_per_100k, heart_disease_mortality_per_100k, boundary) VALUES
  (1, '51187', 'Warren County', 'VA', 2000,   31584,  41246.00, 24.7, 11.2,  8.4, 148.7, 175.2, 189.4, ST_GeomFromText('POLYGON((-78.40 38.76, -78.40 38.99, -78.00 38.99, -78.00 38.76, -78.40 38.76))', 4326)),
  (2, '48201', 'Harris County', 'TX', 2000, 3400578,  42890.00, 28.3,  7.9, 55.4, 162.4, 194.8, 215.6, ST_GeomFromText('POLYGON((-95.79 29.52, -95.79 30.11, -94.91 30.11, -94.91 29.52, -95.79 29.52))', 4326)),
  (3, '45003', 'Aiken County',  'SC', 2000,  142552,  38100.00, 25.1, 13.6, 34.2, 155.3, 186.1, 228.7, ST_GeomFromText('POLYGON((-81.97 33.35, -81.97 33.84, -81.42 33.84, -81.42 33.35, -81.97 33.35))', 4326))
ON CONFLICT (id) DO UPDATE SET
  fips_code = EXCLUDED.fips_code,
  name = EXCLUDED.name,
  state_code = EXCLUDED.state_code,
  census_year = EXCLUDED.census_year,
  total_pop = EXCLUDED.total_pop,
  median_income = EXCLUDED.median_income,
  pct_under_18 = EXCLUDED.pct_under_18,
  pct_over_65 = EXCLUDED.pct_over_65,
  pct_nonwhite = EXCLUDED.pct_nonwhite,
  cancer_mortality_female_per_100k = EXCLUDED.cancer_mortality_female_per_100k,
  cancer_mortality_male_per_100k = EXCLUDED.cancer_mortality_male_per_100k,
  heart_disease_mortality_per_100k = EXCLUDED.heart_disease_mortality_per_100k,
  boundary = EXCLUDED.boundary;

COMMIT;
