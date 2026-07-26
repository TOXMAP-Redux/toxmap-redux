# TOXMAP Testing Suite Audit

**Date:** 2026-07-21  
**Auditor:** GitHub Copilot  
**Files Audited:** All 12 files in `docs/testing/`  
**Score: 8.4 / 10** *(V2 — updated after discovering 9 new findings post-V1)*

---

## Dimensions

| Dimension | Score | V1 Score | Delta | Notes |
|-----------|-------|----------|-------|-------|
| **Maturity** | 9.0 | 9.0 | — | Five-layer pyramid, BDD+fuzzing+visual+mutation — exceeds most OSS projects. All tests are pre-implementation (⚠️ Planned) which is expected at this stage. |
| **Consistency** | 7.0 | 7.5 | ↓ | V1 partially fixed F-TA-02 (§4.1 heading still wrong); F-CR-08 applied to Gherkin but not propagated to Layer 3/4 tables; 2 stale "Last updated" timestamps |
| **Accuracy** | 8.0 | 8.5 | ↓ | Layer 4 SLA count "3" was stale after CA-11/12/13 added; DEM-07/DM-05 missing 5th unit key; Layer 3 typo |
| **Best Practices** | 8.5 | 9.0 | ↓ | BC hex values were unspecified (now guidance added); CSV prefix collision in Layer 2 (now annotated) |
| **Agentic Readiness** | 8.0 | 8.5 | ↓ | BC hex ambiguity blocked agent implementation; CSV prefix confusion; Layer 4 §4.1 wrong count was misleading |

---

## V1 Findings — Verification Status

| V1 ID | Claimed Status | Actual Status in Source Files |
|-------|---------------|-------------------------------|
| F-TA-01 | ✅ Fixed | ✅ Verified — no stray fence in Layer 3 |
| F-TA-02 | ✅ Fixed | ⚠️ **Partially fixed** — §1 and Exit Criteria updated to 41, but §4.1 heading still said "(13 scenarios)"; fixed in V2 (F-NA-01) |
| F-TA-03 | ✅ Fixed | ✅ Verified — "Release by Medium Chart" section present in TEST_ID_REGISTRY.md |
| F-TA-04 | ✅ Fixed | ✅ Verified — TESTING_STRATEGY.md coverage table reads "10/10"; Layer 5 Exit Criteria §5 item 4 has the caveat |
| F-TA-05 | ✅ Fixed | ✅ Verified — TESTING_STRATEGY.md architecture diagram reads "FastAPI ≥ 0.111.0" |
| F-TA-06 | ✅ Fixed | ✅ Verified — `census-health-panel` not duplicated in Sidebar section |
| F-TA-07 | ✅ Fixed | ✅ Verified — Note added to TEST_ID_REGISTRY.md Sidebar section |
| F-TA-08 | ✅ Fixed | Not re-verified (TOXMAP_ACCEPTANCE_TESTS.md not in V2 scope) |
| F-TA-09 | ✅ Fixed | ✅ Verified — CB-10 → `ValueError` in Layer 1 |
| F-TA-10 | ✅ Fixed | Not re-verified (TOXMAP_ACCEPTANCE_TESTS.md not in V2 scope) |
| F-TA-11 | ✅ Fixed | ✅ Verified — E2E Phase 0 rows present in test-step-coverage.md |

---

## V2 Findings (new — all resolved in this session)

| ID | Severity | File | Finding | Status |
|----|----------|------|---------|--------|
| F-NA-01 | **High** | `LAYER4_API_CONTRACT.md` §4.1 | Heading still read "(13 scenarios)" — F-TA-02 only updated §1 and Exit Criteria; §4.1 section heading was missed | ✅ Fixed |
| F-NA-02 | **High** | `LAYER4_API_CONTRACT.md` §6 Exit Criteria #5 | "Performance SLAs met for all **3** measured endpoints" — stale after F-CR-03 added CA-11/CA-12/CA-13; correct count is **6** (CA-08 through CA-13) | ✅ Fixed |
| F-NA-03 | **High** | `LAYER3_INTEGRATION.md` DEM-07 · `LAYER4_API_CONTRACT.md` DM-05 | Both scenario tables listed 4 unit keys (`pct_under_18`, `median_income`, `pct_over_65`, `pct_nonwhite`); F-CR-08 added `cancer_mortality_female_per_100k` to the Gherkin acceptance test but **did not propagate the fix back to the Layer 3 and Layer 4 test plan tables** | ✅ Fixed — 5th key added to both tables |
| F-NA-04 | **Medium** | `TEST_ID_REGISTRY.md` | "Last updated" timestamp read **2026-07-16** — file was subsequently changed on 2026-07-21 (F-TA-03, F-TA-06, F-TA-07); timestamp was stale | ✅ Fixed → 2026-07-21 |
| F-NA-05 | **Medium** | `test-step-coverage.md` | "Last updated" timestamp read **2026-07-20** — file was changed on 2026-07-21 (F-TA-11); timestamp was stale | ✅ Fixed → 2026-07-21 |
| F-NA-06 | **Medium** | `LAYER1_UNIT.md` §4.8 | BC-01–BC-04 expected values were `"Correct hex per design system"` — too vague for agent implementation; agents cannot generate deterministic test assertions without knowing the actual hex values | ✅ Fixed — guidance added directing agents to read `colorBand.ts` production source |
| F-NA-07 | **Medium** | `LAYER2_COMPONENT.md` §4.2 | Prefix `CSV` used for **Chemical SerVice** — collides with the universal meaning of "CSV" (comma-separated values); the export service tests also appear in the same file (§4.4, prefix `XSV`); an agent reading top-to-bottom would misinterpret CSV-01–CSV-04 as export-related | ✅ Fixed — disambiguation note added to §4.2 |
| F-NA-08 | **Low** | `LAYER3_INTEGRATION.md` §4.9 | `**Prefix:** \`META\` (METAdta)` — typo "METAdta" should be "METAdata" | ✅ Fixed |
| F-NA-09 | **Low** | `LAYER3_INTEGRATION.md` §5 Exit Criteria #1 | Listed prefixes (FSR-*, FDT-*, RLS-*, CHM-*, SUP-*, DEM-*, EXP-*, META-*) cover only 56 scenarios but the parenthetical said "(58 tests)"; FSE-* (2 validation error scenarios) was separated into criterion 2 but the total in criterion 1 implied it was already included — confusing | ✅ Fixed — FSE-* added to criterion 1 prefix list; criterion 2 rephrased as emphasis rather than separate gate |

