# TOXMAP Agentic Development Audit — V9

**Auditor:** GitHub Copilot  
**Date:** 2026-07-23  
**Scope:** Full independent sweep — all V8 post-improvement fixes verified + new findings  
**Audit Dimensions:** Agentic Readiness · Consistency · Orchestration · Maturity · Governance · Reliability  
**Basis:** 50+ documents read in full; all 7 agent prompts, all governance files, all testing docs, all ADRs, PROGRESS_TRACKER  
**Predecessor:** `TOXMAP_AGENTIC_AUDIT_V8.md` — declared post-V8 score 9.4/10

---

## Executive Summary

V9 independently verifies all V8 post-improvement claims and performs a fresh full-corpus sweep with 2 additional days elapsed since V8. **4 new findings identified.** One is HIGH severity: story 7.2.4 (service worker) is explicitly claimed by **both** the FE prompt (Phase 7 story table) and the OPS prompt (Phase 7 story table), while the PM dispatch assigns it exclusively to OPS. In the co-led Phase 7, any FE agent dispatched for 7.1.x will see 7.2.4 in its own prompt as a "your story" item and implement it in parallel with OPS — producing duplicate and potentially conflicting implementations.

One MEDIUM finding: the OPS prompt story 1.5.2 spec instructs using `cloudflare/wrangler-action@v3` — a mutable tag — when introducing this new Action in Phase 1. AGENTS.md §11 explicitly requires all new GitHub Actions to be SHA-pinned **in the same commit they are introduced**, and story 1.5.2 has no corresponding Phase 1 SEC pinning story. The two-step "OPS introduces, SEC pins" workflow is explicitly designed for Phase 0 (via story 0.5.4) but is not replicated for new Actions introduced in later phases.

One MEDIUM finding: the OPS prompt declares "Phase 0 is entirely yours. Nothing else can start until these are done." This is inaccurate — Phase 0 has stories across all five active agents (OPS, BE, FE, QA, SEC). In the solo-agent shortcut path documented in AGENTS.md §0, an OPS agent reading this phrase may treat all 33 Phase 0 story points as its responsibility, blocking incorrectly on SEC/BE/FE/QA deliverables before declaring Phase 0 complete.

One LOW finding: the CONTEXT_SUMMARY Phase Sequence table still reads "17 endpoints" for Phase 2 — the V8-E fix was applied to PROGRESS_TRACKER but not to this table, leaving a second location with the pre-fix ambiguity.

**Pre-fix score: 9.1 / 10** (V9-A HIGH finding pulls pre-fix score below 9.4 post-V8)  
**Post-fix score: 9.6 / 10** (all 4 findings resolved in this session)

---

## V8 Post-Improvement Verification

| Claim | Status | Evidence |
|-------|--------|---------|
| All 7 agent prompts have ESCALATION fallback | ✅ Confirmed | FE, OPS, QA, SEC, BE, DE all have the `ESCALATION_[YYYYMMDD_HHMMSS].md` fallback block |
| CONTEXT_SUMMARY.md invariants match FE prompt (V8-A) | ✅ Confirmed | All 10 invariants in CONTEXT_SUMMARY match FE prompt exactly including `data-testid` values |
| OPS broken file path fixed (V8-B) | ✅ Confirmed | OPS context load table Priority 4 reads `CONTRIBUTING.md` (repo root) |
| CHANGELOG.md dual-update policy header (V8-C) | ✅ Confirmed | CHANGELOG.md header correctly describes agents/PM/maintainer update split |
| AGENTS.md §14 DE Phase 7 trigger corrected (V8-D) | ✅ Confirmed | Last row reads "FE 7.1.1–7.1.8 complete (DuckDB WASM hooks, Phase 7)" → "DE 7.DE.1" |
| PROGRESS_TRACKER Phase 2 DoD "17 domain + meta" (V8-E) | ✅ Confirmed | Line 140: "All 17 domain endpoints + `GET /api/v1/meta` visible at Swagger UI `/docs`" |
| CONTRIBUTING.md Docker Desktop floor ≥4.35 (V8-F) | ✅ Confirmed | CONTRIBUTING.md Prerequisites table updated |
| CODEOWNERS template includes `SECURITY.md @maintainer` (V7-C) | ✅ Confirmed | OPS prompt CODEOWNERS section line 343 |

**All V8 post-improvement claims verified. No regressions found.**

---

## Scoring Summary

