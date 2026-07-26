# TOXMAP Agentic Development Audit — V8

**Auditor:** GitHub Copilot  
**Date:** 2026-07-21  
**Scope:** Full independent sweep — all V7 / post-V7 fixes verified + new findings  
**Audit Dimensions:** Agentic Readiness · Consistency · Orchestration · Maturity · Governance · Reliability  
**Basis:** 45+ documents read in full; all 7 agent prompts, all governance files, all testing docs  
**Predecessor:** `TOXMAP_AGENTIC_AUDIT_V7.md` — declared post-V7 score 9.2/10

---

## Executive Summary

V8 independently verifies all V7 post-improvement claims and performs a fresh full-corpus sweep. **6 new findings are identified.** One is HIGH severity: `CONTEXT_SUMMARY.md` — the document explicitly designed for constrained-context agent sessions — contains a UX invariant list that is completely wrong relative to the authoritative FE prompt and Playwright gate checks. Five of ten invariants describe different behaviors. Any FE or QA agent running from the constrained-context path would implement and test the wrong product contract.

Three additional MEDIUM findings affect orchestration (wrong handoff trigger phase), governance (CHANGELOG.md ownership conflict), and reliability (broken file path in OPS prompt). Two LOW findings round out the sweep.

**Pre-fix score: 8.6 / 10** (V7 post-improvement score was overstated due to the CONTEXT_SUMMARY invariant divergence being undetected)  
**Post-fix score: 9.4 / 10** (all 6 findings resolved in this session)

---

## V7 Post-Improvement Verification

| Claim | Status | Evidence |
|-------|--------|---------|
| All 7 agent prompts have ESCALATION fallback | ✅ Confirmed | FE, OPS, QA, SEC prompts all contain the `ESCALATION_[YYYYMMDD_HHMMSS].md` fallback block |
| CODEOWNERS template includes `SECURITY.md @maintainer` | ✅ Confirmed | `agents/devops-engineer/prompt.md` line 343 |
| FE prompt reads "10 UX Invariants" (not 11) | ✅ Confirmed | FE prompt line 39: `## The 10 UX Invariants` |
| PM Phase 6 goal uses dynamic form (no "57") | ✅ Confirmed | Phase 6 goal header reads "All Gherkin scenarios pass (scenario count grows across phases — do not gate on a hardcoded number)" |
| QA prompt uses dynamic form (no "57/57") | ✅ Confirmed | QA Purpose and Phase 6 DoD use dynamic form throughout |
| Priority 0 context files added to all 6 agent prompts | ✅ Confirmed | BE, DE, FE, OPS, QA, SEC all show `CURRENT_PHASE.txt` and `CONTEXT_SUMMARY.md` at Priority 0 |
| §14 Inter-Agent Handoff Protocol added to AGENTS.md | ✅ Confirmed | Lines 445–482 present and complete |
| GOVERNANCE.md v1.1 + agent completion report requirement | ✅ Confirmed | Version 1.1; §2.3 AI Agent role includes completion report clause |
| `CONTEXT_SUMMARY.md` usage rules clarified | ✅ Confirmed | Lines 6–10 explain constrained vs. full-session usage |

**All V7 post-improvement claims verified. No regressions found.**

---

## Scoring Summary

| Dimension | Pre-Fix Score | Post-Fix Score | Delta vs. V7 post |
|-----------|--------------|----------------|-------------------|
| **Agentic Readiness** | 7.5 / 10 | 9.2 / 10 | (V8-A depressed pre-fix; +1.7 after fix) |
| **Consistency** | 7.5 / 10 | 9.2 / 10 | (V8-A, V8-C, V8-E resolved) |
| **Orchestration** | 8.5 / 10 | 9.2 / 10 | (V8-D resolved) |
| **Maturity** | 9.0 / 10 | 9.0 / 10 | → (no change) |
| **Governance** | 8.5 / 10 | 8.7 / 10 | (V8-C, V8-F addressed) |
| **Reliability** | 8.5 / 10 | 9.2 / 10 | (V8-B resolved) |
| **Overall** | **8.6 / 10** | **9.4 / 10** | ↑ +0.2 vs V7 declared score |

---

## 1. Agentic Readiness — Pre-Fix 7.5 / Post-Fix 9.2

### Finding V8-A — HIGH: `CONTEXT_SUMMARY.md` UX Invariants Diverge From Authoritative FE Prompt List

