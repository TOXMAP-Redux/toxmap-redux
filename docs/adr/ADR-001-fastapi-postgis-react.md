# ADR-001: Python · FastAPI · PostGIS · React/MapLibre

| Field             | Value                                                                                                                                     |
|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| **ID**            | ADR-001                                                                                                                                   |
| **Title**         | Python FastAPI + PostGIS + React/MapLibre as Primary Architecture                                                                         |
| **Date**          | 2026-07-15                                                                                                                                |
| **Status**        | **Accepted**                                                                                                                              |
| **Deciders**      | Architecture Review                                                                                                                       |
| **NLM Sources**   | [PMC2703818](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2703818/) · [PMC4251466](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4251466/) |
| **Supersedes**    | —                                                                                                                                         |
| **Superseded by** | —                                                                                                                                         |

---

## Context

We are building an open-source clone of the NLM's TOXMAP application (decommissioned 2019). Per the authoritative NLM peer-reviewed articles ([PMC2703818](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2703818/), [PMC4251466](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4251466/)), the original system:

- Was built on **ESRI ArcIMS** (2004) then upgraded to **ESRI ArcGIS for Server** (2013) — both proprietary and expensive
- Used **MySQL** initially, then migrated to **PostgreSQL** in 2013 (validating our DB choice)
- Used a **Java/Apache Struts** backend, then **Adobe Flash/Flex (ActionScript)** client — both now EOL
- Served TRI data, **Superfund/NPL sites**, **U.S. Census demographic overlays**, **Canadian NPRI**, nuclear plant locations, and congressional district boundaries

Our clone replaces the proprietary ESRI stack with open-source equivalents, the Flash/Flex client with React/MapLibre GL, and extends to the full feature set described in the NLM source record.

The system must:

1. Ingest ~4M+ historical EPA TRI records, Superfund/NPL sites, and optional Census demographic data
2. Serve geospatial queries (radius search, bounding box, Superfund proximity) with sub-500ms p95 latency
3. Render an interactive map with color-coded facility pins (by release volume), cluster aggregation, and toggleable overlay layers
4. Display facility detail with bar charts (top chemicals by release) and 15-year trend lines
5. Be fully self-hostable via Docker and welcoming to open-source contributors

The team evaluated three architecture contenders documented in the [Tech Stack Analysis](TOXMAP_TECH_STACK_ANALYSIS.md). This ADR documents the recommended option.

---

## Decision

**Adopt the following stack:**

```
Backend API:       Python 3.12 + FastAPI (async)
Database:          PostgreSQL 16 + PostGIS 3.4
ORM / Geo:         SQLAlchemy 2.0 (async) + GeoAlchemy2
Data Ingestion:    pandas 2.x + geopandas 0.14
Frontend:          React 18 + MapLibre GL JS (via react-map-gl)
Map Tiles:         Protomaps (self-hosted PMTiles) or OpenFreeMap
Charts:            Recharts
Styling:           Tailwind CSS
Containerization:  Docker + Docker Compose
CI/CD:             GitHub Actions
```

---

## UX Architecture Decisions (UCD Inc. Usability Study, 2011)

