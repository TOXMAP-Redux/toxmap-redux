# TOXMAP Context Summary

> **For agents:** Load this file when context is constrained. It distills the most critical
> invariants, guardrails, protected files, and per-role doc links from the full corpus.
>
> **Usage rules:**
> - **Constrained context** (e.g., small context window): load this file *instead of* files 1–8 in `AGENTS.md §1`
> - **Full session**: load this file *alongside* files 1–8 — it supplements the full context load, not replaces it
> - **Always load:** `CURRENT_PHASE.txt` and `TOXMAP_PROGRESS_TRACKER.md` regardless of context size — they are Priority 0

**Last Updated:** 2026-08-03 (**ROLLBACK** — Phase 7 reverted to Phase 6)

---

## ⚠️ DEVELOPMENT HALTED (2026-08-03)

**Phase 7 has been rolled back to Phase 6.** New defects discovered pre-deployment. Development is paused until QA completes triage and resolution.

See: [ROLLBACK_PHASE7_TO_PHASE6_20260803.md](docs/escalations/ROLLBACK_PHASE7_TO_PHASE6_20260803.md)

---

## Current Phase

```
cat CURRENT_PHASE.txt   → 6  (Full QA Pass — ROLLBACK)
```

Active milestone: **M6 — Feature Complete** (REOPENED 2026-08-03 after rollback from Phase 7)

Full status: `docs/product/TOXMAP_PROGRESS_TRACKER.md`

---

## Stack (ADR-001, Accepted)

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy 2.x async + PostGIS 3.4
- **Frontend:** React 18 + TypeScript + Vite + MapLibre GL JS + Tailwind CSS
- **Geocoding:** Photon (photon.komoot.io) — browser-direct, no API key, OSM-backed (ADR-006). Cache + throttle + attribution in `api/geocode.ts`. FastAPI `GET /api/v1/geocode` retained but unused by frontend. **Production scaling:** Cloudflare Workers proxy for global cache + aggregate rate limiting (ADR-009).
- **Production:** DuckDB WASM + Cloudflare Pages + Cloudflare R2 ($0/month)
- **Tests:** pytest-bdd (Gherkin) + pytest-playwright + Schemathesis

Do not deviate from this stack without a new ADR and maintainer RFC.

---

## Map Data Flow (2026-07-28)

```
TRI Browse mode ────────► GET /api/v1/facilities/browse ────► All ~22k facilities
Superfund Browse ───────► GET /api/v1/superfund/browse ─────► All ~1.7k sites
                                                             │
Search mode (submitted) ► GET /api/v1/{facilities|superfund}?lat=...&radius=... ► Radius-filtered results
```

- **Browse mode:** Both layers fetch all data once via `/browse` endpoints (no radius constraint)
- **Search mode:** Frontend passes `{ lat, lon, radiusMiles, ... }` → hooks call radius endpoints
- **Viewport rendering:** MapLibre handles viewport clipping automatically from full datasets
- **TRI toggle:** `setLayoutProperty('facility-circles', 'visibility', ...)`
- **Superfund toggle:** `setLayoutProperty('superfund-sites', 'visibility', ...)`

---

## 10 UX Invariants (Must Never Break)

> **Source of truth:** `agents/frontend-engineer/prompt.md §The 10 UX Invariants`. The list below is the exact authoritative set. Every invariant has a Playwright test and a `data-testid` in `TEST_ID_REGISTRY.md`. Phase Advancement Gates 3→4 and 5→6 gate on these exact invariants by number.

| # | Rule | Key `data-testid` |
|---|------|------------------|
| 1 | **Single sidebar** — Map Contents and Search Results never visible simultaneously | `map-contents-panel` hidden when search active |
| 2 | **No empty table rows** — Results table shows only in-viewport facilities (`useViewportFacilities`; re-fetch on map move with `bbox=`) | `results-table` |
| 3 | **State filter restricts, not only zooms** — State dropdown labeled "Filter to state (optional)" filters results when set | `state-select` |
| 4 | **Correct panel labels** — "Search Chemical Releases by Location" (not "Quick Search"); "US Census & Health Data" (not "Demographics") | `search-panel` label check |
| 5 | **Inline demographic legend** — Legend values and units visible at all times, not mouse-over only | `inline-legend` |
| 6 | **Distinct icon shapes** — TRI = circle, Superfund = diamond; no icon reuse with hospitals | marker `marker_shape` from API |
| 7 | **"(latest year)" label** — Most-recent year in layer toggles shows `(latest year)` appended | `year-toggle-latest` |
| 8 | **Comma-formatted numbers** — All release quantities: `8,205 lbs` not `8205 lbs` | `results-row-release` |
| 9 | **Close link at bottom of popup** — Facility popup has a close link at the bottom, not only a corner X | `popup-close-bottom` |
| 10 | **Co-occurrence disclaimer on mortality tab only** — "Correlation does not imply causation" on cancer/heart disease tab; NOT on income/population tabs | conditional render by active tab |