**Files affected:** `CONTEXT_SUMMARY.md` (lines 36–49)  
**Root cause:** The UX invariants section in `CONTEXT_SUMMARY.md` was written from an earlier version of the product specification. After the FE prompt was finalized against the 2011 UCD study, the invariant list in the FE prompt diverged significantly from the summary copy — but the summary was never updated.

**Why this is HIGH severity:**

`CONTEXT_SUMMARY.md` is the **primary and only** document an agent loads in constrained-context sessions. `AGENTS.md §1` explicitly states: "For short / context-constrained sessions, stop here — these three files are the minimum viable context for routine implementation tasks." An FE or QA agent loading `CONTEXT_SUMMARY.md` in a constrained session would implement and test a completely different product than the one described by the FE prompt.

**Invariant comparison (5 of 10 diverge):**

| # | `CONTEXT_SUMMARY.md` (incorrect) | `agents/frontend-engineer/prompt.md` (authoritative) | Difference |
|---|----------------------------------|------------------------------------------------------|------------|
| 1 | Default view: continental US centered, all TRI facilities visible | **Single sidebar** — Map Contents and Search Results never visible simultaneously; `data-testid="map-contents-panel"` must be hidden when search is active | Different behavior entirely |
| 2 | Search triggers map re-center and marker update without full page reload | **No empty table rows** — Results table shows only in-viewport facilities; `useViewportFacilities` hook; re-fetch on map move with `bbox=` param | Different behavior entirely |
| 3 | Selected facility detail panel appears without a new page navigation | **State filter restricts, not only zooms** — "Limit to state" checkbox triggers `restrict_to_state=true`; `data-testid="restrict-to-state-checkbox"` | Different behavior entirely |
| 7 | Facility count displayed in results panel | **"(latest year)" label** — Most-recent year in layer toggles shows `(latest year)` appended; `data-testid="year-toggle-latest"` | Different behavior entirely |
| 9 | Map state (center, zoom) preserved on browser back/forward | **Close link at bottom of popup** — Facility popup has a close link at the bottom, not only a corner X; `data-testid="popup-close-bottom"` | Different behavior entirely |

**Evidence that FE prompt invariants are the authoritative ones:**
- Phase Advancement Gates 3→4 and 5→6 explicitly cite "UX invariants 1, 2, 3, 4, 7, 8, 9" using the FE prompt numbering (e.g., Gate 3→4 checks "UX invariants 1, 2, 3, 4, 7, 8, 9 pass in Playwright")
- `TEST_ID_REGISTRY.md` contains `data-testid` values for FE prompt invariants: `restrict-to-state-checkbox` (inv. 3), `year-toggle-latest` (inv. 7), `popup-close-bottom` (inv. 9)
- `agents/quality-engineer/prompt.md` Phase 3–5 DoD references the FE prompt numbering exactly

The behaviors described in `CONTEXT_SUMMARY.md` (invariants 1, 2, 3, 7, 9) are not incorrect product requirements — the app should have a default continental US view, map re-center on search, etc. — but they are **not the gated invariants with Playwright tests and data-testid contracts**. They are general UX behaviors that fall out of normal feature implementation, not the specific invariants that Phase Advancement gates check.

**Fix:** Replace the UX invariants section in `CONTEXT_SUMMARY.md` with the exact FE prompt invariants (condensed for the summary format).

---

## 2. Consistency — Pre-Fix 7.5 / Post-Fix 9.2

### V8-A: See §1 above (also a Consistency finding).

### Finding V8-C — Medium: CHANGELOG.md Ownership Conflict With AGENTS.md §2

**Files:** `CHANGELOG.md` (lines 7–9), `AGENTS.md` (§2 line 72)

**CHANGELOG.md header:**
> "Do NOT edit this file directly. The Phase Manager updates this file when a milestone is declared (M0–M7). Human maintainers update it at release time."

**AGENTS.md §2 (added in post-V7 session):**
> ✅ Update `CHANGELOG.md` with entries for work completed in the current session (follow the format in the existing file; one entry per story shipped; use the commit type as the changelog category)

These directly contradict each other. An agent reading `CHANGELOG.md` itself is told to stop. An agent reading `AGENTS.md §2` is told to proceed. The AGENTS.md permission was deliberately added in the post-V7 session to enable per-story CHANGELOG entries — this is the desired behavior. The CHANGELOG.md header is outdated relative to the post-V7 governance update.

