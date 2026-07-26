# TOXMAP Testing ↔ Product/Architecture Cross-Reference Audit

**Date:** 2026-07-21  
**Auditor:** GitHub Copilot  
**Source Documents Compared:**
- `docs/testing/` — all 10 testing files (post testing-audit V1)
- `docs/product/TOXMAP_DEVELOPMENT_ROADMAP.md`
- `docs/product/TOXMAP_SCREEN_CATALOG.md`
- `docs/api/TOXMAP_API_CONTRACT.md`
- `docs/adr/ADR-001-fastapi-postgis-react.md` · `ADR-004-zero-budget-hosting.md`
- `CONTEXT_SUMMARY.md`

**Overall Consistency Rating: 7.8 / 10**  
*(High structural alignment; 9 actionable gaps found, all resolved in-session)*

---

## Dimension Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Roadmap ↔ Tests** | 7.5 | Phase 2 DoD omits Feature 9; security + DuckDB test plans missing |
| **API Contract ↔ Tests** | 7.5 | 5 of 8 performance SLAs not in Layer 4; 2 endpoints absent from test scope; 1 data inconsistency |
| **Screen Catalog ↔ Tests** | 8.5 | Chart structure consistent; deferred layers correctly noted; `marker_shape` assertion missing |
| **Architecture ↔ Tests** | 9.0 | Two-mode awareness correct; coordinate convention enforced; schema types consistent |
| **Internal Test Consistency** | 9.0 | ↑ from 7.5 after testing-audit V1 |

---

## Findings

| ID | Severity | Source Conflict | Finding | Status |
|----|----------|-----------------|---------|--------|
| **F-CR-01** | High | API Contract §9 ↔ Seed Data §6 | Warren County VA (`51187`) `cancer_mortality_female_per_100k` is `null` in the API contract example JSON but `148.7` in `seed.sql` and §6 Known Good values — misleads agents implementing the demographics serializer | ✅ Fixed — API contract example corrected to `148.7` |
| **F-CR-02** | High | Roadmap Phase 2 DoD ↔ test-step-coverage.md | Phase 2 DoD says "Features 1–6 pass"; Feature 9 (Data Vintage Metadata) is also Phase 2 per `test-step-coverage.md` and Layer 4 Appendix — Feature 9 omitted from the Phase 2 gate | ✅ Fixed — Roadmap Phase 2 DoD updated to "Features 1–6 and Feature 9" |
| **F-CR-03** | High | API Contract SLA table ↔ Layer 4 CA-* | Layer 4 has 3 performance assertions (CA-08 radius, CA-09 autocomplete, CA-10 mislabeled "Facility detail"); the API contract defines 8 SLAs — 5 are untested: viewport bbox re-fetch (200ms), Superfund (300ms), CSV first-byte (1,000ms), demographics/county (400ms); CA-10 label incorrect | ✅ Fixed — CA-10 relabeled; CA-11/12/13 added for missing SLAs |
| **F-CR-04** | Medium | API Contract §7 + Roadmap 2.4.1 ↔ Acceptance Tests F4 | Feature 4 Superfund Gherkin asserts `epa_id, name, hrs_score, status, contaminants` but never asserts `marker_shape == "diamond"` — the key contract invariant distinguishing Superfund from TRI markers (UX Invariant 6) | ✅ Fixed — assertion added to F4 Scenario 2 |
| **F-CR-05** | Medium | API Contract §15 ↔ Layer 4 Out of Scope | `GET /api/v1/export/map-metadata` (endpoint 15) is in the API contract and roadmap story 2.6.3 but has no Gherkin feature, no integration test, and is not listed in Layer 4 Out of Scope — agents have no signal that it is intentionally untested | ✅ Fixed — added to Layer 4 Out of Scope with delivery note |
| **F-CR-06** | Medium | API Contract §16 ↔ Layer 4 Out of Scope | `GET /api/v1/geocode` (endpoint 16/7) is dev-only with a 500ms SLA defined in the API contract but has no Layer 3 or Layer 4 test scenario and is not in any Out of Scope section — the SLA is silently untested | ✅ Fixed — added to Layer 4 Out of Scope; SLA coverage deferred to Layer 5 E2E (implicit via location input steps) |
| **F-CR-07** | Low | Roadmap Phase 4/5 epics ↔ Acceptance Tests | Nuclear, NPRI, and Congressional Districts layers are in the roadmap (Phase 4/5) and API contract but have no corresponding Gherkin feature stubs in `TOXMAP_ACCEPTANCE_TESTS.md`; when implemented, agents will have no test scaffold to follow | ✅ Fixed — note added to `test-step-coverage.md` with scaffolding instructions |
| **F-CR-08** | Low | API Contract §9 `meta.units` ↔ Gherkin F5 | Feature 5 Gherkin asserts units for `pct_under_18`, `median_income`, `pct_over_65`, `pct_nonwhite` but omits `cancer_mortality_female_per_100k: "per 100,000"` — the API contract requires this field in every `meta.units` response | ✅ Fixed — assertion added to F5 demographics unit scenario |
| **F-CR-09** | Low | Roadmap Phase 6 Story 6.4.4 ↔ Testing Strategy | Phase 6 story 6.4.4 requires `tests/security/` (rate limiting 429, error sanitization, input validation); no security test plan document exists in `docs/testing/`; `TOXMAP_TESTING_STRATEGY.md` lists Security as a cross-cutting concern but gives no file path | ✅ Fixed — note added to `TOXMAP_TESTING_STRATEGY.md` §3 + §8 |