> These decisions are **non-negotiable frontend constraints** derived directly from the 2011 usability study conducted by User-Centered Design, Inc. for NLM. See [TOXMAP_TECH_STACK_ANALYSIS.md §8](TOXMAP_TECH_STACK_ANALYSIS.md#8-ux-lessons-learned-ucd-inc-usability-study-2011).

| Decision | Rationale (from study) |
|----------|------------------------|
| **Single collapsible sidebar** — Search Results and Map Contents never shown simultaneously | Critical finding: dual panels caused users to interact with inactive panel and miss active results |
| **Search results scoped to current map viewport** — re-fetched on map move/zoom | 500-row paged table with empty placeholder rows was the most confusing element in the entire study |
| **State dropdown includes "Limit to state" checkbox** — state doesn't only zoom | Users consistently expected state selection to filter, not just pan |
| Label search panel **"Search Chemical Releases by Location"** (not "Quick Search") | "Quick Search" didn't imply chemical + location; users went to "Chemical Information" instead |
| Label census panel **"US Census & Health Data"** (not "Demographics") | Users did not expect mortality data under "Demographics" |
| **Labeled icon toolbar** — no separate redundant text menus | Users explored text menus first but wanted icons after familiarity; both was redundant and confusing |
| **Inline demographic legend values** with units (%, $, years, people) | Mouse-over-only legend required memory or extra interaction; units were missing entirely |
| **Co-occurrence disclaimer only on mortality tab** | Disclaimer was shown on all demographic tabs; only relevant for mortality data |
| **Distinct icon shapes per site type** — TRI (circle), Superfund (diamond), hospital (blue H) | Red cross for hospitals was confused with red dot for Superfund sites |
| **"(latest year)" label** on most-recent year in layer toggles | Users wondered why 2008 was shown; didn't know it was the latest vetted data |
| **Comma-formatted numbers** throughout (8,205 lbs, not 8205) | Direct usability complaint; impairs readability of release quantities |
| **Close link at bottom of facility popup** in addition to corner X | Corner close button was frequently scrolled off-screen; users couldn't dismiss popup |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser Client                        │
│  React 18 · MapLibre GL · react-map-gl · Recharts           │
│  Tailwind CSS                                                │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS (REST/JSON)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│                                                             │
│  ┌───────────────┐  ┌───────────────┐   ┌─────────────────┐ │
│  │  Facilities   │  │   Chemicals   │   │   Time Series   │ │
│  │   Router      │  │    Router     │   │     Router      │ │
│  └───────┬───────┘  └───────┬───────┘   └────────┬────────┘ │
│          └──────────────────┼────────────────────┘          │
│                             ▼                               │
│              ┌──────────────────────────┐                   │
│              │    Service Layer         │                   │
│              │  (FacilityService,       │                   │
│              │   ChemicalService, etc.) │                   │
│              └──────────────┬───────────┘                   │
│                             │ SQLAlchemy (async)            │
└─────────────────────────────┼───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL 16 + PostGIS 3.4                    │
│                                                             │
│  facilities          release_events        chemicals        │
│  ───────────         ──────────────        ─────────        │
│  id (PK)             id (PK)               id (PK)          │
│  tri_facility_id     facility_id (FK)      cas_number (NULL │
│  name                chemical_id (FK)        for N-prefix   │
│  location (POINT)    reporting_year          categories)    │
│  frs_id              total_release_lbs     name             │
│  naics_code          air_release_lbs       category         │
│  primary_sic         water_release_lbs                      │
│                      land_release_lbs                       │
│                      underground_release_lbs                │
│                      off_site_lbs                           │
│                      unit_of_measure                        │
│                      form_type                              │
│                                                             │
│  Indexes:                                                   │
│  GIST index on facilities.location                          │
│  B-tree on release_events.reporting_year                    │
│  B-tree on release_events.chemical_id                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   Ingestion Pipeline                        │
│   (runs on schedule or manually via CLI)                    │
│                                                             │
│   EPA TRI CSV ──► pandas ──► geopandas ──► PostGIS          │
│                   parse      geocode       bulk insert      │
│                   clean      reproject     (ST_GeomFromText)│
└─────────────────────────────────────────────────────────────┘
```

---

## API Design (Key Endpoints)

```
# TRI Facilities — viewport-scoped (UCD 2011: no empty rows)
GET  /api/v1/facilities
     ?lat=47.6&lon=-122.3&radius_miles=25
     &year=2022&chemical=lead&naics=325&medium=air
     &bbox=-122.5,47.4,-122.1,47.8      # viewport bounding box for table results
     &state=WA&restrict_to_state=true   # UCD 2011: state restricts, not just zooms
     → GeoJSON FeatureCollection (color-coded by total_release_lbs)

# TRI Facilities — browse mode (all facilities, no radius constraint)
# Added 2026-07-28: Used for initial map view before any search is submitted.
# MapLibre handles viewport subsetting client-side from the full ~22k dataset.
GET  /api/v1/facilities/browse
     ?year=2022&chemical=lead&medium=air&state=WA
     → GeoJSON FeatureCollection (same shape as /facilities)

GET  /api/v1/facilities/{tri_facility_id}
     → Facility detail JSON

GET  /api/v1/facilities/{tri_facility_id}/releases
     ?from_year=2000&to_year=2024&medium=air
     → Time series array (15-year trend; NLM bar chart feature)

# Chemical lookup with live auto-complete (NLM + UCD 2011)
GET  /api/v1/chemicals
     → Full chemical list with CAS numbers
GET  /api/v1/chemicals/search?q=merc
     → Auto-complete suggestions (drives "Search Chemical Releases by Location" panel)

# Largest release queries (UCD 2011 Task 5 — state vs. nationwide comparison)
GET  /api/v1/releases/largest?chemical=chlorine&state=SC
     → Top facility in SC for chlorine
GET  /api/v1/releases/largest?chemical=chlorine
     → Top facility nationwide for chlorine

# Superfund / NPL overlay (NLM 2006 enhancement)
# Browse mode: all Superfund sites, no radius constraint (added 2026-07-28)
# Used for the always-on diamond layer on the map
GET  /api/v1/superfund/browse
     ?status=NPL&state=CA
     → GeoJSON with all sites (MapLibre handles viewport subsetting)
GET  /api/v1/superfund
     ?lat=47.6&lon=-122.3&radius_miles=25
     → GeoJSON with HRS score, cleanup status, contaminants
GET  /api/v1/superfund/{epa_id}
     → Site detail with ATSDR/CDC document links

# Census demographic overlays (NLM 2006–2013; UCD 2011 "US Census & Health Data")
GET  /api/v1/demographics/county?state=WA
     → County GeoJSON with income, age, population, race attributes + units metadata
GET  /api/v1/demographics/tract?county_fips=53033
     → Census tract GeoJSON

# Optional layers (NLM 2013 redesign)
GET  /api/v1/layers/npri?province=ON
     → Canadian NPRI facilities GeoJSON
GET  /api/v1/layers/nuclear
     → U.S. commercial nuclear power plants GeoJSON
GET  /api/v1/layers/congressional-districts?state=WA
     → Congressional district boundaries GeoJSON

# Export — CSV + map snapshot (UCD 2011 user request: not just browser print)
GET  /api/v1/export/csv
     ?lat=47.6&lon=-122.3&radius_miles=25&year=2022&medium=air
     → Streaming CSV download
GET  /api/v1/export/map-metadata
     → Returns current filter state for client-side map image export
```

---

## Data Model (Core Tables)

```sql
-- PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- ── TRI Core ──────────────────────────────────────────────────────────────────

CREATE TABLE facilities (
    id              SERIAL PRIMARY KEY,
    tri_facility_id VARCHAR(15) NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    address         TEXT,
    city            TEXT,
    state_code      CHAR(2),
    zip_code        VARCHAR(10),
    county          TEXT,
    naics_code      VARCHAR(6),
    naics_desc      TEXT,
    -- frs_id: EPA Facility Registry Service ID (TRI Field 3).
    -- Enables cross-program linkage to RCRA, CWA, and CERCLIS datasets.
    frs_id          VARCHAR(12),
    -- primary_sic: original SIC code for pre-2006 data (Fields 24-29).
    -- For RY 1987-2005, EPA assigned NAICS retroactively via crosswalk;
    -- the original SIC code is more historically accurate for those years.
    primary_sic     VARCHAR(4),
    location        GEOMETRY(POINT, 4326) NOT NULL
);

CREATE INDEX idx_facilities_location ON facilities USING GIST (location);
CREATE INDEX idx_facilities_state    ON facilities (state_code);

CREATE TABLE chemicals (
    id          SERIAL PRIMARY KEY,
    -- cas_number is NULL for TRI compound categories (e.g. N420 = LEAD COMPOUNDS,
    -- N100 = COPPER COMPOUNDS). These TRI categories use N-prefix IDs (Field 39),
    -- not CAS numbers. The NOT NULL constraint was removed to accommodate them.
    -- The partial unique index prevents duplicates on non-null CAS values only.
    cas_number  VARCHAR(12),
    name        TEXT NOT NULL,
    category    TEXT,
    atsdr_url   TEXT,    -- ATSDR ToxFAQs page for this chemical (may be null)
    pubchem_url TEXT     -- PubChem compound page (may be null)
    -- name is the auto-complete source (NLM original feature)
);

-- Partial unique index: allows multiple NULL cas_number rows (compound categories)
-- while still enforcing uniqueness among rows that have a real CAS number.
CREATE UNIQUE INDEX idx_chemicals_cas_number ON chemicals (cas_number)
    WHERE cas_number IS NOT NULL;

CREATE TABLE release_events (
    id                SERIAL PRIMARY KEY,
    facility_id       INTEGER NOT NULL REFERENCES facilities(id),
    chemical_id       INTEGER NOT NULL REFERENCES chemicals(id),
    reporting_year    SMALLINT NOT NULL,

    -- total_release_lbs: on-site release total (TRI Field 65 = ON-SITE RELEASE TOTAL).
    -- This equals the sum of the four medium breakdown columns below.
    -- Used for color-band assignment, bar charts, and CSV export.
    -- NOTE: This is Field 65, NOT Field 107 (TOTAL RELEASES = on-site + off-site).
    -- Do not map Field 107 here — it would inflate values for facilities with off-site transfers.
    total_release_lbs NUMERIC(14, 2),

    -- Medium breakdown (NLM original: air/water/land/underground injection filter).
    -- Source: Form R Section 5, individual release-to-medium columns.
    -- air_release_lbs = fugitive air (Field 51) + stack air (Field 52).
    -- underground_release_lbs = Class I wells (Field 55) + Class II-V wells (Field 56).
    -- land_release_lbs = computed sum of Fields 57–64 (see LAND_RELEASE_FIELDS in tri_parser.py).
    air_release_lbs         NUMERIC(14, 2),
    water_release_lbs       NUMERIC(14, 2),  -- Field 53 (single column, no aggregation needed)
    land_release_lbs        NUMERIC(14, 2),
    underground_release_lbs NUMERIC(14, 2),

    -- off_site_lbs: off-site release total (TRI Field 88 = OFF-SITE RELEASE TOTAL).
    -- Stored for analytical completeness; not displayed in the current UI.
    off_site_lbs            NUMERIC(14, 2),

    -- unit_of_measure: CRITICAL — dioxin/dioxin-like compounds (classification = 'DIOXIN',
    -- compound N150) are reported in GRAMS. All other chemicals are in POUNDS.
    -- The _lbs column names are accurate only for unit_of_measure = 'Pounds' rows.
    -- Source: TRI Field 50 (UNIT OF MEASURE). Values: 'Pounds' or 'Grams'.
    unit_of_measure VARCHAR(6) DEFAULT 'Pounds',

    -- form_type: TRI Field 49. 'R' = Form R (full release data). 'A' = Form A Certification
    -- (facility certified below threshold; all release quantity columns are zero by definition,
    -- not because zero releases occurred). Required to distinguish Form A zeros from
    -- Form R-reported zeros per Data Integrity Rule 3.
    form_type CHAR(1) DEFAULT 'R'
);

CREATE INDEX idx_releases_facility ON release_events (facility_id);
CREATE INDEX idx_releases_year     ON release_events (reporting_year);
CREATE INDEX idx_releases_chemical ON release_events (chemical_id);

-- ── Superfund / NPL (NLM 2006 enhancement) ───────────────────────────────────

CREATE TABLE superfund_sites (
    id                  SERIAL PRIMARY KEY,
    epa_id              VARCHAR(12) NOT NULL UNIQUE,   -- e.g. WAD009248671
    name                TEXT NOT NULL,
    address             TEXT,     -- street address (e.g. "BOX 1169 KENDRICK LN")
    city                TEXT,
    state_code          CHAR(2),
    county              TEXT,
    zip_code            VARCHAR(10),
    status              TEXT,     -- 'NPL', 'CERCLIS', 'Deleted', etc.
    hrs_score           NUMERIC(5, 2),  -- Hazard Ranking System score (0–100)
    npl_date            DATE,
    -- EPA CERCLIS numeric site ID differs from epa_id format — must be stored, not computed
    epa_progress_url    TEXT,     -- https://cumulis.epa.gov/supercpad/SiteProfiles/...
    contaminants        TEXT[],   -- array of primary contaminants
    location            GEOMETRY(POINT, 4326) NOT NULL
);

CREATE INDEX idx_superfund_location  ON superfund_sites USING GIST (location);
CREATE INDEX idx_superfund_state     ON superfund_sites (state_code);

-- ── Census Demographics (NLM 2006–2013 enhancement) ──────────────────────────

CREATE TABLE census_county (
    id              SERIAL PRIMARY KEY,
    fips_code       CHAR(5) NOT NULL UNIQUE,   -- state+county FIPS
    name            TEXT NOT NULL,
    state_code      CHAR(2),
    census_year     SMALLINT NOT NULL,
    total_pop       INTEGER,
    median_income   NUMERIC(10, 2),
    pct_under_18    NUMERIC(5, 2),
    pct_over_65     NUMERIC(5, 2),
    pct_nonwhite    NUMERIC(5, 2),
    -- Health / mortality overlays (NLM 2006–2013 enhancement; T-09)
    cancer_mortality_female_per_100k  NUMERIC(6, 1),
    cancer_mortality_male_per_100k    NUMERIC(6, 1),
    heart_disease_mortality_per_100k  NUMERIC(6, 1),
    boundary        GEOMETRY(MULTIPOLYGON, 4326)
);

CREATE INDEX idx_county_boundary ON census_county USING GIST (boundary);

-- ── Optional Layers (NLM 2013 redesign) ──────────────────────────────────────

CREATE TABLE nuclear_plants (
    id          SERIAL PRIMARY KEY,
    plant_name  TEXT NOT NULL,
    operator    TEXT,
    state_code  CHAR(2),
    status      TEXT,   -- 'Operating', 'Shutdown', etc.
    location    GEOMETRY(POINT, 4326) NOT NULL
);

CREATE TABLE npri_facilities (
    id              SERIAL PRIMARY KEY,
    npri_id         VARCHAR(12) NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    province        CHAR(2),
    location        GEOMETRY(POINT, 4326) NOT NULL
);
```

---

## Project Structure

```
toxmap/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app factory
│   │   ├── config.py             # Settings (pydantic-settings)
│   │   ├── database.py           # Async SQLAlchemy engine
│   │   ├── models/               # SQLAlchemy ORM models
│   │   │   ├── facility.py
│   │   │   ├── chemical.py
│   │   │   ├── release_event.py
│   │   │   ├── superfund_site.py   # NLM 2006 enhancement
│   │   │   ├── census_county.py    # NLM 2006-2013 enhancement
│   │   │   ├── nuclear_plant.py    # NLM 2013 redesign
│   │   │   └── npri_facility.py    # NLM 2013 redesign (Canadian)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   │   ├── facility.py
│   │   │   ├── release.py
│   │   │   ├── superfund.py
│   │   │   └── demographics.py
│   │   ├── routers/              # FastAPI route handlers
│   │   │   ├── facilities.py
│   │   │   ├── chemicals.py
│   │   │   ├── superfund.py
│   │   │   ├── demographics.py
│   │   │   ├── layers.py         # nuclear, npri, congressional
│   │   │   └── export.py
│   │   └── services/             # Business logic
│   │       ├── facility_service.py
│   │       ├── release_service.py
│   │       ├── superfund_service.py
│   │       └── demographics_service.py
│   ├── ingestion/
│   │   ├── tri_ingest.py         # EPA TRI CSV → PostGIS
│   │   ├── superfund_ingest.py   # EPA NPL/CERCLIS → PostGIS
│   │   ├── census_ingest.py      # Census TIGER → PostGIS
│   │   ├── npri_ingest.py        # Canadian NPRI CSV → PostGIS
│   │   ├── tri_parser.py         # pandas TRI CSV parser
│   │   └── geocoder.py           # Coordinate normalization
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Map/                    # MapLibre GL map component
│   │   │   ├── Sidebar/                # SINGLE collapsible panel (UCD 2011)
│   │   │   │   ├── SearchPanel/        # "Search Chemical Releases by Location" (not "Quick Search")
│   │   │   │   │   ├── ChemicalAutocomplete/   # Live auto-complete
│   │   │   │   │   ├── StateFilter/            # Dropdown + "Limit to state" checkbox
│   │   │   │   │   └── ResultsTable/           # Viewport-scoped; no empty rows
│   │   │   │   ├── MapContentsPanel/   # Layer toggles (shown when no search active)
│   │   │   │   └── CensusHealthPanel/  # "US Census & Health Data" (not "Demographics")
│   │   │   │       ├── DemographicLayers/      # One layer at a time
│   │   │   │       └── InlineLegend/           # Values + units always visible (not mouse-over)
│   │   │   ├── FacilityDetail/         # Facility drawer/modal
│   │   │   │   └── CloseLink/          # Close link at bottom (UCD 2011 — off-screen X fix)
│   │   │   ├── SuperfundDetail/        # Superfund site drawer
│   │   │   ├── IconToolbar/            # Labeled icons only — no separate text menus (UCD 2011)
│   │   │   ├── Legend/                 # Unified TRI+Superfund legend; distinct icons per type
│   │   │   ├── Onboarding/             # Tutorial overlay for first-time users (UCD 2011)
│   │   │   └── Charts/                 # Recharts: bar chart (top chemicals) + 15-year trend
│   │   ├── hooks/
│   │   │   ├── useViewportFacilities.ts  # Re-fetch on map move (viewport-scoped results)
│   │   │   └── useChemicalAutocomplete.ts
│   │   ├── api/                        # Typed API client
│   │   │   ├── facilities.ts
│   │   │   ├── superfund.ts
│   │   │   ├── demographics.ts
│   │   │   └── export.ts
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

---

## Consequences

## Positive

- **Fastest time to working prototype** — FastAPI + pandas enables end-to-end data pipeline in ~200 lines of Python
- **Best-in-class geospatial tooling** — geopandas, shapely, GeoAlchemy2 are the standard tools for this domain
- **Single-language backend** — ingestion pipeline and API in Python; no language context-switching
- **Open-source community appeal** — Python has the largest data/geo contributor pool
- **PostGIS performance** — `ST_DWithin` with GIST index handles radius queries on 90K facilities in <50ms
- **MapLibre GL** — WebGL-rendered, handles 100K+ points with clustering; fully open-source; supports the color expression ramp needed for TRI release amount color-coding (confirmed in [screen catalog Fig 1](../product/TOXMAP_SCREEN_CATALOG.md))
- **Recharts** — natively supports the three-tab bar chart pattern documented in [screen catalog Fig 11](../product/TOXMAP_SCREEN_CATALOG.md): top-5 chemicals, release-by-medium stacked bar, 15-year trend
### Negative

- **Python runtime memory** — Python processes consume more RAM than JVM under certain workloads; mitigated with `uvicorn` worker pools
- **Less opinionated structure** — FastAPI doesn't enforce application architecture; team must maintain discipline (mitigated by service layer pattern above)
- **No built-in module boundary enforcement** — unlike Spring Modulith; acceptable for this domain scope

### Neutral

- Async SQLAlchemy has a steeper learning curve than synchronous SQLAlchemy 1.x; offset by excellent documentation
- Protomaps tile hosting requires an initial ~100 GB planet tile download for global coverage; US-only PMTiles extract is ~8 GB

---

## Implementation Notes

### Geospatial Radius Query Example (FastAPI)

```python
from geoalchemy2.functions import ST_DWithin, ST_GeomFromText, ST_Transform

async def get_facilities_near(
    lat: float, lon: float, radius_miles: float, session: AsyncSession
) -> list[Facility]:
    radius_meters = radius_miles * 1609.34
    point = ST_GeomFromText(f"POINT({lon} {lat})", 4326)
    result = await session.execute(
        select(Facility).where(
            ST_DWithin(
                ST_Transform(Facility.location, 3857),
                ST_Transform(point, 3857),
                radius_meters
            )
        )
    )
    return result.scalars().all()
```

### TRI Ingestion Example

```python
import geopandas as gpd
import pandas as pd
from sqlalchemy import text

from ingestion.tri_parser import (
    TRI_COLUMN_MAP,
    compute_aggregated_release_columns,
)

def ingest_tri_year(csv_path: str, year: int, engine) -> None:
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)

    # 1. Rename raw EPA column headers to canonical names.
    #    TRI_COLUMN_MAP includes both "ST"/"STATE" and "CAS #"/"CAS NUMBER" aliases
    #    to handle format variations across EPA release years.
    df = df.rename(columns=TRI_COLUMN_MAP)

    # 2. Compute aggregated medium columns from individual Section 5 fields.
    #    air_release_lbs = fugitive (Field 51) + stack (Field 52)
    #    land_release_lbs = sum of Fields 57–64 (varies by reporting year)
    #    underground_release_lbs = Class I (Field 55) + Class II-V (Field 56)
    df = compute_aggregated_release_columns(df)

    # 3. Numeric coercion — after aggregation, cast canonical columns.
    for col in ["latitude", "longitude", "total_release_lbs", "off_site_lbs",
                "air_release_lbs", "water_release_lbs", "land_release_lbs",
                "underground_release_lbs"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 4. Drop rows with missing coordinates.
    df = df.dropna(subset=["latitude", "longitude"])

    # 5. Geometry column.
    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df["longitude"], df["latitude"]), crs="EPSG:4326"
    )
    gdf["reporting_year"] = year

    # 6. Upsert into facilities / release_events tables.
    gdf.to_postgis("facilities_staging", engine, if_exists="replace")
    # ... upsert logic into facilities and release_events tables
```

---

## Alternatives Considered

- **[ADR-002](ADR-002-spring-modulith-postgis.md)** (Spring Modulith): Rejected as primary choice due to heavier boilerplate and weaker geospatial ingestion toolchain
- **[ADR-003](ADR-003-nextjs-serverless-postgis.md)** (Next.js + Supabase): Rejected as primary choice due to vendor dependency risk and weaker geospatial query control
- **[ADR-004](ADR-004-zero-budget-hosting.md)** (Zero-budget hosting): Companion ADR — defines that the **production deployment target** for this stack is Cloudflare Pages + DuckDB WASM (Option A), replacing FastAPI with in-browser queries. FastAPI is retained for local development and acceptance testing.
- **GeoDjango**: Considered; FastAPI preferred for async performance and lighter framework footprint
- **DuckDB + Spatial**: Considered for ingestion pipeline; promoted to primary production query engine in ADR-004 Option A

---

## Geocoding Specification (H-3)

> **⚠️ SUPERSEDED:** This section describes the original Nominatim-based geocoding plan. **ADR-006 (2026-07-27) replaced Nominatim with Photon (photon.komoot.io).** The current implementation uses browser-direct calls to Photon with a 1-second throttle and 200-entry LRU cache. See [ADR-006](ADR-006-photon-geocoding.md) for the authoritative geocoding specification.

Address-to-coordinate conversion is required for the location search field (e.g. "Sparrows Point, MD" → lat/lon).

**Dev/server mode (FastAPI running):** Use `GET /api/v1/geocode?q=` — a server-side Nominatim proxy defined in `TOXMAP_API_CONTRACT.md` §15. This keeps the Nominatim rate-limit logic and User-Agent header server-side.

**Production mode (DuckDB WASM / ADR-004 Option A, no backend):** The frontend calls Nominatim directly from the browser via the hook below.

```
Service:    Nominatim (OpenStreetMap)
Endpoint:   GET https://nominatim.openstreetmap.org/search
Params:     q={address}&format=json&limit=1&countrycodes=us
Rate limit: 1 request/second — MUST debounce input (500ms delay after last keystroke)
User-Agent: Must set User-Agent header identifying the application per OSM policy
Privacy:    User-typed addresses are sent to nominatim.openstreetmap.org
```

**React hook pattern:**
```typescript
// frontend/src/hooks/useGeocode.ts
const useGeocode = (address: string) => {
  // Debounce 500ms, then:
  const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=json&limit=1&countrycodes=us`;
  // Returns { lat: number, lon: number, display_name: string } | null
};
```

**Fallback for offline/test use:** A hardcoded lookup table covers all seed city names:
```typescript
const SEED_CITY_COORDS: Record<string, [number, number]> = {
  "Sparrows Point, MD":  [39.2197, -76.4785],
  "Ruth, NV":            [39.2919, -115.0319],
  "Front Royal, VA":     [38.9241, -78.1856],
  "Houston, TX":         [29.7604, -95.3698],
};
```

---

## URL Routing / Deep Link Scheme (H-7)

All map state is encoded in the URL hash so that:
- Browser back/forward buttons work correctly
- The current view is shareable via URL
- T-08 (ToxFAQ opens in new tab without losing map state) passes automatically

**Hash-param format:**
```
/#/map?lat=38.0&lon=-97.0&zoom=4
/#/map?lat=39.22&lon=-76.48&zoom=10&chemical=LEAD+COMPOUNDS&year=2008&medium=air
/#/map?lat=38.92&lon=-78.19&zoom=10&dataset=superfund&chemical=STYRENE
```

**Parameter reference:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `lat` | float | `38.0` | Map center latitude |
| `lon` | float | `-97.0` | Map center longitude |
| `zoom` | int | `4` | MapLibre GL zoom level (1–20) |
| `chemical` | string | — | URL-encoded chemical name |
| `year` | int | latest | TRI reporting year |
| `medium` | string | — | `air` \| `water` \| `land` \| `underground` |
| `state` | string | — | Two-letter state code |
| `restrict` | bool | `false` | `true` = restrict results to state |
| `dataset` | string | `tri` | `tri` \| `superfund` \| `both` |
| `demo` | string | — | Active demographic layer key |

**Rules:**
- All state changes use `history.replaceState` (not `pushState`) to avoid polluting browser history with every map pan
- Search submission uses `history.pushState` — creates a back-navigable entry
- React Router `useSearchParams` with `#` hash strategy (not pathname routing — compatible with Cloudflare Pages static hosting)