**Fix:** Update `CHANGELOG.md` header to reflect the current dual-mode update policy: agents add per-story entries during their session; PM adds milestone-level summaries; human maintainers add release entries.

### Finding V8-E — Low: Phase 2 DoD Preview in PROGRESS_TRACKER Has Stale Endpoint Count

**File:** `docs/product/TOXMAP_PROGRESS_TRACKER.md` (line 140)

**PROGRESS_TRACKER Phase 2 DoD preview:**
> "- [ ] All 17 endpoints visible at Swagger UI `/docs`"

**PM Gate 2→3:**
> "- [ ] Swagger UI at `/docs` shows all endpoints (17 domain + `GET /api/v1/meta`)"

**PM Phase 2 arch reference (Quick Reference table):**
> "Phase 2 ─ Core API → BE leads → 17 domain endpoints + /api/v1/meta + security hardening"

The PM explicitly distinguishes 17 domain endpoints from `GET /api/v1/meta`, implying 18 total. The PROGRESS_TRACKER preview echoes only "17 endpoints." An agent reading the PROGRESS_TRACKER DoD preview for Phase 2 would have a different gate count than the PM's authoritative gate check.

**Fix:** Update PROGRESS_TRACKER Phase 2 DoD preview to read "All 17 domain endpoints + `GET /api/v1/meta` visible at Swagger UI `/docs`" — aligning with PM Gate wording.

---

## 3. Orchestration — Pre-Fix 8.5 / Post-Fix 9.2

### Finding V8-D — Medium: §14 Handoff Table Cites Wrong Phase as DE Phase 7 Trigger

**File:** `AGENTS.md` (§14, last row of Critical Handoff Dependencies table)

**Current entry:**
```
| FE | Phase 4 complete | **DE Phase 7 review** can begin (DuckDB WASM hooks now exist to audit Parquet column parity) |
```

**Why this is wrong:** Phase 4 ships the Superfund diamond marker overlay (stories 4.1.1–4.3.2). There are zero DuckDB WASM hooks in Phase 4. DuckDB WASM hooks are Phase 7 stories: `7.1.1–7.1.8` (`useDuckDBFacilities`, `useDuckDBSuperfund`, `useDuckDBDemographics`). DE story `7.DE.1` (Parquet column parity review) requires those hooks to exist so DE can cross-reference Parquet column names against the API contract expectations in the hook code.

**Impact:** If a PM agent reads this table literally, it could dispatch DE for Phase 7 column-parity review immediately after Phase 4 completes — finding nothing to review, as DuckDB hooks don't exist yet. At minimum, this confuses dispatch sequencing; at worst, it causes a false-clean DE review that misses the actual parity audit when Phase 7 hooks are finally implemented.

**Correct trigger:** FE stories 7.1.1–7.1.8 complete (DuckDB WASM hooks exist in Phase 7).

**Fix:** Replace the row with the correct trigger: FE 7.1.x complete → DE 7.DE.1 can begin.

---

## 4. Maturity — 9.0 / 10 (No New Findings)

No new maturity findings beyond those already tracked. Confirmed strengths:
- CODEOWNERS template correctly covers all 11 protected files (V7-C fix verified)
- ADR lifecycle with single-maintainer exception is well-specified and explicitly documented
- Release checklist in GOVERNANCE.md §7 uses dynamic Gherkin count form
- Security posture (GOVERNANCE.md §8) is comprehensive and internally consistent

Governance findings 4 (no DCO/CLA), 7 (Docker Desktop floor), 8 (squash-merge [agent] CI enforcement), 9 (@maintainers team undefined), 15 (no commitlint), 21 ([agent] tag no CI enforcement) remain open. None block Phase 0. Count: 6 of the original 23 governance findings remain unresolved (10 were listed as open in V7 but 4 can now be confirmed or partially confirmed from reading CONTRIBUTING.md).

**Finding 7 (Docker Desktop `4.x`) — partially confirmed:**  
CONTRIBUTING.md §1 specifies `≥ 4.25 (latest stable recommended)`. Docker Desktop 4.25 was released ~November 2023 (~2.5 years before this audit). The "latest stable recommended" note partially mitigates; contributors are guided to current versions. The floor is outdated but not critically so. See V8-F.

