# ToxMap Clone — Tech Stack Analysis

**Date:** 2026-07-15  
**Author:** Architecture Review  
**Status:** Draft  
**Related ADRs:** [ADR-001](ADR-001-fastapi-postgis-react.md) · [ADR-002](ADR-002-spring-modulith-postgis.md) · [ADR-003](ADR-003-nextjs-serverless-postgis.md) · [ADR-004](ADR-004-zero-budget-hosting.md)  
**Primary Sources:**
- [NLM TOXMAP: A GIS-Based Gateway (PMC2703818)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2703818/)
- [Ten Years of Change: TOXMAP Gets a New Look (PMC4251466)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4251466/)
- [TOXMAP Usability Evaluation, User-Centered Design Inc., August 2011](https://dpcpsi.nih.gov/sites/g/files/mnhszr346/files/FR508_10-4004_NLM_11-03-11.pdf)
- [TOXMAP Screen Catalog — 18 annotated screenshots](../product/TOXMAP_SCREEN_CATALOG.md)

---

## 1. Executive Summary

This document evaluates technology stack options for an open-source clone of the EPA's ToxMap application (decommissioned 2019). ToxMap visualized Toxic Release Inventory (TRI) data on an interactive map, allowing the public to explore chemical releases by facility, chemical, year, geography, and industry sector.

Three architecture contenders were evaluated:

| ADR | Stack | Verdict |
|-----|-------|---------|
| ADR-001 | Python · FastAPI · PostGIS · React/MapLibre | ✅ **Recommended** |
| ADR-002 | Java · Spring Modulith · PostGIS · React/MapLibre | ⚠️ Viable (Java-heavy teams) |
| ADR-003 | Next.js · Node API · Supabase/PostGIS · MapLibre | ⚠️ Viable (JS-only teams) |

---

## 2. Problem Domain

### 2.1 What ToxMap Was (NLM Source Record)

TOXMAP was a web-based **Geographic Information System (GIS) developed by the National Library of Medicine (NLM/NIH)**, first released in 2004 and decommissioned in 2019. It served as an interactive mapping gateway to environmental health data, visualizing toxic chemical releases and linking to comprehensive NLM/EPA/CDC information resources.

**Original architecture evolution (authoritative):**

| Era | GIS Engine | Database | Client | Notes |
|-----|-----------|----------|--------|-------|
| 2004–2012 | ESRI ArcIMS | MySQL | Java / Apache Struts | Initial release; USGS National Atlas basemaps |
| 2013–2019 | ESRI ArcGIS for Server | PostgreSQL | Adobe Flash/Flex (ActionScript) | Complete redesign; RIA model |

Our clone **replaces the proprietary ESRI stack with open-source equivalents** (PostGIS + MapLibre GL) and the decommissioned Flash/Flex client with React. The 2013 NLM migration from MySQL → PostgreSQL validates our PostgreSQL + PostGIS choice.

### 2.2 Data Sources

| Source | Format | Size (approx.) | Update Frequency | Notes |
|--------|--------|-----------------|------------------|-------|
| EPA TRI Basic Data Files | CSV (per year) | ~300 MB/year | Annual (July) | Core dataset; 1987–present; ~700K records/year |
| EPA Superfund / NPL | GeoJSON / CSV | ~1,500 sites | Quarterly | National Priorities List (CERCLA hazardous waste sites) |
| EPA CERCLIS | CSV / REST | ~50K sites | Quarterly | Broader site assessment inventory |
| U.S. Census (TIGER) | Shapefile / GeoJSON | ~500 MB | Decennial | Demographic/economic overlays by county & census tract |
| Canadian NPRI | CSV | ~7K facilities | Annual | National Pollutant Release Inventory (optional layer) |
| Nuclear Power Plant Locations | GeoJSON | ~100 sites | Annual | U.S. commercial nuclear facilities |
| U.S. Congressional Districts | Shapefile | ~60 MB | Post-redistricting | Boundary overlay layer |
| EPA EJScreen (optional) | GeoJSON / REST | Varies | Annual | Environmental justice screening scores |

### 2.3 Core User Stories

> Stories 1–8 are sourced from the NLM PMC articles. Stories 9–14 are sourced directly from the 2011 usability study task scenarios (UCD Inc.), representing the actual tasks real users were asked to perform.

1. **Map Explorer:** As a user, I can view a map of all TRI facilities in a region, with color-coded markers indicating total release volume.
2. **Proximity Search:** As a user, I can enter my ZIP/address and see TRI facilities and Superfund sites within N miles.
3. **Chemical Filter:** As a user, I can filter the map by a specific chemical (with auto-completion of chemical names).
4. **Release Medium Filter:** As a user, I can filter releases by medium — air, water, land, or underground injection.
5. **Facility Detail:** As a user, I can click a facility and see its release history with a bar chart of top chemicals and a 15-year trend line.
6. **Superfund Overlay:** As a user, I can toggle an overlay of EPA Superfund/NPL sites with their Hazard Ranking System (HRS) score and cleanup status.
7. **Demographic Overlay:** As a user, I can overlay U.S. Census demographic data (population, income, age, race, mortality) by county or census tract.
8. **Download/Export:** As a user, I can export filtered TRI results and the current map view to CSV or image.
9. **Release Quantity Lookup:** As a parent concerned about nearby pollution, I can find a specific TRI facility near my home and see exactly how many pounds of a chemical (e.g., lead compounds) were released in a given year. *(UCD 2011, Task 1)*
10. **Superfund Chemical List:** As a user, I can find the list of Superfund-reportable chemicals within the application. *(UCD 2011, Task 2)*
11. **State Comparison:** As a researcher, I can find the largest release of a specific chemical in a given state and compare it to the largest release of that chemical nationwide. *(UCD 2011, Task 5)*
12. **External Health Links:** As a user, I can navigate from any chemical on the map directly to CDC ToxFAQs, NLM HSDB, and ATSDR resources for that chemical. *(UCD 2011, Task 6)*
13. **Cancer/Mortality Correlation Study:** As a public health professional, I can overlay demographic health data (e.g., cancer mortality) on a map of benzene-releasing TRI facilities to examine spatial co-occurrence — with clear disclaimers that correlation ≠ causation. *(UCD 2011, Task 7)*
14. **State-Restricted Search:** As a user, when I select a state in the search, I can optionally restrict results to only that state (not just zoom the map to that state). *(UCD 2011, critical finding)*

---

## 3. Functional Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| F-01 | Ingest and parse EPA TRI CSV bulk files (1987–present) | Must | NLM original |
| F-02 | Store facility location as geographic point (WGS84) | Must | NLM original |
| F-03 | Geospatial radius search (ST_DWithin) | Must | NLM original |
| F-04 | Filter by chemical (with live auto-complete), year, state, NAICS code | Must | NLM + UCD 2011 |
| F-05 | Filter releases by medium: air, water, land, underground injection | Must | NLM original |
| F-06 | Color-coded pin/cluster overlay (release volume determines marker color) | Must | NLM 2013 |
| F-07 | Facility detail: bar chart (top chemicals) + 15-year trend line | Must | NLM 2006 |
| F-08 | **Single unified sidebar** — Search Results and Map Contents never shown simultaneously | Must | UCD 2011 §"Two Panels" |
| F-09 | Search results table shows **only map-viewport facilities** (no empty placeholder rows) | Must | UCD 2011 §"Table of Results" |
| F-10 | State filter optionally **restricts** results to state (not only zooms map) | Must | UCD 2011 §"Search Parameters" |
| F-11 | Superfund / NPL overlay with HRS score, cleanup status, contaminant list | Should | NLM 2006 |
| F-12 | **Combined TRI + Superfund legend** when both layers are active; no icon ambiguity with hospital/other markers | Should | UCD 2011 §"TRI and Superfund Tabs" + §"Hospital Icons" |
| F-13 | Census demographic overlays (income, age, population, race, mortality by county/tract) | Should | NLM 2006–2013 |
| F-14 | Demographic legend: **inline values** (not mouse-over only); units shown (%, $, years, people) | Should | UCD 2011 §"Mouse-Over Legend" |
| F-15 | Demographic overlay: one layer at a time; **co-occurrence disclaimer on mortality tab only** | Should | UCD 2011 §"Instructions for Demographics" |
| F-16 | Facility popup: accessible **close link at bottom** in addition to corner X | Should | UCD 2011 §"Closing Facility Pop-Ups" |
| F-17 | All release quantities with **comma-formatted numbers** (8,205 lbs, not 8205) | Should | UCD 2011 §"Commas in Numbers" |
| F-18 | Most-recent data year labeled **"(latest year)"** in all layer toggles | Should | UCD 2011 §"Why 2008 Data?" |
| F-19 | **Export**: CSV + map image download (not just browser print) | Should | UCD 2011 user requests |
| F-20 | Direct links to NLM HSDB, ATSDR ToxFAQs, PubMed for selected chemical | Should | NLM original |
| F-21 | Labeled icon toolbar (single navigation mechanism; no separate redundant text menus) | Could | UCD 2011 §"Menus vs. Icons" |
| F-22 | In-app **tutorial / onboarding** for first-time users | Could | UCD 2011 §"Learning Curve" |
| F-23 | Search for **multiple chemicals** simultaneously on a single map | Could | UCD 2011 user requests |
| F-24 | EPA monitoring site overlay | Could | UCD 2011 user requests |
| F-25 | Canadian NPRI facility layer | Could | NLM 2013 redesign |
| F-26 | Nuclear power plant location overlay | Could | NLM 2013 redesign |
| F-27 | Congressional district boundary overlay | Could | NLM 2013 redesign |

---

## 4. Non-Functional Requirements

| ID | Requirement | Target | Source |
|----|-------------|--------|--------|
| NF-01 | Map viewport query response time | < 500ms (p95) | NLM 2013: "real-time search result updating with zoom" |
| NF-02 | Facility detail response time | < 200ms (p95) | — |
| NF-03 | Data ingestion (full TRI history, ~4M rows) | < 2 hours | — |
| NF-04 | Public read-only — no authentication required | — | NLM: government, business, academia, and citizens |
| NF-05 | Open-source license (MIT / Apache 2.0) | — | Replaces ESRI proprietary stack |
| NF-06 | Containerized deployment (Docker Compose) | Must | — |
| NF-07 | Horizontal scalability of API layer | Should | — |
| NF-08 | Correlation ≠ causation disclaimers on mortality/health overlays | Must | NLM + UCD 2011 §"Instructions for Demographics" |
| NF-09 | Pop-up blocker warning before app launches | Should | UCD 2011 §"Pop-Up Blocker" (session loss risk) |
| NF-10 | Steep learning curve mitigated via in-app tutorial + help | Should | UCD 2011: majority of participants requested tutorial; non-GIS users had steep curve |

---

## 5. Technology Evaluation

### 5.1 Backend Framework

| Framework | Language | Geospatial Ecosystem | Dev Speed | Maturity | OSS Fit |
|-----------|----------|---------------------|-----------|----------|---------|
| **FastAPI** | Python 3.12 | ★★★★★ (geopandas, shapely, GeoAlchemy2) | ★★★★★ | ★★★★☆ | ★★★★★ |
| Spring Modulith | Java 21 | ★★★★☆ (Hibernate Spatial, JTS) | ★★★☆☆ | ★★★★★ | ★★★☆☆ |
| Express / Fastify | Node.js | ★★★☆☆ (node-postgres, turf.js) | ★★★★☆ | ★★★★☆ | ★★★★☆ |
| Next.js API Routes | Node.js | ★★★☆☆ | ★★★★★ | ★★★★☆ | ★★★★★ |
| Django + GeoDjango | Python 3.12 | ★★★★★ | ★★★★☆ | ★★★★★ | ★★★★☆ |

**Winner: FastAPI** — lightest overhead, async-native, excellent geospatial library support, and the data ingestion pipeline (pandas/geopandas) lives in the same language.

### 5.2 Database

| Database | Geospatial | Full-Text Search | JSON Support | Scalability |
|----------|-----------|-----------------|--------------|-------------|
| **PostgreSQL + PostGIS** | ★★★★★ | ★★★★☆ | ★★★★☆ | ★★★★☆ |
| MySQL + Spatial | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ |
| MongoDB + GeoJSON | ★★★★☆ | ★★★★☆ | ★★★★★ | ★★★★☆ |
| SQLite + SpatiaLite | ★★★☆☆ | ★★☆☆☆ | ★★★☆☆ | ★★☆☆☆ |
| DuckDB + Spatial | ★★★☆☆ | ★★☆☆☆ | ★★★★☆ | ★★★☆☆ |

**Winner: PostgreSQL + PostGIS** — industry standard for geospatial queries; `ST_DWithin`, `ST_Contains`, `ST_ClusterDBSCAN` are critical for this use case. Supported by all three contenders.

### 5.3 Frontend / Map Rendering

| Library | Tile Support | Clustering | Open-Source | Bundle Size |
|---------|-------------|------------|-------------|-------------|
| **MapLibre GL JS** | ★★★★★ | ★★★★★ | ★★★★★ (MIT) | ★★★★☆ |
| Leaflet.js | ★★★★☆ | ★★★★☆ | ★★★★★ (BSD) | ★★★★★ |
| Mapbox GL JS v3 | ★★★★★ | ★★★★★ | ★★☆☆☆ (proprietary) | ★★★☆☆ |
| OpenLayers | ★★★★★ | ★★★★☆ | ★★★★★ (BSD) | ★★★☆☆ |
| Deck.gl | ★★★☆☆ | ★★★★★ | ★★★★★ (MIT) | ★★★☆☆ |

**Winner: MapLibre GL JS** — fully open-source Mapbox GL fork, WebGL-accelerated, handles 100K+ data points, excellent clustering support. Pairs with React via `react-map-gl`.

**Tile Source:** OpenStreetMap / Protomaps (self-hostable, zero licensing cost).

### 5.4 Data Ingestion Pipeline

| Approach | TRI CSV Parsing | Geocoding | Scheduling | OSS Fit |
|----------|----------------|-----------|------------|---------|
| **pandas + geopandas** | ★★★★★ | ★★★★★ | ★★★★☆ | ★★★★★ |
| Apache Spark | ★★★★★ | ★★★☆☆ | ★★★★★ | ★★★★☆ |
| dbt + SQL transforms | ★★★☆☆ | ★★★☆☆ | ★★★★★ | ★★★★☆ |
| Spring Batch | ★★★★☆ | ★★★★☆ | ★★★★★ | ★★★☆☆ |

**Winner: pandas/geopandas** — TRI bulk files are well-structured CSVs. geopandas handles coordinate reprojection and PostGIS writes natively.

### 5.5 Infrastructure / Deployment

| Option | Complexity | Cost | Self-Hostable | Dev Experience |
|--------|-----------|------|---------------|----------------|
| **Docker Compose (local/VPS)** | Low | Low | ✅ | ★★★★★ |
| Kubernetes | High | Medium | ✅ | ★★★☆☆ |
| Vercel + Supabase | Low | Free tier | ❌ (vendor) | ★★★★★ |
| Fly.io + Supabase | Low | Low | Partial | ★★★★☆ |
| AWS ECS + RDS | Medium | Medium | ❌ (vendor) | ★★★☆☆ |

**Winner: Docker Compose** for development and self-hosting; **Fly.io** for easy cloud deployment without vendor lock-in.

---

## 6. Evaluation Matrix

Scored 1–5 per criterion, weighted by importance to ToxMap use case.

| Criterion | Weight | FastAPI Stack | Spring Modulith | Next.js Full-Stack |
|-----------|--------|--------------|-----------------|-------------------|
| Geospatial tooling quality | 25% | 5 (1.25) | 4 (1.00) | 3 (0.75) |
| Data ingestion / ETL ease | 20% | 5 (1.00) | 3 (0.60) | 3 (0.60) |
| API development speed | 15% | 5 (0.75) | 3 (0.45) | 4 (0.60) |
| Open-source community fit | 15% | 5 (0.75) | 3 (0.45) | 5 (0.75) |
| Production scalability | 10% | 4 (0.40) | 5 (0.50) | 3 (0.30) |
| Modularity / maintainability | 10% | 3 (0.30) | 5 (0.50) | 3 (0.30) |
| Deployment simplicity | 5% | 4 (0.20) | 3 (0.15) | 5 (0.25) |
| **TOTAL** | | **4.65** | **3.65** | **3.55** |

---

## 7. Recommendation

**ADR-001 (FastAPI + PostGIS + React/MapLibre)** is the recommended architecture.

Python's geospatial ecosystem is the decisive factor. The data pipeline (TRI CSV → PostGIS) and API layer share a language, minimizing context-switching and toolchain complexity. FastAPI's async support ensures competitive query performance without the ceremony of a Java stack.

Spring Modulith (ADR-002) is the correct choice only if:
- The team is exclusively Java and unwilling to adopt Python, OR
- The system is expected to evolve into a larger multi-domain platform requiring hard module boundaries.

Next.js full-stack (ADR-003) is the correct choice only if:
- The team is exclusively JavaScript/TypeScript, AND
- The geospatial query load is modest enough to delegate to Supabase managed services.

---

## 8. UX Lessons Learned (UCD Inc. Usability Study, 2011)

> Source: *TOXMAP Usability Evaluation*, User-Centered Design, Inc., August 2011. 15 participants: 4 concerned citizens + 11 professionals (toxicologists, researchers, public health). Combined in-lab (Rockville, MD) and remote sessions.

These findings directly shape frontend architecture decisions in [ADR-001](ADR-001-fastapi-postgis-react.md).

### 8.1 Critical Findings (Must Fix)

| Finding | Root Cause | Design Decision for Clone |
|---------|-----------|--------------------------|
| **Dual panel confusion** — users didn't understand Map Contents (left) and Search Results (right) were mutually exclusive | Two panels shown simultaneously | **Single collapsible sidebar panel** — one context at a time (F-08) |
| **Empty table rows** — search results table showed 500 rows/page with most empty (out-of-viewport facilities) | Table was country-wide, paged, not viewport-scoped | **Viewport-scoped results only**, re-fetched on map move (F-09) |
| **State filter zooms, doesn't filter** — selecting "Nevada" showed surrounding states too | State field was a zoom-to control, not a filter | **Add "Limit to state" checkbox** alongside state dropdown (F-10) |
| **"Quick Search" label missed** — users went to "Chemical Information" instead | Label didn't imply chemical+location search | Label as **"Search Chemical Releases by Location"** |
| **"Demographics" label missed** — users didn't expect mortality data there | Label didn't imply health/mortality data | Label as **"US Census & Health Data"** |

### 8.2 High-Impact Improvements

| Finding | Design Decision for Clone |
|---------|--------------------------|
| Welcome screen skipped entirely | Keep welcome flow minimal; prefer **persistent onboarding tooltip overlay** or short video link |
| Redundant menus + icon toolbar | **Labeled icon toolbar only** — no separate text menus (F-21) |
| TRI + Superfund tabs not noticed | **Unified legend** when both layers active; visually prominent tab indicators (F-12) |
| Mouse-over-only demographic legend | **Inline legend values** at all times; units always visible (%, $, years, people) (F-14) |
| Co-occurrence disclaimer shown on all demographic tabs | **Disclaimer shown on mortality tab only** (F-15) |
| Can't remove demographic layer from within the panel | Add **"Clear layer" button inside demographic panel** |
| Facility popup close button off-screen | **Close link at bottom of popup** always in viewport (F-16) |
| Numbers hard to read without commas | **Comma-format all numeric values** throughout (8,205 lbs) (F-17) |
| Latest year not obvious | Label most-recent year as **"2024 (latest year)"** in toggles (F-18) |
| Hospital icons ≈ Superfund site icons | **Distinct icon shapes + colors** per site type: TRI circle, Superfund diamond, hospital H-cross in different color (F-12) |

### 8.3 Feature Requests from Usability Participants

These emerged organically from the 2011 test sessions and inform our "Could" requirements:

- Search for **multiple chemicals simultaneously** on one map (F-23)
- Include **EPA monitoring sites** as an overlay (F-24)
- **Export** (not just print) — CSV of results + map image (F-19)
- Street names visible on aerial/satellite view
- Persistent search box visible at all times

### 8.4 Key Task Scenarios (Test Coverage Requirements)

The following task scenarios from the UCD study serve as acceptance test cases for the clone:

| Task | Scenario | Key Assertion |
|------|----------|--------------|
| T-01 | Parent searching for lead releases near Sparrows Point, MD | Correct facility found; correct lb amount for year |
| T-02 | Finding list of Superfund-reportable chemicals | Accessible within 2 clicks |
| T-03 | Copper releases > 8,000 lbs in eastern Nevada | Robinson Nevada Mining Co returned with correct medium (land) |
| T-04 | Styrene Superfund site near Front Royal, VA | AVTEX FIBERS, INC. returned |
| T-05 | TRI sites releasing styrene near Front Royal + under-18 population overlay | Both data layers visible simultaneously without confusion |
| T-06 | Income range overlay for an area | Demographic layer applies; units shown; layer removable |
| T-07 | Largest chlorine release in South Carolina vs. nationwide | State-filter returns SC result; nationwide comparison accessible |
| T-08 | CDC ToxFAQ for ammonia via TOXMAP | External link opens without losing map state |
| T-09 | Benzene releases + cancer mortality co-occurrence | Both visible; co-occurrence disclaimer present on mortality tab |

---

## 9. References

### NLM Primary Sources
- Roth SL. "TOXMAP: A GIS-Based Gateway to Environmental Health Resources." *J Med Libr Assoc.* 2006 Apr;94(2):156–158. [PMC2703818](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2703818/)
- Roth SL, Kalis MA. "Ten Years of Change: National Library of Medicine TOXMAP Gets a New Look." *J Med Libr Assoc.* 2015 Apr;103(2):100–102. [PMC4251466](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4251466/)

### Usability Research
- User-Centered Design, Inc. *TOXMAP Usability Evaluation — Final Report.* August 2011. Submitted to NLM/SIS. [https://dpcpsi.nih.gov/sites/g/files/mnhszr346/files/FR508_10-4004_NLM_11-03-11.pdf](https://dpcpsi.nih.gov/sites/g/files/mnhszr346/files/FR508_10-4004_NLM_11-03-11.pdf)

### ATDD Artifacts
- [TOXMAP_ACCEPTANCE_TESTS.md](../testing/TOXMAP_ACCEPTANCE_TESTS.md) — 57 Gherkin scenarios across 8 feature files (API + E2E); count grows as phases complete
- [TOXMAP_TEST_SEED_DATA.md](../testing/TOXMAP_TEST_SEED_DATA.md) — Deterministic SQL seed: 7 facilities, 6 chemicals, 14 release events, 2 Superfund sites, 3 counties
- [TOXMAP_API_CONTRACT.md](../api/TOXMAP_API_CONTRACT.md) — 17 endpoint contracts with example JSON, Pydantic schemas, and SLAs
- [TOXMAP_DEVELOPMENT_ROADMAP.md](../product/TOXMAP_DEVELOPMENT_ROADMAP.md) — 8-phase delivery roadmap: 322 story points, 7 milestones, risk register, handoff checklist

### Data Sources
- [EPA TRI Data & Tools](https://www.epa.gov/toxics-release-inventory-tri-program/tri-data-and-tools)
- [EPA Superfund National Priorities List](https://www.epa.gov/superfund/superfund-national-priorities-list-npl)
- [EPA CERCLIS / SEMS](https://www.epa.gov/superfund/superfund-data-and-reports)
- [US Census TIGER/Line Shapefiles](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html)
- [Environment and Climate Change Canada — NPRI](https://www.canada.ca/en/environment-climate-change/services/national-pollutant-release-inventory.html)

### Screen Reference
- [TOXMAP_SCREEN_CATALOG.md](../product/TOXMAP_SCREEN_CATALOG.md) — All 18 NLM-published screenshots (12 from 2006 article + 6 from 2015 article) with design annotations and clone implications
- [PostGIS Documentation](https://postgis.net/docs/)
- [GeoAlchemy2](https://geoalchemy-2.readthedocs.io/)
- [MapLibre GL JS](https://maplibre.org/) — open-source replacement for ESRI/Mapbox
- [Protomaps](https://protomaps.com/) — self-hostable tile server
- [FastAPI](https://fastapi.tiangolo.com/)
### Technology
- [PostGIS Documentation](https://postgis.net/docs/)
- [GeoAlchemy2](https://geoalchemy-2.readthedocs.io/)
- [MapLibre GL JS](https://maplibre.org/) — open-source replacement for ESRI/Mapbox
- [Protomaps](https://protomaps.com/) — self-hostable tile server
- [FastAPI](https://fastapi.tiangolo.com/)
- [ADR-001](ADR-001-fastapi-postgis-react.md) · [ADR-002](ADR-002-spring-modulith-postgis.md) · [ADR-003](ADR-003-nextjs-serverless-postgis.md)