---

## Structural Coverage Matrix

| API Endpoint | Gherkin Feature | Layer 3 Plan | Layer 4 Plan | Status |
|-------------|----------------|-------------|-------------|--------|
| `GET /api/v1/facilities` | F1 ✓ | FSR-* ✓ | FS-01–14 ✓ | ✅ |
| `GET /api/v1/facilities/{id}` | F1 ✓ | FDT-* ✓ | FS-11–12 ✓ | ✅ |
| `GET /api/v1/facilities/{id}/releases` | F2 ✓ | RLS-* ✓ | RT-* ✓ | ✅ |
| `GET /api/v1/releases/largest` | F2 ✓ | RLS-06/07 ✓ | RT-04/05 ✓ | ✅ |
| `GET /api/v1/chemicals` | F3 ✓ | CHM-01/02 ✓ | CH-01 ✓ | ✅ |
| `GET /api/v1/chemicals/search` | F3 ✓ | CHM-03–07 ✓ | CH-02–05 ✓ | ✅ |
| `GET /api/v1/geocode` ⚠️ dev-only | — | — | Out of Scope ✓ | ✅ Documented |
| `GET /api/v1/superfund` | F4 ✓ | SUP-* ✓ | SF-* ✓ | ✅ |
| `GET /api/v1/superfund/{id}` | F4 ✓ | SUP-04 ✓ | SF-03 ✓ | ✅ |
| `GET /api/v1/demographics/county` | F5 ✓ | DEM-* ✓ | DM-* ✓ | ✅ |
| `GET /api/v1/demographics/tract` | F5 ✓ | DEM-08 ✓ | DM-04 ✓ | ✅ |
| `GET /api/v1/layers/nuclear` | — | Deferred Ph4 | Out of Scope ✓ | 🟡 Phase 4 |
| `GET /api/v1/layers/npri` | — | Deferred Ph5 | Out of Scope ✓ | 🟡 Phase 5 |
| `GET /api/v1/layers/congressional-districts` | — | Deferred Ph5 | Out of Scope ✓ | 🟡 Phase 5 |
| `GET /api/v1/export/csv` | F6 ✓ | EXP-* ✓ | EX-* ✓ | ✅ |
| `GET /api/v1/export/map-metadata` | — | — | Out of Scope ✓ | ✅ Documented |
| `GET /api/v1/meta` ⚠️ dev-only | F9 ✓ | META-* ✓ | MT-* ✓ | ✅ |

**17/17 endpoints accounted for** (12 fully tested, 3 phased, 2 explicitly out of scope).

---

## Performance SLA Coverage Matrix (post-fix)