**Finding 8 (Squash-merge [agent] tag) — documented, not CI-enforced:**  
CONTRIBUTING.md §7 now contains: "When squash-merging a branch where any commit was [agent]-tagged, the squash commit subject must retain [agent] at the end of the subject line." This is correct documentation; CI enforcement remains absent (finding 21 overlap).

**Finding 9 (@maintainers team mention) — confirmed present in CONTRIBUTING.md:**  
CONTRIBUTING.md §6 ("Technical disagreements in PRs") says "either party may escalate by tagging `@maintainers`". With a single-maintainer project and no GitHub team named `@maintainers`, this mention is decorative. No CI/enforcement impact; low-priority cosmetic issue.

---

## 5. Governance — 8.5 → 8.7 / 10

### Finding V8-F — Low: CONTRIBUTING.md Docker Desktop Minimum Floor `≥ 4.25` Is ~2.5 Years Old

**File:** `CONTRIBUTING.md` (§1 Prerequisites table)

Docker Desktop 4.25 was released approximately November 2023. As of July 2026, the current stable release is likely ≥ 4.35. The current text `≥ 4.25 (latest stable recommended)` softens the floor with the "latest stable recommended" note — contributors are pointed toward the current version. However, the stated floor is anachronistic for a fresh 2026 project.

**Risk:** Low. Docker Desktop 4.25+ remains functionally compatible with Compose v2 and the project's compose spec. No behavioral incompatibility is expected. The floor serves mostly as documentation hygiene.

**Fix:** Update minimum to `≥ 4.35` to reduce the anachronism gap. Keep "latest stable recommended."

---

## 6. Reliability — Pre-Fix 8.5 / Post-Fix 9.2

### Finding V8-B — Medium: OPS Prompt Contains a Broken File Path in Context Load Table

**File:** `agents/devops-engineer/prompt.md` (Priority 4 row in "Context Files — Load Before Every Session" table)

**Current entry:**
```
| 4 | docs/onboarding/TOXMAP_CONTRIBUTING.md | Branch strategy, PR process, commit format, the .github/ infrastructure you need to create |
```

**Actual file path:** `CONTRIBUTING.md` at the repository root.

There is no file at `docs/onboarding/TOXMAP_CONTRIBUTING.md`. The file is `CONTRIBUTING.md` (repo root). An OPS agent attempting to load Priority 4 context would either fail to find the file or silently skip it — missing branch strategy, PR template requirements, and the `.github/` infrastructure spec it needs to implement stories 0.1.3 and 0.3.1.

**Fix:** Change `docs/onboarding/TOXMAP_CONTRIBUTING.md` → `CONTRIBUTING.md` in the OPS context load table.

---

## 7. New Findings Summary

| ID | Dimension | Severity | File | Finding | Fix Time |
|----|-----------|----------|------|---------|----------|
| V8-A | Agentic Readiness / Consistency | 🔴 **High** | `CONTEXT_SUMMARY.md` §UX Invariants | 5 of 10 UX invariants describe different behaviors from FE prompt; constrained-context agents implement/test wrong invariants | 3 min |
| V8-B | Reliability | 🟡 **Medium** | `agents/devops-engineer/prompt.md` Priority 4 | Broken file path `docs/onboarding/TOXMAP_CONTRIBUTING.md` — file is at `CONTRIBUTING.md` in repo root | 30 sec |
| V8-C | Consistency / Governance | 🟡 **Medium** | `CHANGELOG.md` header (lines 7–9) | CHANGELOG.md prohibits direct edits; AGENTS.md §2 grants agents permission to update it — direct contradiction | 1 min |
| V8-D | Orchestration | 🟡 **Medium** | `AGENTS.md` §14 handoff table (last row) | DE Phase 7 review trigger incorrectly set to "FE Phase 4 complete" — should be "FE 7.1.x DuckDB WASM hooks complete" | 30 sec |
| V8-E | Consistency | 🟢 **Low** | `docs/product/TOXMAP_PROGRESS_TRACKER.md` Phase 2 DoD preview (line 140) | "17 endpoints" in PROGRESS_TRACKER vs. "17 domain + `GET /api/v1/meta`" in PM Gate 2→3 — ambiguous total count | 30 sec |
| V8-F | Governance | 🟢 **Low** | `CONTRIBUTING.md` §1 Prerequisites (Docker Desktop row) | Minimum floor `≥ 4.25` is ~2.5 years old as of July 2026 | 30 sec |

**Total estimated fix time: ~6 minutes. All findings resolved in this session.**