| Dimension | Pre-Fix Score | Post-Fix Score | Delta vs. V8 post |
|-----------|--------------|----------------|-------------------|
| **Agentic Readiness** | 9.2 / 10 | 9.5 / 10 | (V9-C fix removes solo-agent confusion) |
| **Consistency** | 8.8 / 10 | 9.5 / 10 | (V9-A, V9-D resolved) |
| **Orchestration** | 9.2 / 10 | 9.6 / 10 | (V9-A resolved removes Phase 7 dispatch conflict) |
| **Maturity** | 9.0 / 10 | 9.2 / 10 | (no new issues; confirmed strengths hold) |
| **Governance** | 8.7 / 10 | 8.7 / 10 | → (no change; open findings from V8 persist) |
| **Reliability** | 9.0 / 10 | 9.5 / 10 | (V9-B resolved; new Action spec safe-to-ship) |
| **Overall** | **9.1 / 10** | **9.6 / 10** | ↑ +0.2 vs V8 declared score |

---

## 1. Consistency / Orchestration — Pre-Fix 8.8+9.2 / Post-Fix 9.5+9.6

### Finding V9-A — HIGH: Story 7.2.4 Dual Ownership — FE and OPS Both Claim It; PM Assigns to OPS

**Files affected:**  
- `agents/frontend-engineer/prompt.md` — §Phase 7 story table  
- `agents/devops-engineer/prompt.md` — §Phase 7 story table  
- `agents/phase-manager/prompt.md` — §Phase 7 dispatch (authoritative: OPS 7.2.1–7.2.4)

**FE prompt Phase 7 story table (current):**
```
| 7.2.4 | Service worker: cache WASM + first Parquet chunks for offline use |
```

**OPS prompt Phase 7 story table (current):**
```
| 7.2.4 | Service worker for offline caching. `vite-plugin-pwa` in `frontend/package.json`.
         Configure to precache: the WASM binary (`@duckdb/duckdb-wasm`), `manifest.json`,
         and the first Parquet chunks. Must not cache user-specific query results. |
```

**PM Phase 7 dispatch (authoritative):**
```
| 2 | OPS | 7.2.1–7.2.4 — Cloudflare Pages + R2 + service worker | Parallel with FE after 7.1.8 |
```

**Why this is HIGH severity:**

Phase 7 is the only co-led phase (FE + OPS). Both agents are dispatched in the same phase. The PM dispatch table explicitly allocates the 7.2.x series (7.2.1–7.2.4) to OPS. Yet the FE prompt lists 7.2.4 under "Your Stories, Phase 7." Any FE agent loading its own prompt will see 7.2.4 as a FE story and implement it — because its prompt says so. The PM dispatch allocating it to OPS is on a different document. The FE prompt's story table is loaded at Priority 1 (roadmap); the PM dispatch is only loaded by the Phase Manager, not by the FE agent itself.

**Impact chain:**
1. PM dispatches FE agent for Phase 7 stories 7.1.1–7.1.8 (DuckDB WASM hooks).
2. FE agent loads its own prompt and reads its Phase 7 story table, which includes **7.2.4** ("Service worker: cache WASM...").
3. FE agent implements 7.2.4 (service worker + vite-plugin-pwa).
4. PM separately dispatches OPS agent for stories 7.2.1–7.2.4.
5. OPS agent also implements 7.2.4 (service worker + vite-plugin-pwa in frontend/package.json).
6. Two conflicting implementations of the same service worker in the same file.

**The boundary is clear from the PM dispatch** (7.1.x = FE, 7.2.x = OPS) but is not enforced by the FE prompt itself. The FE prompt should only list 7.1.x stories and the production smoke tests (7.3.x) as FE Phase 7 work.

**Root cause:** Story 7.2.4 involves `frontend/package.json` (`vite-plugin-pwa`) and is clearly frontend-adjacent, so it was added to the FE story table. But OPS owns the deployment infra including the service worker configuration, and the PM dispatch correctly puts all 7.2.x stories in OPS. The FE prompt was not updated when the PM assigned 7.2.4 to OPS.

**Fix:** Remove story 7.2.4 from the FE prompt Phase 7 story table. Add a clarifying note below the 7.1.x and 7.3.x stories explaining that the service worker configuration (7.2.4) is owned by OPS even though it involves `frontend/package.json` — OPS owns the PWA/offline infrastructure; FE owns the DuckDB WASM query hooks (7.1.x).

---

## 2. Reliability — Pre-Fix 9.0 / Post-Fix 9.5