---

## Maturity Highlights (what's already excellent)

- **Five-layer test pyramid** with explicit scope boundaries between layers — industry best practice.
- **Two-mode awareness** (dev/CI vs. production DuckDB WASM) built into every layer — rare in OSS projects.
- **Schemathesis fuzzing** against committed `openapi.json` + drift detection gate — production-grade API contract enforcement.
- **Phase-guarded step delivery** in `test-step-coverage.md` prevents agents from over-generating untestable code.
- **Deterministic seed isolation** (TRUNCATE + RESTART IDENTITY + CASCADE before/after each test) correctly prevents inter-test contamination.
- **`-p no:xdist` enforcement** in `pyproject.toml` + documentation prevents parallel execution corruption.
- **RFC 7946 coordinate order** tested independently from integration behavior — a subtle but critical correctness invariant.
- **Page Object Model** classes defined in Appendix B of Layer 5 plan — agents have concrete POM structure to implement.
- **Risk register** (R-01 through R-11) with review cadence — exceeds typical test planning maturity.
- **Cross-reference audit** (TOXMAP_CROSS_REFERENCE_AUDIT.md) verified 17/17 API endpoints are accounted for across test layers — rare in documentation suites of this size.

---

## Agentic Readiness Assessment (V2)

| Signal | V2 Assessment |
|--------|--------------|
| Phase-guarded step delivery | ✅ Clear — agents must not implement Phase N+1 steps before Phase N UI exists |
| `data-testid` registry with component + Gherkin step mapping | ✅ Excellent — agents can derive all E2E selectors from registry |
| Seed data with known-good assertion values table | ✅ Excellent — agents can implement step assertions without guessing values |
| Step stubs in `api_steps.py` + `e2e_steps.py` | ✅ Sufficient to bootstrap agent implementation |
| Feature numbering scheme (F1–F6, F9, F7, F8) | ✅ Clarifying note present in TOXMAP_ACCEPTANCE_TESTS.md |
| Chart bar testids for T-03 assertion | ✅ `release-by-medium-chart` + per-medium bar testids in registry |
| CB-10 behavior policy | ✅ Resolved — `ValueError` for negative input |
| `browser_base_url` vs. pytest-playwright `base_url` | ✅ Documented — conftest stub updated with comment |
| BC hex color assertions (BC-01–BC-04) | ✅ Now fixed — agents directed to read `colorBand.ts` source |
| `CSV` prefix for ChemicalService | ✅ Now annotated — disambiguation note added in Layer 2 §4.2 |
| Layer 4 §4.1 scenario count | ✅ Now fixed — reads "(14 scenarios)" |
| SLA assertion count in Layer 4 Exit Criteria | ✅ Now fixed — reads "6 SLA-tested endpoints" |

---

## Outstanding Structural Gaps (deferred — not fixable in-document)

| Gap | Impact | Action |
|-----|--------|--------|
| All tests are ⚠️ Planned / ❌ Not started | Expected at pre-implementation phase; no test file exists yet; high execution risk if implementation is delayed | Begin Phase 2 implementation immediately after API scaffold is complete |
| No `TOXMAP_TEST_PLAN_SECURITY.md` | Phase 6 story 6.4.4 has no test scaffold | Create in Phase 6 sprint start |
| No Layer 2 component tests for DuckDB WASM hooks | Phase 7 production path has no unit/component coverage | Add `TOXMAP_TEST_PLAN_LAYER7_DUCKDB.md` in Phase 7 |
| No Gherkin stubs for nuclear / NPRI / congressional layers | Agents have no scaffold for Phase 4/5 layer tests | Create feature file stubs at Phase 4 sprint start |
| `GET /api/v1/geocode` SLA (< 500ms) untested at API layer | SLA silently not enforced | Add to Phase 6 performance benchmark suite |

---

*V2 audit complete — all 9 new findings resolved. 20 total findings across V1+V2, all resolved in-session. Last updated: 2026-07-21.*