---

## Appendix A: Python Dependency Specification (H-4)

Canonical pinned versions for the backend. Use `pyproject.toml` (PEP 621 format):

```toml
# backend/pyproject.toml
[project]
name = "toxmap-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi==0.111.1",
    "uvicorn[standard]==0.30.1",
    "sqlalchemy[asyncio]==2.0.31",
    "geoalchemy2==0.15.2",
    "asyncpg==0.29.0",
    "alembic==1.13.2",
    "pydantic==2.8.2",
    "pydantic-settings==2.3.4",
    "httpx==0.27.0",             # async HTTP client (geocoding, health checks)
    "python-dotenv==1.0.1",
]

[project.optional-dependencies]
ingestion = [
    "geopandas==0.14.4",
    "pandas==2.2.2",
    "pyarrow==16.1.0",           # Parquet output for ADR-004 DuckDB WASM path
    "shapely==2.0.5",
]
test = [
    "pytest==8.2.2",
    "pytest-bdd==7.2.0",
    "pytest-asyncio==0.23.7",
    "pytest-benchmark==4.0.0",
    "psycopg2-binary==2.9.9",    # sync driver for test fixtures only
    "playwright==1.44.0",
    "pytest-playwright==0.5.0",
    "schemathesis==3.33.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
addopts = "-p no:xdist"          # tests must run single-threaded (shared DB session)
testpaths = ["tests"]

[tool.alembic]
script_location = "alembic"
```