| API Contract SLA | Target | Layer 4 ID | Status |
|-----------------|--------|-----------|--------|
| `GET /api/v1/facilities` radius ≤ 50mi | p95 < 500ms | CA-08 | ✅ |
| `GET /api/v1/facilities` viewport bbox | p95 < 200ms | CA-10 | ✅ |
| `GET /api/v1/chemicals/search` | p95 < 100ms | CA-09 | ✅ |
| `GET /api/v1/superfund` radius ≤ 50mi | p95 < 300ms | CA-11 | ✅ Added |
| `GET /api/v1/export/csv` first byte | p95 < 1,000ms | CA-12 | ✅ Added |
| `GET /api/v1/demographics/county` | p95 < 400ms | CA-13 | ✅ Added |
| `GET /api/v1/geocode` | p95 < 500ms | E2E implicit | 🟡 Phase 5 E2E |
| `GET /api/v1/meta` | p95 < 50ms | — | 🟡 Phase 6 perf suite |

---

## Verified Consistency (no changes needed)

| Item | Verified |
|------|---------|
| Color band thresholds: 0–999 green, 1K–9K yellow, 10K–99K orange, ≥100K red | ✅ API contract § = Layer 1 CB-01–CB-09 = Pydantic `ColorBand` enum |
| Coordinate order `[lon, lat]` RFC 7946 | ✅ API contract §Common Patterns = Layer 1 GB-02 = Layer 4 CA-05 = R-01 risk |
| T-03 exact UCD 2011 values (8,205 lbs, land-only, Robinson NV) | ✅ API contract §3 = Seed §3 = Acceptance Test F2 = Layer 1 FF-01 |
| T-04 exact UCD 2011 values (AVTEX FIBERS, VAD070358684) | ✅ API contract §8 = Seed §4 = Acceptance Test F4 |
| Comma formatting responsibility: frontend only (not API) | ✅ API contract §Common/Number Formatting = Layer 1 CF-02 = E2E Invariant 8 |
| `vintage_label` fallback to `"unknown"` in seed | ✅ API contract §17 = Seed §10 = Layer 1 MB-01 = Feature 9 MT-04 |
| `restrict_to_state` checkbox → state filter | ✅ Roadmap 3.2.6 = TEST_ID_REGISTRY `restrict-to-state-checkbox` = UX Invariant 3 |
| Three-tab bar chart: chemicals/medium/trends | ✅ Screen catalog Fig 11 = Roadmap 3.4.3 = TEST_ID_REGISTRY `facility-chart-tab-1/2/3` |
| Diamond shape for Superfund markers | ✅ Screen catalog Fig 9 = API contract §7 `marker_shape:"diamond"` = Roadmap 4.1.1 = UX Invariant 6 |
| Phase-by-phase E2E scenario delivery | ✅ Roadmap Phase 3→5 E2E tables = test-step-coverage.md phase assignments = Layer 5 Deferred table |
| `data-vintage-label` testid = Phase 3 gate DoD | ✅ Roadmap 3.1.5 = TEST_ID_REGISTRY = test-step-coverage Feature 8 item 11 |
| `-p no:xdist` single-threaded enforcement | ✅ Seed §8 conftest comment = Layer 3 §2 = Layer 5 §2 = Strategy R-08 |
| `postgis/postgis:16-3.4` pinned image | ✅ Strategy §4 = Layer 3 §2 = Roadmap Constraint table |

---

## Outstanding Structural Gaps (deferred — require new documents or stories)

| Gap | Impact | Recommended Action |
|-----|--------|-------------------|
| No `tests/security/` test plan document | Phase 6 story 6.4.4 has no test scaffold | Create `TOXMAP_TEST_PLAN_SECURITY.md` in Phase 6 |
| No Layer 2 component tests for DuckDB WASM hooks (`useDuckDBFacilities` etc.) | Phase 7 production path has no unit/component coverage | Add `TOXMAP_TEST_PLAN_LAYER7_DUCKDB.md` or extend Layer 2 in Phase 7 |
| No Gherkin feature stubs for nuclear / NPRI / congressional layers | QA cannot start Phase 4/5 layer tests without feature files | Add `features/api/nuclear.feature` stub in Phase 4 sprint start |
| `GET /api/v1/geocode` performance SLA (< 500ms) defined but untested at API layer | SLA may never be verified | Add to Phase 6 performance benchmark suite |

---

*All 9 actionable findings resolved. 4 structural gaps documented. Updated: 2026-07-21.*