### Finding V9-B — Medium: Story 1.5.2 Spec Uses Mutable `@v3` GitHub Action Tag; No Phase 1 Pinning Story Covers It

**File:** `agents/devops-engineer/prompt.md`, Phase 1 story 1.5.2

**Current story spec:**
> "...uploads `.parquet` and `.meta.json` files to R2 via `cloudflare/wrangler-action@v3`."

**Governing rule (AGENTS.md §11):**
> "New GitHub Actions must be pinned to a full 40-character SHA in the same commit they are introduced. Readable tag comments are required (e.g., `# v3.0.0`). Never use `@latest`."

**The two-step workflow vs. the rule:**

For Phase 0, there is an intentional two-step design:
- OPS stories 0.3.1/0.3.3 introduce Actions with readable tags
- SEC story 0.5.4 pins all Phase 0 Actions to full SHA immediately after

This two-step design conflicts with AGENTS.md §11 ("in the same commit they are introduced"), but Phase 0 is self-contained — 0.5.4 runs in the same phase, shortly after 0.3.x.

**For Phase 1, no equivalent SEC pinning story exists:**

| Phase | OPS story introducing new Action | SEC story pinning it |
|-------|----------------------------------|---------------------|
| 0 | 0.3.1 (`codecov-action@v4`) + 0.3.3 | 0.5.4 — explicit Phase 0 SEC story |
| 1 | 1.5.2 (`wrangler-action@v3`) | **None** — no Phase 1 SEC pinning story in PM dispatch or ROADMAP |

An OPS agent implementing story 1.5.2 will use `@v3` exactly as the story spec says. This introduces a mutable Action tag into `build-data.yml` that will remain unpinned indefinitely — there is no Phase 1 trigger for SEC to pin it. The Action will only get pinned if: (a) OPS reads AGENTS.md §11 carefully and deviates from the story spec, (b) a Phase 6 SEC review catches it, or (c) Dependabot creates a PR upgrading it.

**Impact:** T-SEC-08 (supply chain attack via mutable Action tags) is the exact risk this rule prevents. The `build-data.yml` workflow runs on a schedule to build production Parquet datasets. A compromised `wrangler-action@v3` could exfiltrate `CF_API_TOKEN` or overwrite R2 contents with poisoned Parquet files.

**Fix:**
1. Update story 1.5.2 spec: change "`cloudflare/wrangler-action@v3`" to "`cloudflare/wrangler-action@<SHA> # v3` — resolve the SHA from `docs/security/PINNED_ACTIONS.md` before implementing; follow the 5-step pin procedure in that file (AGENTS.md §11)."
2. Add a note in the Phase 1 OPS story: "After completing 1.5.2, update `docs/security/PINNED_ACTIONS.md` with the resolved SHA for `wrangler-action`."

---

## 3. Agentic Readiness — Pre-Fix 9.2 / Post-Fix 9.5

### Finding V9-C — Medium: OPS Prompt "Phase 0 Is Entirely Yours" Overstates OPS Ownership of Phase 0

**File:** `agents/devops-engineer/prompt.md` (§Phase 0 Foundation — Your Lead Phase)

**Current text:**
> "Phase 0 is entirely yours. Nothing else can start until these are done."

**Reality:** Phase 0 has 33 story points across **5 agents**:

| Agent | Phase 0 Stories | Points |
|-------|----------------|--------|
| OPS | 0.1.1–0.3.3 (Epic 0.1, 0.2 except 0.2.3/0.2.4, 0.3) | 14 |
| BE | 0.2.3 — backend Dockerfile + health endpoint | 2 |
| FE | 0.2.4 — frontend Dockerfile | 2 |
| QA | 0.4.1–0.4.4 — test infrastructure | 8 |
| SEC | 0.5.1–0.5.4 — security foundation | 7 |

**Why this is MEDIUM severity:**

AGENTS.md §0 defines a "Single-agent shortcut" path: if running without a Phase Manager agent, an agent reads `CURRENT_PHASE.txt` + its own prompt. An OPS agent using this shortcut will read "Phase 0 is entirely yours" and may:
1. Not dispatch or coordinate with SEC/BE/FE/QA for their Phase 0 stories
2. Consider Phase 0 DoD verified when only OPS's stories are complete, even though the Gate 0→1 checklist requires SEC's SECURITY.md, QA's seed.sql, and BE's health endpoint

