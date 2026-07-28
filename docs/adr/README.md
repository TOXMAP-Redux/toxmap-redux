# ADR Status Index

**Last updated:** 2026-07-27  
**Purpose:** Single source of truth for the current status of every Architecture Decision Record. Agents and contributors MUST consult this file before treating any ADR as authoritative.

---

## Status Definitions

| Status         | Meaning                                                                                                        |
|----------------|----------------------------------------------------------------------------------------------------------------|
| **Accepted**   | Decision is in effect. All implementation must follow this ADR.                                                |
| **Rejected**   | Decision was formally rejected. The file is retained for historical reference only. Do NOT implement this ADR. |
| **Proposed**   | Under active discussion. Not yet binding.                                                                      |
| **Deprecated** | Was accepted but superseded. Retained for migration reference.                                                 |

---

## Current ADR States

| ID                                              | Title                                                | Status         | Supersedes | Superseded By | Date       |
|-------------------------------------------------|------------------------------------------------------|----------------|------------|---------------|------------|
| [ADR-001](ADR-001-fastapi-postgis-react.md)     | Python · FastAPI · PostGIS · React/MapLibre          | **✅ Accepted** | —          | —             | 2026-07-15 |
| [ADR-002](ADR-002-spring-modulith-postgis.md)   | Java · Spring Modulith · PostGIS · React/MapLibre    | **❌ Rejected** | —          | ADR-001       | 2026-07-16 |
| [ADR-003](ADR-003-nextjs-serverless-postgis.md) | Next.js · Node API · Supabase/PostGIS · MapLibre     | **❌ Rejected** | —          | ADR-001       | 2026-07-16 |
| [ADR-004](ADR-004-zero-budget-hosting.md)       | Zero-Budget Hosting (Cloudflare Pages + DuckDB WASM) | **✅ Accepted** | —          | —             | 2026-07-16 |
| [ADR-005](ADR-005-openfreemap-basemap-tiles.md) | OpenFreeMap Hosted Tiles for MapLibre Basemap        | **✅ Accepted** | —          | —             | 2026-07-27 |
| [ADR-006](ADR-006-photon-geocoding.md)          | Photon (Komoot) for Browser-Direct Geocoding         | **✅ Accepted** | —          | —             | 2026-07-27 |

---

## Agent Disambiguation Rules

When two ADR files contain conflicting specifications, resolve as follows:

1. **ADR-001 always wins** for backend architecture, database schema, and API shape — it is the single Accepted backend ADR.
2. **ADR-004 wins** for deployment and hosting decisions — it constrains ADR-001's production target.
3. **ADR-002 and ADR-003 are historical reference only** — do NOT generate code from them.
4. If an ADR says "Proposed" anywhere in its file but this index says "Rejected" — **this index takes precedence**.

---

## Adding a New ADR

1. Create the file as `ADR-{NNN}-{short-title}.md` in the project root.
2. Add a row to the table above with status "Proposed".
3. Link from the relevant "Alternatives Considered" section of existing ADRs.
4. Change status to "Accepted" or "Rejected" only after team review.