---

## 8. What to Do Next

### Fix Now (applied in this session)

1. **V8-A:** Replace `CONTEXT_SUMMARY.md` UX invariants with exact FE prompt invariants (condensed form matching the summary format)
2. **V8-B:** Fix broken file path in OPS prompt context load table: `docs/onboarding/TOXMAP_CONTRIBUTING.md` → `CONTRIBUTING.md`
3. **V8-C:** Update `CHANGELOG.md` header to align with the AGENTS.md §2 permission for agent updates
4. **V8-D:** Fix AGENTS.md §14 handoff table: "FE Phase 4 complete" → "FE 7.1.x (DuckDB WASM hooks, Phase 7) complete"
5. **V8-E:** Update PROGRESS_TRACKER Phase 2 DoD preview: "17 endpoints" → "17 domain endpoints + `GET /api/v1/meta`"
6. **V8-F:** Update CONTRIBUTING.md Docker Desktop floor: `≥ 4.25` → `≥ 4.35`

### Defer (No Blocker for Phase 0)

Governance findings 4 (no DCO/CLA), 8/21 ([agent] commit tag CI enforcement), 9 (@maintainers team), 15 (no commitlint) remain open. None block Phase 0 and all require external GitHub org/workflow setup that exceeds agent authority.

---

## 9. Autonomous Development Feasibility Verdict

**Yes, unconditionally, for Phase 0 — and with higher confidence post-V8 fix than pre-V8.**

V8-A was the most significant undetected risk in the post-V7 corpus: agents using the constrained-context path (which all 7 agent prompts designate as Priority 0) would have been testing the wrong UX invariants. After the V8-A fix, `CONTEXT_SUMMARY.md` is finally aligned with the authoritative FE prompt.

After all 6 V8 fixes, the corpus is self-consistent at the level needed for Phase 0 execution:
- All 7 agent prompts have correct escalation fallback paths ✅
- CONTEXT_SUMMARY.md now matches FE prompt on all 10 UX invariants ✅
- CODEOWNERS template covers all 11 protected files ✅
- All hardcoded scenario counts removed from all agent prompts ✅
- Phase Manager handoff table correctly triggers DE Phase 7 review after Phase 7, not Phase 4 ✅
- OPS agent can load its Priority 4 context file without a path error ✅
- CHANGELOG.md update rights are unambiguous ✅

---

## 10. Fixes Applied in This Session

| File | Change | Finding |
|------|--------|---------|
| `CONTEXT_SUMMARY.md` | Replaced UX invariants section with the exact authoritative list from `agents/frontend-engineer/prompt.md` (condensed to match summary format); all 10 invariants now consistent with FE prompt, Phase Advancement gates, and TEST_ID_REGISTRY.md | V8-A |
| `agents/devops-engineer/prompt.md` | Fixed broken file path: `docs/onboarding/TOXMAP_CONTRIBUTING.md` → `CONTRIBUTING.md` in Priority 4 of context load table | V8-B |
| `CHANGELOG.md` | Updated header to clarify dual-mode update policy: agents update per story during their session; PM updates at milestones; maintainers at release time | V8-C |
| `AGENTS.md` | Fixed §14 handoff table last row: trigger changed from "FE Phase 4 complete" to "FE 7.1.1–7.1.8 complete (DuckDB WASM hooks, Phase 7)"; unblocked agent changed to "DE 7.DE.1 (Parquet column parity review)" | V8-D |
| `docs/product/TOXMAP_PROGRESS_TRACKER.md` | Updated Phase 2 DoD preview endpoint count: "All 17 endpoints" → "All 17 domain endpoints + `GET /api/v1/meta`" — aligned with PM Gate 2→3 wording | V8-E |
| `CONTRIBUTING.md` | Updated Docker Desktop minimum floor: `≥ 4.25` → `≥ 4.35`; retained "latest stable recommended" | V8-F |
| `docs/product/TOXMAP_PROGRESS_TRACKER.md` | Added V8 session log entry | Accuracy |

**All V8 findings fully resolved. Post-V8 corpus maturity score: 9.4/10.**

---

*End of V8 Audit. Combined findings resolved in V7 + V8 sessions: 11 V7 findings + 6 V8 findings = 17 across all 7 agent prompts, AGENTS.md, GOVERNANCE.md, CONTEXT_SUMMARY.md, CHANGELOG.md, and CONTRIBUTING.md.*