**Environment variables (`backend/.env.example`):**
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/toxmap
DATABASE_URL_SYNC=postgresql+psycopg2://postgres:postgres@localhost:5432/toxmap
DATABASE_URL_TEST=postgresql+psycopg2://postgres:postgres@localhost:5432/toxmap_test
ALLOWED_ORIGINS=http://localhost:3000,https://toxmap.pages.dev
```

---

## Appendix B: Frontend Dependency Specification (H-5)

```json
{
  "name": "toxmap-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev":   "vite",
    "build": "tsc && vite build",
    "test":  "playwright test"
  },
  "dependencies": {
    "react":                "^18.3.1",
    "react-dom":            "^18.3.1",
    "maplibre-gl":          "^4.5.0",
    "react-map-gl":         "^7.1.7",
    "recharts":             "^2.12.7",
    "@duckdb/duckdb-wasm":  "^1.29.0",
    "tailwindcss":          "^3.4.6"
  },
  "devDependencies": {
    "@types/react":         "^18.3.3",
    "@types/react-dom":     "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript":           "^5.5.3",
    "vite":                 "^5.3.4",
    "autoprefixer":         "^10.4.19",
    "postcss":              "^8.4.39"
    // NOTE: E2E tests use pytest-playwright (Python). Do NOT add @playwright/test here.
  }
}
```

**Environment variables (`frontend/.env.example`):**
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_DATA_SOURCE=api                        # "api" | "duckdb"
VITE_R2_BASE_URL=https://pub-XXXXX.r2.dev  # Cloudflare R2 public URL
VITE_MAPLIBRE_STYLE=http://localhost:8080/styles/basic.json
# VITE_NOMINATIM_UA is obsolete — geocoding uses Photon per ADR-006
```

