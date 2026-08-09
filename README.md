# TOXMAP Redux

**An open-source revival of the EPA/NLM TOXMAP environmental health mapping tool — built for the public, free.**

[![CI](https://github.com/VictorCannestro/toxmap/actions/workflows/ci.yml/badge.svg)](https://github.com/VictorCannestro/toxmap/actions/workflows/ci.yml)
[![Security](https://github.com/VictorCannestro/toxmap/actions/workflows/security.yml/badge.svg)](https://github.com/VictorCannestro/toxmap/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Phase](https://img.shields.io/badge/Phase-6%20%E2%80%94%20Full%20QA%20Pass%20(ROLLBACK)-orange)](docs/product/TOXMAP_PROGRESS_TRACKER.md)
[![Data: EPA TRI](https://img.shields.io/badge/Data-EPA%20TRI%201987%E2%80%93present-green)](https://www.epa.gov/toxics-release-inventory-tri-program)
[![Cost: $0/month](https://img.shields.io/badge/hosting-%240%2Fmonth-brightgreen)](docs/adr/ADR-004-zero-budget-hosting.md)

---

> *"TOXMAP was decommissioned in December 2019. The data didn't go anywhere. The need didn't go anywhere. We're bringing the map back."*

---

## What Is TOXMAP?

The original **TOXMAP** was a free, public Geographic Information System built by the **National Library of Medicine (NLM/NIH)**. For fifteen years — from 2004 to 2019 — it let anyone in the United States look up what toxic chemicals were being released near their home, school, or workplace, who was releasing them, and how much. It linked directly to EPA Superfund sites, CDC health resources, and Census demographic overlays so that residents, researchers, journalists, and public health professionals could connect the dots.

Then it was decommissioned.

This project is an open-source recreation of that tool — built on modern, open-source infrastructure, deployed at zero cost, and available to anyone with a browser. No account. No paywall. No server required in production.

**The data is public. The map should be too.**

---

## Features

TOXMAP Redux is a comprehensive environmental health mapping tool with the following capabilities:

### What You Can Find

- **TRI Facilities** — Every EPA Toxic Release Inventory facility in the US (1987–present), color-coded by release amount: green (low) → yellow → orange → red (high)
- **Superfund Sites** — EPA National Priorities List hazardous waste sites with cleanup status and contaminants
- **Demographics** — Census data overlays: population, income, age, race, and mortality rates by county

### How You Can Search

- **By Facility Name** — Search for a specific company or site by name, TRI ID, or EPA ID
- **By Location** — Enter any address or city to find facilities
- **By Chemical** — Type a chemical name and get instant suggestions 
- **By State** — Browse all facilities in a state without entering a location
- **By Year** — Filter to a specific reporting year (1987–present) or view all years combined
- **By Dataset** — Search TRI facilities, Superfund sites, or both at once

### What You'll See

- **Facility Details** — Click any marker to see the full record: address, chemicals released, release amounts by medium
- **15-Year Trends** — Bar charts showing how a facility's releases have changed over time
- **Top Chemicals** — The 5 largest chemical releases at each facility with percentages
- **Superfund Contaminants** — List of hazardous substances found at each Superfund site
- **Health Information** — Direct links to CDC ToxFAQs and PubChem for many chemicals

### Data You Can Export

- **CSV Download** — Export your search results for spreadsheet analysis
- **Data Vintage** — Always shows which EPA data release you're viewing

### Important Notes

- **Free & No Account Required** — Runs entirely in your browser with no server costs
- **Correlation ≠ Causation** — When viewing health data alongside facilities, a disclaimer reminds you that proximity doesn't prove harm
- **Release Amount ≠ Health Risk** — High release quantities don't automatically mean danger; toxicity and exposure pathways vary by chemical

---

## Live Demo

> **⚠️ DEVELOPMENT HALTED — Phase 6 rollback in progress (2026-08-03).** New defects were discovered pre-Phase 7 deployment. Development is paused while QA triages and resolves outstanding issues. See [progress tracker](docs/product/TOXMAP_PROGRESS_TRACKER.md) for details.

When live: **[https://toxmap.pages.dev](https://toxmap.pages.dev)**

---

## Quick Start (Local Dev)

You need [Docker Desktop ≥ 4.35](https://www.docker.com/products/docker-desktop/) and [Git](https://git-scm.com/).

```bash
# 1. Clone
git clone https://github.com/VictorCannestro/toxmap.git
cd toxmap

# 2. Start the full stack (PostgreSQL + PostGIS, FastAPI, React)
docker compose up

# 3. Wait ~30 seconds for health checks, then verify:
curl http://localhost:8000/health   # → {"status": "ok"}
open http://localhost:3000          # → React app

# 4. Load the seed dataset (7 facilities, 3 counties, 2 Superfund sites)
#    Note: On first run, Docker init scripts load seed.sql automatically.
#    For subsequent runs or to reset seed data:
docker exec -i toxmap-postgres psql -U postgres -d toxmap < tests/fixtures/seed.sql

# 5. Run the test suite
docker compose exec backend pytest tests/ -v

# 6. Verify the two immutable seed values from the 2011 NLM usability study:
docker compose exec postgres psql -U postgres -d toxmap -c \
  "SELECT f.tri_facility_id, re.total_release_lbs
   FROM release_events re JOIN facilities f ON f.id = re.facility_id
   WHERE f.tri_facility_id = '89319BHPCP7MILE' AND re.reporting_year = 2008;"
# → 89319BHPCP7MILE | 8205.0  (Robinson Nevada Mining Co — copper to land)
```

No Docker? Frontend-only:
```bash
cd frontend && npm install
VITE_DATA_SOURCE=api VITE_API_URL=http://localhost:8000 npm run dev
```

Backend-only:
```bash
cd backend && pip install -e ".[dev]"
uvicorn app.main:app --reload
```

---

## Architecture

TOXMAP has two modes that share the same React UI:

```
Dev mode  (VITE_DATA_SOURCE=api)
  Browser ──HTTP──► FastAPI + PostGIS  ← for development & acceptance testing

Prod mode (VITE_DATA_SOURCE=duckdb)
  Browser ──SQL──► DuckDB WASM ──range requests──► Parquet files on Cloudflare R2
  No server. No cold start. $0/month.
```

| Layer | Technology | Why |
|-------|-----------|-----|
| API (dev) | Python 3.12 · FastAPI · SQLAlchemy 2.x async | Async, typed, fast; PostGIS spatial queries |
| Database (dev) | PostgreSQL 16 + PostGIS 3.4 | Industry-standard geospatial SQL |
| Query engine (prod) | DuckDB WASM + Parquet on Cloudflare R2 | Full SQL in the browser; no server required |
| Frontend | React 18 · TypeScript · Vite · MapLibre GL JS · Tailwind CSS | Open-source map stack (no Mapbox license) |
| Charts | Recharts | Composable, accessible React charts |
| Tests | pytest-bdd (Gherkin) · Playwright · Schemathesis | BDD acceptance tests + E2E + API fuzzing |
| CI/CD | GitHub Actions → Cloudflare Pages | Automated; free tier |
| Cost | **$0 / month** | Cloudflare Pages + R2 free tier |

Full design rationale: [ADR-001](docs/adr/ADR-001-fastapi-postgis-react.md) · [ADR-004](docs/adr/ADR-004-zero-budget-hosting.md)

---

## Data Sources

All data is public domain or open-access. No synthetic data is ever served to users.

| Dataset | Source | Coverage | Update Cadence |
|---------|--------|----------|---------------|
| **EPA Toxic Release Inventory (TRI)** | [EPA TRI Program](https://www.epa.gov/toxics-release-inventory-tri-program) | 1987–present · ~700K records/year | Annual (July; pipeline runs August, October, April) |
| **EPA Superfund / National Priorities List** | [EPA CERCLIS/SEMS](https://www.epa.gov/superfund/superfund-data-and-reports) | ~1,500 active NPL sites | Quarterly |
| **U.S. Census Demographics** | [Census TIGER/Line ACS 5-Year](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) | County + tract level | Decennial + ACS annual |
| **Basemap tiles** | [OpenFreeMap](https://openfreemap.org/) (hosted vector tiles) | Global | Continuous (OSM-derived) |

### Data Provenance Policy

This is a **public health tool**. Inaccurate data is not just a bug — it can mislead people making real decisions about where to live, work, or advocate.

- No synthetic data in production — all facility data comes from EPA primary sources
- Seed test data values are pinned to a [peer-reviewed NLM usability study (2011)](https://dpcpsi.nih.gov/sites/g/files/mnhszr346/files/FR508_10-4004_NLM_11-03-11.pdf) and must never be changed without a primary-source citation
- The co-occurrence disclaimer is mandatory on any view combining release data with health outcomes

Full policy: [GOVERNANCE.md §9 — Data Provenance](docs/GOVERNANCE.md)

---

## Roadmap

The project is built in **8 sequential phases** with objective Definition-of-Done checklists. Each phase gate requires passing CI, Playwright tests, and Schemathesis before advancing.

| Phase | Name | Status | Milestone | Story Points |
|-------|------|--------|-----------|-------------|
| **0** | Foundation — Repo, Docker, CI, security baseline | ✅ | M0 — Dev Environment Ready | 33 |
| **1** | Data Pipeline — TRI + Superfund + Census → PostGIS + Parquet | ✅ | M1 — Data Pipeline Working | 48 |
| **2** | Core API — 17 domain endpoints + `/api/v1/meta` | ✅ | M2 — Core API Green | 62 |
| **3** | Core Map UI — Map, search, TRI markers, T-01/T-03/T-08 E2E pass | ✅ | M3 — First Shareable Demo | 79 |
| **4** | Superfund Overlay — Diamond markers, T-02/T-04 E2E pass | ✅ | M4 — Superfund Layer | 28 |
| **5** | Demographics Layer — Census choropleth, T-05/T-06/T-09 E2E pass | ✅ | M5 — Demographics Layer | 33 |
| **6** | Full QA Pass — All Gherkin green, SLAs met, security regression | 🔄 In Progress | M6 — Feature Complete | 51 |
| **7** | Production Deploy — Cloudflare Pages + DuckDB WASM, $0 cost | ⬜ | **M7 — MVP Shipped 🚀** | 51 |

**Total: ~385 story points · ~13–19 weeks**

Live phase status: [`CURRENT_PHASE.txt`](CURRENT_PHASE.txt) · Full story table: [`TOXMAP_PROGRESS_TRACKER.md`](docs/product/TOXMAP_PROGRESS_TRACKER.md)

---

## Acceptance Tests

The MVP is defined by **9 task scenarios** sourced directly from NLM's 2011 User-Centered Design usability study. If these pass, the app is done. No earlier.

| Scenario | What It Tests |
|---------|--------------|
| **T-01** | Lead compounds near Sparrows Point, MD → facility `21219BTHLS3RD`, `12,485 lbs`, year 2008 |
| **T-02** | Superfund-reportable chemical list reachable within 2 clicks |
| **T-03** | Copper releases >8,000 lbs in eastern Nevada → `89319BHPCP7MILE`, `8,205 lbs`, land medium |
| **T-04** | Styrene Superfund site near Front Royal, VA → AVTEX FIBERS INC |
| **T-05** | TRI styrene + under-18 demographic overlay — both visible, single-sidebar invariant holds |
| **T-06** | Income layer applies; units from database (not hardcoded); "Clear layer" works |
| **T-07** | Largest chlorine release: SC → `85,000 lbs`; nationwide → `342,500 lbs` |
| **T-08** | CDC ToxFAQ link opens in new tab; map state preserved (no history entry lost) |
| **T-09** | Benzene + cancer mortality overlay; co-occurrence disclaimer visible; NOT on income tab |

Run all 9: `pytest tests/features/e2e/F7_ucd_task_scenarios.feature -v`

---

## Contributing

TOXMAP is actively welcoming contributors. Whether you're a GIS developer, a data scientist, a public health researcher who wants to verify the data, or someone who just learned Python last month — there is a place for you here.

**Best first steps:**

1. **Get the stack running locally** — `docker compose up` (see [Quick Start](#quick-start-local-dev))
2. **Pick a labeled issue:** look for `good-first-issue`, `test-needed`, or `Phase 0` labels
3. **Implement a test stub** — the fastest path to your first merged PR is picking a `@pytest.mark.skip` step in `tests/steps/api_steps.py` and filling it in
4. **Read the contributor guide** — [`CONTRIBUTING.md`](CONTRIBUTING.md) · 10 minutes; covers branching, commit format, PR process, and the seed data rules

**For AI-assisted contributions:** This project has a complete agentic development framework with 7 specialized agent prompts, a Phase Manager orchestrator, and a full governance model. See [`AGENTS.md`](AGENTS.md).

**Governance:** [`GOVERNANCE.md`](docs/GOVERNANCE.md) — decision authority, ADR process, conflict resolution, release process.

**Code of Conduct:** [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)

---

## Security

TOXMAP is a **public, read-only** data visualization tool with no user accounts and no payment processing. The attack surface is intentionally narrow. We take it seriously anyway.

- `gitleaks`, `pip-audit`, `npm audit`, and `bandit` run on every PR
- All third-party GitHub Actions pinned to full 40-character commit SHAs (supply chain protection)
- No secrets in code; no `VITE_`-prefixed env vars may contain credentials
- Production uses DuckDB WASM — there is no server to attack

**To report a vulnerability:** Open a [private security advisory](https://github.com/VictorCannestro/toxmap/security/advisories/new). Do not open a public GitHub issue. We acknowledge within 72 hours.

Full security policy: [`SECURITY.md`](SECURITY.md) · Threat model: [`docs/security/THREAT_MODEL.md`](docs/security/THREAT_MODEL.md)

---

## Development Documentation

| Document | What's In It |
|---------|-------------|
| [`docs/adr/ADR-001-fastapi-postgis-react.md`](docs/adr/ADR-001-fastapi-postgis-react.md) | Full stack spec: SQL DDL for all 7 tables, API design, spatial query patterns, UX decisions |
| [`docs/adr/ADR-004-zero-budget-hosting.md`](docs/adr/ADR-004-zero-budget-hosting.md) | How the $0 production architecture works; DuckDB WASM + Parquet + Cloudflare |
| [`docs/api/TOXMAP_API_CONTRACT.md`](docs/api/TOXMAP_API_CONTRACT.md) | Every endpoint: URL, parameters, response shape, example JSON, SLAs |
| [`docs/testing/TOXMAP_ACCEPTANCE_TESTS.md`](docs/testing/TOXMAP_ACCEPTANCE_TESTS.md) | All Gherkin scenarios (the authoritative product contract) |
| [`docs/testing/TOXMAP_TEST_SEED_DATA.md`](docs/testing/TOXMAP_TEST_SEED_DATA.md) | The exact seed dataset and known-good assertion values |
| [`docs/product/TOXMAP_SCREEN_CATALOG.md`](docs/product/TOXMAP_SCREEN_CATALOG.md) | Annotated screenshots of the original 2006 and 2015 NLM TOXMAP UI |
| [`docs/onboarding/TECH_STACK_ONBOARDING.md`](docs/onboarding/TECH_STACK_ONBOARDING.md) | Getting oriented: env vars, Docker services, port map, troubleshooting |
| [`docs/onboarding/TWO_MODES_DEEP_DIVE.md`](docs/onboarding/TWO_MODES_DEEP_DIVE.md) | How `VITE_DATA_SOURCE` switches between FastAPI mode and DuckDB WASM mode |

---

## Acknowledgments

TOXMAP would not exist without the work of others:

- **National Library of Medicine / NIH** — for building and maintaining the original TOXMAP for 15 years, and for publishing peer-reviewed documentation of its design ([PMC2703818](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2703818/), [PMC4251466](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4251466/))
- **U.S. Environmental Protection Agency** — for the Toxic Release Inventory program (est. 1987) and for making all TRI data publicly downloadable
- **UCD Inc.** — for the 2011 usability study that produced the 9 task scenarios that define this project's acceptance criteria
- **The PostGIS, MapLibre GL JS, DuckDB, FastAPI, and React communities** — for building the open-source infrastructure that makes a zero-budget rebuild possible
- **Protomaps** — for free, open PMTiles basemap extracts that replace the original ESRI basemap

---

## License

Software: [MIT License](LICENSE) — Copyright © 2026 Victor Cannestro

Data displayed by this application is public domain (EPA TRI, EPA Superfund/NPL, U.S. Census TIGER/Line). The software license does not grant rights to the underlying data beyond the terms of its respective public-domain policies. See [LICENSE](LICENSE) for full data provenance details.

---

<p align="center">
  <sub>
    EPA data is updated annually. Superfund status changes. Census data is revised.
    <br>
    If you find a data error, <a href="https://github.com/VictorCannestro/toxmap/issues/new?labels=data-quality">open an issue</a> — accuracy is a public health matter.
  </sub>
</p>