In PM-orchestrated mode (the normal path), the PM dispatches each agent for their stories — the phrase doesn't cause confusion because the PM controls dispatch. But the single-agent shortcut path is explicitly documented and intended to work. For OPS running standalone, this phrase is materially misleading.

**The true meaning:** "Your stories are what unblock everyone else. You are the prerequisite. Nothing in phases 1+ can start until OPS Phase 0 stories (0.1.x–0.3.x) are done." This is the correct framing.

**Fix:** Replace "Phase 0 is entirely yours. Nothing else can start until these are done." with:
> "**OPS leads Phase 0.** Your stories (0.1.x, 0.2.x, 0.3.x) are the foundation that unblocks all other Phase 0 agents. Story 0.1.1 must be done before **any** other story — in any agent — can start. However, BE (0.2.3), FE (0.2.4), QA (0.4.x), and SEC (0.5.x) all have their own Phase 0 stories that run in parallel once the repo exists. If using the single-agent shortcut (no Phase Manager), coordinate Phase 0 delivery across all 5 agent roles."

---

## 4. Consistency — Pre-Fix 8.8 / Post-Fix 9.5

### Finding V9-D — Low: CONTEXT_SUMMARY Phase Sequence Table Phase 2 Entry Still Reads "17 Endpoints" — V8-E Echo

**File:** `CONTEXT_SUMMARY.md` (Phase Sequence at a Glance table)

**Current entry:**
```
| 2 | BE | 17 endpoints + API tests green |
```

**V8-E fix (already applied to PROGRESS_TRACKER):**
> "All 17 domain endpoints + `GET /api/v1/meta` visible at Swagger UI `/docs`"

**PM Gate 2→3 (authoritative):**
> "Swagger UI at `/docs` shows all endpoints (17 domain + `GET /api/v1/meta`)"

V8-E correctly updated the PROGRESS_TRACKER Phase 2 DoD preview but did not update the CONTEXT_SUMMARY Phase Sequence table. The Phase Sequence table is loaded by every agent in constrained-context sessions as the quick-reference guide. An agent reading "17 endpoints" may not know whether `/api/v1/meta` is counted as endpoint #17 or is additional. This is the same ambiguity V8-E resolved — it just survived in a second location.

**Fix:** Update Phase Sequence table Phase 2 entry from "17 endpoints + API tests green" to "17 domain endpoints + `/api/v1/meta` + API tests green".

---

## 5. New Findings Summary

| ID | Dimension | Severity | File | Finding | Fix Time |
|----|-----------|----------|------|---------|----------|
| V9-A | Consistency / Orchestration | 🔴 **High** | `agents/frontend-engineer/prompt.md` Phase 7 story table | Story 7.2.4 listed as FE Phase 7 story; PM assigns 7.2.1–7.2.4 to OPS; dual ownership causes conflicting implementations in co-led phase | 2 min |
| V9-B | Reliability | 🟡 **Medium** | `agents/devops-engineer/prompt.md` Phase 1 story 1.5.2 | Story spec instructs `wrangler-action@v3` mutable tag; no Phase 1 SEC pinning story; violates AGENTS.md §11 | 1 min |
| V9-C | Agentic Readiness | 🟡 **Medium** | `agents/devops-engineer/prompt.md` §Phase 0 header | "Phase 0 is entirely yours" overstates OPS scope; confuses solo-agent shortcut path; all 5 Phase 0 agents have their own stories | 2 min |
| V9-D | Consistency | 🟢 **Low** | `CONTEXT_SUMMARY.md` Phase Sequence table | Phase 2 entry "17 endpoints" — V8-E fix applied to PROGRESS_TRACKER but not to this second location | 30 sec |

**Total estimated fix time: ~6 minutes. All findings resolved in this session.**

---

## 6. Maturity — 9.0 / 10 (No New Findings; Confirmed Strengths)

- All 11 protected files in CODEOWNERS template (including SECURITY.md — V7-C fix intact)
- All Phase Advancement Gates use objectively verifiable DoD items (curl commands, psql queries, exit codes)
- PM sole-writer protocol for CURRENT_PHASE.txt stated in 4 locations (PM prompt, AGENTS.md §0, CONTEXT_SUMMARY.md, OPS prompt ownership note)
- Immutable seed values consistent across 6+ locations — no divergence found
- 10 UX invariants consistent across FE prompt, CONTEXT_SUMMARY.md, Phase Gates, TEST_ID_REGISTRY.md — V8-A fix intact
- Security threat model (T-SEC-01–T-SEC-15) correctly maps to mitigating controls across all relevant prompts