---

## Review Checklist

**Technical**
- [ ] Geospatial radius query benchmarked against PostGIS with ~90K TRI facilities (p95 < 500ms)
- [ ] Viewport-scoped facility query benchmarked (re-fetch on map move < 200ms)
- [ ] `restrict_to_state=true` parameter returns only in-state facilities
- [ ] Superfund `ST_DWithin` query validated against ~1,500 NPL sites
- [ ] Census TIGER polygon overlay renders without viewport stall
- [ ] TRI CSV ingestion tested against 2022 bulk file
- [ ] Medium filter (air/water/land/underground) returns correct subset
- [ ] 15-year trend chart renders correctly for facilities with sparse year coverage
- [ ] Chemical auto-complete returns results in < 100ms
- [ ] Docker Compose cold start → map load works end-to-end

**UX Acceptance Tests (UCD 2011 Task Scenarios)**
- [ ] T-01: Parent finds lead-compound TRI facility near Sparrows Point, MD; correct lb amount for year shown
- [ ] T-02: Superfund-reportable chemical list accessible within 2 clicks
- [ ] T-03: Copper releases > 8,000 lbs in eastern Nevada — Robinson Nevada Mining Co returned; medium = land
- [ ] T-04: Styrene Superfund site near Front Royal, VA — AVTEX FIBERS returned
- [ ] T-05: TRI styrene sites near Front Royal + under-18 demographic overlay visible without panel confusion
- [ ] T-06: Income demographic layer applied; units shown; layer removable from within panel
- [ ] T-07: Largest chlorine release in SC + largest nationwide both queryable
- [ ] T-08: CDC ToxFAQ link for ammonia opens without losing map state
- [ ] T-09: Benzene releases + cancer mortality overlay; co-occurrence disclaimer visible on mortality tab only

**UX Design Invariants**
- [ ] Dual-panel layout never occurs — only one sidebar context visible at a time
- [ ] Search results table contains zero empty placeholder rows
- [ ] State dropdown includes "Limit to state" checkbox that actually restricts results
- [ ] Panel labeled "Search Chemical Releases by Location" (not "Quick Search")
- [ ] Panel labeled "US Census & Health Data" (not "Demographics")
- [ ] Demographic legend values inline with units; not mouse-over-only
- [ ] TRI / Superfund / hospital icons are visually distinct (no icon ambiguity)
- [ ] Most-recent year labeled "(latest year)" in layer toggles
- [ ] All release quantities comma-formatted (8,205 not 8205)
- [ ] Facility popup close link present at bottom of popup

- [ ] All 57 Gherkin scenarios in [TOXMAP_ACCEPTANCE_TESTS.md](../testing/TOXMAP_ACCEPTANCE_TESTS.md) pass against seeded DB
- [ ] Schemathesis contract tests pass against `/openapi.json` with `--checks all`
- [ ] Performance SLAs from [TOXMAP_API_CONTRACT.md §Performance](../api/TOXMAP_API_CONTRACT.md) met under `pytest-benchmark`
- [ ] ADR reviewed by at least two contributors before status → Accepted