---

## 5 Security Guardrails (Absolute Rules)

| Rule | Why |
|------|-----|
| Never f-string SQL with user input — always parameterized SQLAlchemy or `$variable` DuckDB | SQL injection (T-SEC-02, T-SEC-03) |
| Never commit API keys, DB passwords, Cloudflare tokens | Credential leakage (T-SEC-06) |
| Never use `VITE_`-prefixed env vars for secrets | All `VITE_` vars are inlined into the public browser bundle (T-SEC-07) |
| Never pin a GitHub Action to a mutable tag (`@v3`) | Supply chain attack (T-SEC-08) |
| Never set `ALLOWED_ORIGINS = ["*"]` in FastAPI | Open CORS breaks API security model |

---

## 2 Immutable Seed Values

These come from a peer-reviewed NLM study. Do not alter them under any circumstances:

- `89319BHPCP7MILE` → copper → **8205.0 lbs** → land medium → year 2008 (T-01/T-03)
- `VAD070358684` → **AVTEX FIBERS INC** → FRONT ROYAL, VA (T-04)

`null` ≠ `0` for `total_release_lbs`. `null` = data absent; `0` = zero releases reported.

---

## 11 Protected Files (Read-Only for Agents)

> **2026-07-28 note:** Maintainer granted permission to update all protected files to
> reflect Superfund browse endpoint architecture changes (matching TRI browse pattern).
> Future sessions should treat this list as read-only again.

```
TOXMAP_API_CONTRACT.md
TOXMAP_ACCEPTANCE_TESTS.md
TOXMAP_TEST_SEED_DATA.md
tests/fixtures/seed.sql
ADR-001-fastapi-postgis-react.md
ADR-002-spring-modulith-postgis.md
ADR-003-nextjs-serverless-postgis.md
ADR-004-zero-budget-hosting.md
TOXMAP_DEVELOPMENT_ROADMAP.md
TOXMAP_TECH_STACK_ANALYSIS.md
SECURITY.md
```

If a change to any of these seems required, open a `[clarification-needed]` issue (or write
`docs/escalations/ESCALATION_[timestamp].md` if GitHub write access is unavailable) and stop.

---

## Per-Role Minimum Context

| Role | Must Load | Also Recommended |
|------|-----------|-----------------|
| OPS | `CURRENT_PHASE.txt` + `TOXMAP_PROGRESS_TRACKER.md` + `agents/devops-engineer/prompt.md` | ADR-001 §Docker, ADR-004 §Cloudflare |
| BE | `CURRENT_PHASE.txt` + `agents/backend-engineer/prompt.md` + `TOXMAP_API_CONTRACT.md` | ADR-001 §DDL, `TOXMAP_ACCEPTANCE_TESTS.md` |
| DE | `CURRENT_PHASE.txt` + `agents/data-engineer/prompt.md` + `TOXMAP_TEST_SEED_DATA.md` | ADR-001 §DDL, ADR-004 §Parquet |
| FE | `CURRENT_PHASE.txt` + `agents/frontend-engineer/prompt.md` + `TOXMAP_API_CONTRACT.md` | ADR-004 §DuckDB WASM, `TOXMAP_SCREEN_CATALOG.md` |
| QA | `CURRENT_PHASE.txt` + `agents/quality-engineer/prompt.md` + `TOXMAP_ACCEPTANCE_TESTS.md` | `TOXMAP_TEST_SEED_DATA.md`, ADR-001 §testid |
| SEC | `CURRENT_PHASE.txt` + `agents/security-engineer/prompt.md` + `GOVERNANCE.md §8` | `docs/security/THREAT_MODEL.md` |
| PM | `CURRENT_PHASE.txt` + `TOXMAP_PROGRESS_TRACKER.md` + `agents/phase-manager/prompt.md` | Roadmap §current phase |

---

## Phase Sequence at a Glance

| Phase | Lead | Goal |
|-------|------|------|
| 0 | OPS | Repo, Docker, CI, security baseline |
| 1 | DE | TRI + Superfund + Census → PostGIS + Parquet |
| 2 | BE | 17 domain endpoints + `/api/v1/meta` + API tests green |
| 3 | FE | Map + search + markers → T-01, T-03, T-08 E2E pass |
| 4 | FE | Superfund diamond markers → T-02, T-04 E2E pass |
| 5 | FE | Census overlays → T-05, T-06, T-09 E2E pass |
| 6 | QA | All Gherkin pass + SLAs + security regression |
| 7 | FE+OPS | Cloudflare Pages + DuckDB WASM + $0 deploy — **MVP** |
| 8 | DE | Tribal lands data — `bia_code`/`tribe_name` columns, tribal filter (post-MVP) |