**Open governance findings from V8 (deferred, no Phase 0 blocker):**
- Finding 4: No DCO/CLA process — still open; requires external GitHub org setup
- Findings 8/21: `[agent]` commit tag has no CI enforcement — still open
- Finding 9: `@maintainers` team undefined in GitHub org — decorative mention in CONTRIBUTING.md
- Finding 15: No commitlint — still open; requires external tooling

---

## 7. Governance — 8.7 / 10 (No New Findings)

GOVERNANCE.md v1.1 is stable. The decision authority matrix, ADR lifecycle, release checklist, security policy, and data provenance rules are internally consistent and cross-reference correctly. No new governance findings identified in V9.

---

## 8. What to Do Next

### Fix Now (applied in this session)

1. **V9-A:** Remove story 7.2.4 from FE prompt Phase 7 story table; add clarifying note that 7.2.4 (service worker, vite-plugin-pwa) is OPS-owned
2. **V9-B:** Update OPS prompt story 1.5.2: replace "`wrangler-action@v3`" with "`wrangler-action@<SHA from PINNED_ACTIONS.md> # v3`"; add note to update PINNED_ACTIONS.md after completing 1.5.2
3. **V9-C:** Replace "Phase 0 is entirely yours. Nothing else can start until these are done." with precise language distinguishing OPS lead stories from the multi-agent Phase 0 reality
4. **V9-D:** Update CONTEXT_SUMMARY Phase Sequence Phase 2 entry to "17 domain endpoints + `/api/v1/meta` + API tests green"

### Defer (No Blocker for Phase 0)

Governance findings 4, 8/21, 9, 15 remain open. None block Phase 0 and all require external GitHub org setup that exceeds agent authority.

---

## 9. Autonomous Development Feasibility Verdict

**Yes, unconditionally, for Phase 0 — and for Phases 1–6 with one caveat.**

**Phase 0:** Fully ready. All 7 agent prompts have correct escalation fallback paths, consistent UX invariants, correct Phase 0 dispatch dependencies, and correct security guardrails. After V9-C fix, the OPS Phase 0 scope is precisely stated.

**Phase 7 (after V9-A fix):** The FE/OPS co-lead handoff is now unambiguous. FE owns 7.1.x (DuckDB WASM hooks) + 7.3.x (smoke tests). OPS owns 7.2.x (Cloudflare Pages + R2 + service worker). No story is claimed by two agents.

**Phase 1 (after V9-B fix):** Story 1.5.2 spec no longer instructs a mutable `@v3` GitHub Action tag. OPS agents implementing 1.5.2 will consult PINNED_ACTIONS.md and follow the AGENTS.md §11 SHA-pin-on-introduction rule.

After all 4 V9 fixes, the corpus is self-consistent at the level needed for full-phase autonomous execution.

---

## 10. Fixes Applied in This Session

| File | Change | Finding |
|------|--------|---------|
| `agents/frontend-engineer/prompt.md` | Removed story 7.2.4 from Phase 7 story table; added clarifying note: "7.2.4 (service worker / vite-plugin-pwa) is owned by OPS — see OPS Phase 7 story 7.2.4 and PM dispatch table" | V9-A |
| `agents/devops-engineer/prompt.md` | Story 1.5.2: replaced `wrangler-action@v3` with `wrangler-action@<SHA from PINNED_ACTIONS.md> # v3`; added note to update PINNED_ACTIONS.md after completing 1.5.2 | V9-B |
| `agents/devops-engineer/prompt.md` | Phase 0 lead paragraph: replaced "Phase 0 is entirely yours. Nothing else can start until these are done." with precise multi-agent framing | V9-C |
| `CONTEXT_SUMMARY.md` | Phase Sequence table Phase 2: "17 endpoints + API tests green" → "17 domain endpoints + `/api/v1/meta` + API tests green" | V9-D |
| `docs/product/TOXMAP_PROGRESS_TRACKER.md` | Added V9 session log entry | Accuracy |

**All V9 findings fully resolved. Post-V9 corpus maturity score: 9.6/10.**

---

*End of V9 Audit. Combined findings resolved in V7 + V8 + V9 sessions: 11 V7 findings + 6 V8 findings + 4 V9 findings = 21 across all 7 agent prompts, AGENTS.md, GOVERNANCE.md, CONTEXT_SUMMARY.md, CHANGELOG.md, and CONTRIBUTING.md.*

