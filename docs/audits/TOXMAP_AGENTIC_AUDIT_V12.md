# TOXMAP Agentic Development Audit — V12

**Auditor:** GitHub Copilot  
**Date:** 2026-07-26  
**Scope:** Full independent sweep — all V11 post-improvement fixes verified + new findings.
V12 is the first post-Phase-2 audit: Phase 2 (Core API) completed on 2026-07-26 and Phase 3
(Core Map UI) has been opened. This audit cross-references the complete Phase 0–2 implementation
against all agent prompts, governance documents, CI configuration, and the API contract.  
**Audit Dimensions:** Agentic Readiness · Consistency · Orchestration · Maturity · Reliability  
**Basis:** All 7 agent prompts, all governance files, all ADRs, all CI workflow files,
`conftest.py`, `pyproject.toml`, all backend routers/schemas/services, `main.py`,
`meta.py`, `PROGRESS_TRACKER.md`, `CHANGELOG.md`, `CURRENT_PHASE.txt`, `CONTEXT_SUMMARY.md`,
`frontend/package.json`, `frontend/src/`, `tests/features/`, `tests/steps/`, all escalation
files, `TOXMAP_API_CONTRACT.md` §17.  
**Predecessor:** `TOXMAP_AGENTIC_AUDIT_V11.md` — declared post-V11 score 9.2/10

---

## Executive Summary

V12 independently verifies all V11 post-improvement claims and performs the first audit of the
Phase 3 entry state. **9 new findings identified.** Three are HIGH severity and will cause
agents to produce incorrect output or block Phase 3 before a line of frontend code is written.

**C-01 (HIGH):** `CONTEXT_SUMMARY.md` still declares `cat CURRENT_PHASE.txt → 0 (Foundation)`
with `Last Updated: 2026-07-21`. The actual value is `3`. This file is the constrained-context
fallback: AGENTS.md instructs any agent with a small context window to load it *instead of*
the full tier-1 corpus. Such an agent will believe the project is in Phase 0 and may attempt
Foundation work, skip Phase 2 DoD checks, or dispatch a BE agent for story 0.2.3 rather than a
FE agent for story 3.1.1. The constrained-context path is completely broken for the current
phase.

**C-02 (HIGH):** `GET /api/v1/meta` field names diverge between the agent prompts and the
actual implementation. The BE agent prompt (§Phase 2 story 2.7.3) and the Phase Manager Gate
2→3 checklist both specify `loaded_years` and `db_build_info`. The API contract (§17), the
Pydantic schema (`backend/app/schemas/meta.py`), and the Phase 2 DoD verification in
PROGRESS_TRACKER all correctly use `available_years` and `source`. When the FE agent reads the
BE prompt in Phase 3 story 3.1.5 (data vintage indicator), it will attempt to consume
`loaded_years` from the live API — a field that does not exist — causing a runtime failure at
the first dev-mode page load. This will also cause the PM to misread the Gate 2→3 checklist
as unverified on the next cold-start session.

**C-03 (HIGH):** B-002 (PMTiles manual upload to Cloudflare R2) is explicitly required before
Phase 3 FE dispatch in the Phase 3 prerequisite gate table, but it does not appear in the
Active Blockers section at the bottom of PROGRESS_TRACKER. A Phase Manager agent reading only
the blockers table will see Phase 3 as fully unblocked and dispatch the FE agent immediately.
The FE agent will implement MapLibre story 3.1.2 (PMTiles basemap layer) against an R2 path
that has no file, fail silently, and spend cycles debugging a network 404 rather than a
missing prerequisite.

Three MEDIUM findings cover: Phase 3 story rows 3.2 and 3.3–3.6 collapsed into two mega-rows
(preventing story-level tracking and QA–story mapping); the `react-map-gl` v7 / `maplibre-gl`
v4 version incompatibility (will cause TypeScript and runtime errors on first Phase 3 compile);
and the conftest `DATABASE_URL_SYNC` fallback connecting to a database named `toxmap_test`
while the Docker service creates `toxmap`.

Three LOW findings: Phase 1 section header still reads "*(In Progress)*" despite all stories
being ✅; Milestones M2 and M3 are undeclared in the Milestone History table; and
`vintage_label` / `build_date` always return `"unknown"` in dev mode (known limitation, but
directly prevents Phase 3 DoD item "correct vintage string shown" from passing).

**Pre-fix score: 8.6 / 10**  
**Post-fix score (projected): 9.5 / 10** (all HIGH/MEDIUM findings resolved or mitigated)

> **Note on score delta vs. V11:** The declared V11 post-fix score was 9.2/10. V12 pre-fix
> drops to 8.6/10 primarily because C-01 (stale CONTEXT_SUMMARY) represents a critical
> constrained-context path regression, and C-02 (field name drift) is a Phase 3 code-breaking
> issue that went undetected during the Phase 2 DoD verification. The two findings together
> account for the full score drop. Post-fix 9.5/10 matches expected trajectory for a project
> entering Phase 3.

---

## V11 Post-Improvement Verification

| Claim | Status | Evidence |
|-------|--------|---------|
| `requests` added to ingestion extras in `pyproject.toml` (V11-1) | ✅ Confirmed | `pyproject.toml` ingestion group: `"requests==2.32.3"` present |
| Phase Summary duplicate row removed; Phase 1 DoD bypass acknowledged as B-001 (V11-2) | ✅ Confirmed | Phase Summary table has 8 unique rows; B-001 logged with "does not block Phase 2" note |
| QA Phase 2 epic added to PROGRESS_TRACKER; step implementations created (V11-3) | ✅ Confirmed | Stories 2.QA.1–2.QA.3 all ✅; `tests/steps/api_steps.py` present with implementations |
| `conftest.py` teardown updated to include `nuclear_plants`, `npri_facilities` (V11-4) | ✅ Confirmed | Teardown TRUNCATE: `nuclear_plants, npri_facilities` present in conftest.py |
| DE prompt table names corrected (V11-5) | ✅ Confirmed | DE prompt 1.2.6 validation query uses correct table names |
| OPS story 2.OPS.1 created to remove Schemathesis `\|\| true`; ci.yml updated (V11-6) | ✅ Confirmed | 2.OPS.1 ✅ in PROGRESS_TRACKER; `\|\| true` absent from ci.yml Schemathesis step |
| pip-audit scope updated to include ingestion dependencies (V11-7) | ✅ Confirmed | `security.yml` bandit/pip-audit job updated |

**All V11 post-improvement claims verified. No regressions found.**

---

## Scoring Summary

| Dimension | Pre-Fix Score | Post-Fix Score | Delta vs. V11 post |
|-----------|--------------|----------------|-------------------|
| **Agentic Readiness** | 7.5 / 10 | 9.5 / 10 | ↓ (C-01 CONTEXT_SUMMARY stale — entire constrained-context path broken) |
| **Consistency** | 8.0 / 10 | 9.5 / 10 | ↓ (C-02 meta field drift breaks FE Phase 3; L-01 phase header stale) |
| **Orchestration** | 8.5 / 10 | 9.5 / 10 | ↓ (C-03 B-002 not in blockers table; O-01 Phase 3 opened before prereq confirmed) |
| **Maturity** | 9.0 / 10 | 9.5 / 10 | → (M-03 story granularity gap; L-02 milestones undeclared) |
| **Reliability** | 9.0 / 10 | 9.5 / 10 | → (R-01 DB name mismatch; R-02 vintage "unknown" gap) |
| **Overall** | **8.6 / 10** | **9.5 / 10** | ↓ −0.6 vs. V11 declared (C-01/C-02 are the primary drops) |

---

## 1. Agentic Readiness — HIGH

### Finding C-01 — HIGH: `CONTEXT_SUMMARY.md` Phase Is Stale — Constrained-Context Path Broken

**File:** `CONTEXT_SUMMARY.md`

**Current content (line 18):**
```
## Current Phase

cat CURRENT_PHASE.txt   → 0  (Foundation)
```

**Last Updated: 2026-07-21** (before Phase 0 completion, Phase 1, and Phase 2 all completed)

**Actual `CURRENT_PHASE.txt`:** `3`

**The operational impact:**

`AGENTS.md §1` states:

> "**Constrained context** (e.g., small context window): load this file *instead of* files 1–8
> in `AGENTS.md §1`"

`CONTEXT_SUMMARY.md` is the single-file fallback for any agent that cannot load the full
tier-1 corpus. Every agent prompt lists it as Priority 0. If a new session loads
`CONTEXT_SUMMARY.md` without also loading `CURRENT_PHASE.txt` (which is listed separately as
Priority 0 but easy to miss when context is already constrained), the agent will:

1. Believe the active phase is 0 (Foundation)
2. Identify the next work unit as "dispatch OPS for 0.1.x repo setup"
3. Attempt to create files that already exist, or overwrite completed work

The Phase Sequence table at the bottom of `CONTEXT_SUMMARY.md` also shows Phase 4 and beyond
but has no "current phase" indicator, compounding the confusion.

This is the same class of finding as V8-A (CONTEXT_SUMMARY UX invariants diverged from FE
prompt), which was declared the highest-severity finding of that audit. The phase indicator is
equally critical.

**Fix:** Update `CONTEXT_SUMMARY.md`:
1. Change the Phase section to reflect `3 (Core Map UI)`
2. Update `Last Updated` to `2026-07-26`
3. Add the current active milestone (`M3 — First Shareable Demo`) to the Phase section

---

## 2. Consistency — HIGH

### Finding C-02 — HIGH: `GET /api/v1/meta` Field Names Diverge Between Agent Prompts and Actual Implementation

**Documents in conflict:**

| Document | Field name for "list of years" | Field name for "build metadata" | Status |
|----------|-------------------------------|--------------------------------|--------|
| `docs/api/TOXMAP_API_CONTRACT.md §17` | `available_years` | `vintage_label` + `build_date` + `source` | ✅ Correct |
| `backend/app/schemas/meta.py` | `available_years` | `vintage_label`, `build_date`, `source` | ✅ Correct |
| `docs/product/TOXMAP_PROGRESS_TRACKER.md` Phase 2 DoD | `available_years` | `source: "fastapi-dev"` | ✅ Correct |
| `agents/backend-engineer/prompt.md` §Phase 2 story 2.7.3 | `loaded_years` | `db_build_info` | ❌ **Wrong** |
| `agents/backend-engineer/prompt.md` §Phase 2 Done criteria | `loaded_years` | `db_build_info` | ❌ **Wrong** |
| `agents/phase-manager/prompt.md` Gate 2→3 checklist | `loaded_years` | `db_build_info` | ❌ **Wrong** |

The API contract, the Pydantic schema, and the verified DoD all use `available_years`. The BE
agent prompt and the PM Gate checklist — the two agent-facing documents that will be read at
the start of every future session — specify `loaded_years` and `db_build_info`, which do not
exist in the live API.

**The Phase 3 failure chain:**

1. FE agent is dispatched for Phase 3, loads `agents/frontend-engineer/prompt.md` which
   references story 3.1.5 (data vintage indicator).
2. FE agent reads `agents/backend-engineer/prompt.md` to understand what the upstream
   dependency delivers: "returns `{"loaded_years": [...], "db_build_info": {...}}`".
3. FE agent writes `frontend/src/api/meta.ts` expecting `response.loaded_years` —
   a key that does not exist on the response object.
4. `data-vintage-label` in the map footer displays `undefined` or throws, failing UX
   invariant 7 and the Phase 3 DoD item "correct vintage string shown".
5. The FE agent searches for the bug in its own TypeScript, not in the upstream spec mismatch.

Additionally, a Phase Manager agent re-reading the Gate 2→3 checklist on a cold-start session
will find the gate item `GET /api/v1/meta` returns `loaded_years` — not verified in the
PROGRESS_TRACKER DoD log — and may re-open Phase 2 as incomplete.

**Root cause:** The field names were revised during API contract authoring
(`loaded_years` → `available_years` to match the `manifest.json` schema used in production
DuckDB mode), but two agent prompts were not updated to match.

**Fix:** Update the two agent prompts:
- `agents/backend-engineer/prompt.md` — story 2.7.3 description and Phase 2 Done criteria
- `agents/phase-manager/prompt.md` — Gate 2→3 checklist item

Change `loaded_years` → `available_years` and `db_build_info` → `source: "fastapi-dev"` in
both files. Do not modify the API contract or the Pydantic schema — they are correct.

---

## 3. Orchestration — HIGH

### Finding C-03 — HIGH: B-002 (PMTiles Upload) Not in Active Blockers Table; Phase 3 FE Dispatch Risk

**File:** `docs/product/TOXMAP_PROGRESS_TRACKER.md`

**Phase 3 prerequisite gate (exists in Phase 3 body):**
```
⚠️ Phase 2 OPS Pre-requisite Gate (must complete before Phase 3 FE dispatch):
| PMTiles | Manual `wrangler r2 object put basemap_us.pmtiles` | ⬜ | OPS |
```

**Active Blockers section (at bottom of tracker):**
```
| B-001 | 1 | 1.DoD | workflow_dispatch not yet verified | M1 | OPS / human | 2026-07-26 | Open |
```

B-002 is absent. The Phase Manager Core Loop (step 4) instructs: "Are any blockers preventing
progress?" referring to the Active Blockers section. A PM reading the blockers table will see
only B-001, which is noted as "does not block Phase 2" — leaving the impression that Phase 3
is free to begin.

**The dispatch failure scenario:**

Phase Manager session starts. Reads `CURRENT_PHASE.txt = 3`. Reads PROGRESS_TRACKER: Active
Phase = 3, Active Blockers = [B-001, harmless]. Dispatches FE agent for Phase 3 stories. FE
agent implements story 3.1.2 (MapLibre PMTiles basemap from R2) — writes `vite.config.ts`,
configures the PMTiles plugin, sets `VITE_PMTILES_URL`. Opens browser. Map tile requests hit
R2. R2 returns 404 for every tile. FE agent debugs the MapLibre configuration for hours before
discovering the underlying cause is a missing object, not a code error.

The prerequisite gate record in the Phase 3 body is not visible to a PM agent that only reads
the Active Blockers section, which is the designated location for orchestration blockers per
`AGENTS.md §0`.

**Fix:** Add B-002 to the Active Blockers table:

```markdown
| B-002 | 3 | 3.prereq | `basemap_us.pmtiles` not uploaded to Cloudflare R2 | Phase 3 FE dispatch | OPS / human | 2026-07-26 | Open — manual wrangler upload required (~300 MB Protomaps US extract) |
```

---

## 4. Consistency — MEDIUM

### Finding M-01 — MEDIUM: Phase 3 Story Rows 3.2 and 3.3–3.6 Collapsed Into Two Mega-Rows

**File:** `docs/product/TOXMAP_PROGRESS_TRACKER.md`

**Current Phase 3 story table (Epic 3.2):**
```
| 3.2.1–3.2.9 | Search panel: location input, chemical autocomplete, ... | 18 | ⬜ | FE | — |
```

**Current Phase 3 story table (Epics 3.3–3.6):**
```
| 3.3.1–3.6.2 | TRI circle markers, color band rendering, ... | 29 | ⬜ | FE | — |
```

Two rows carry 47 of the 72 Phase 3 story points. The individual story IDs (3.2.1 through
3.6.2) exist in the roadmap but are absent from the tracker. This breaks three workflows:

1. **PM dispatch:** The PM cannot assign a specific story boundary to the FE agent dispatch
   brief. It must say "implement 3.2.1–3.2.9" rather than dispatching individual stories and
   confirming each on completion.
2. **QA mapping:** The QA agent prompt says to write test stubs "in parallel with FE stories."
   Without individual story rows, QA cannot map test files to story IDs or mark individual
   stubs complete.
3. **Status granularity:** A single ⬜ for 18 points of work provides no visibility into
   partial progress mid-phase. During Phase 3, the PM cannot report "3.2.1–3.2.4 done, 3.2.5–
   3.2.9 in progress."

All Phases 0, 1, and 2 had individual story rows. Phase 3 collapsed epics at the time of
Phase 3 section scaffolding.

**Fix:** Expand both mega-rows into individual story rows from
`docs/product/TOXMAP_DEVELOPMENT_ROADMAP.md` §Phase 3 (roadmap is protected; tracker is not).

---

## 5. Reliability — MEDIUM

### Finding M-02 — MEDIUM: `react-map-gl` v7 / `maplibre-gl` v4 Version Incompatibility

**File:** `frontend/package.json`

```json
"maplibre-gl": "^4.5.0",
"react-map-gl": "^7.1.7",
```

`react-map-gl` v7 was authored against `maplibre-gl` v3.x. MapLibre GL JS v4 introduced
breaking API changes in the `Map` class constructor, the projection system, and the
`addLayer`/`getLayer` method signatures. The `react-map-gl` v7 wrapper passes internally
constructed `Map` options that v4 rejects.

**Observed failures on first Phase 3 compile against maplibre-gl v4:**
- TypeScript errors: `Map` constructor type mismatches in `react-map-gl`'s internal types
  vs. the `maplibre-gl` v4 exported types
- Runtime: `TypeError: this._canvas is undefined` during map initialization (v4 changed
  canvas setup timing)
- Runtime: Layer type assertions fail because v4 renamed `background-color` property paths

The correct pairing is `react-map-gl ^8.x` (released to support maplibre-gl v4) or
downgrading to `maplibre-gl ^3.x`.

**Fix:** Upgrade `react-map-gl` to `^8.0.0`:
```json
"react-map-gl": "^8.0.0"
```

`react-map-gl` v8 is a drop-in for v7 for the use patterns in the FE prompt (MapLibre mode,
`Map`, `Source`, `Layer`, `Popup` components). No React component API changes are required.

**Note:** This requires human confirmation before touching `package.json` per `AGENTS.md §3`
("Add a new `npm` dependency without noting it in the PR description"). Upgrading a major
version of an existing dependency falls under the same disclosure rule. The PR description
must include: package, from-version, to-version, reason, and compatibility notes.

---

## 6. Reliability — MEDIUM

### Finding M-03 — MEDIUM: `DATABASE_URL_SYNC` Default in `conftest.py` Uses Database Name `toxmap_test`; Docker Service Creates `toxmap`

**File:** `tests/conftest.py` (line 30)

```python
DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://postgres:postgres@localhost:5432/toxmap_test"
)
```

**`docker-compose.yml` postgres service:**
```yaml
POSTGRES_DB: toxmap
```

The default fallback connects to `toxmap_test`. The Docker service creates `toxmap`. A
developer who:
1. Port-forwards the Docker postgres (`docker compose up postgres`)
2. Runs `pytest tests/features/api/` from their host machine without setting `DATABASE_URL_SYNC`

will see `FATAL: database "toxmap_test" does not exist` and assume the test suite is broken,
rather than the default being wrong.

**The intended use case for `toxmap_test`:** A separate, isolated test database that can be
created with `CREATE DATABASE toxmap_test;`. This is a valid pattern but is not documented
anywhere in the testing docs or onboarding guide, and the Docker service does not create it.

**Fix options (pick one):**
- **Option A (simpler):** Change the default to `toxmap` to match the Docker service.
  Developers running tests in Docker or with port-forward get the right database without
  configuration.
- **Option B (safer):** Keep `toxmap_test` and add the following to `docs/onboarding/` or
  `CONTRIBUTING.md`: "Create a separate test database: `psql -c 'CREATE DATABASE toxmap_test;'`
  before running host-side tests." Also add `DATABASE_URL_SYNC` to the `.env.example` file.

This finding requires a human decision on whether test isolation (separate DB) or
developer-experience (zero-config default) takes precedence.

---

## 7. Maturity — LOW

### Finding L-01 — LOW: Phase 1 Section Header Still Reads "*(In Progress)*"

**File:** `docs/product/TOXMAP_PROGRESS_TRACKER.md`

**Current:**
```markdown
## Phase 1 — Data Pipeline *(In Progress)*
```

**Phase Summary table (correct):**
```markdown
| **1** | Data Pipeline | ✅ Complete | M1 — Data Pipeline Working | 2026-07-26 |
```

The section header was not updated when Phase 1 was declared complete. An agent scanning
section headers (not the full Phase Summary table) will misread the project state as Phase 1
still active. The same class of finding was reported in V8-A and V9 — both times the
CONTEXT_SUMMARY was the culprit; here the tracker body itself is inconsistent.

**Fix:** Change `*(In Progress)*` → `*(Complete)*` in the Phase 1 section header.

---

## 8. Maturity — LOW

### Finding L-02 — LOW: Milestones M2 and M3 Undeclared in Milestone History

**File:** `docs/product/TOXMAP_PROGRESS_TRACKER.md`

**Milestone History table:**
```
| M2 | Core API Green        | —  | |
| M3 | First Shareable Demo  | —  | |
```

Phase 2 has `Completed: 2026-07-26` in the story section body and the session log header says
"Phase 2 complete — M2 Core API Green [agent]". The Milestone History table was not updated
at phase close.

The PM Core Loop §8 instructs: "Announce milestone to the human" and "Update
TOXMAP_PROGRESS_TRACKER.md — mark current phase complete, open next phase." The milestone
history was the one step missed.

**Fix:** Set M2 Declared date to `2026-07-26` and add a note matching the session log.
Leave M3 as `—` (correctly undeclared — Phase 3 DoD not yet met).

---

## 9. Agentic Readiness — LOW

### Finding L-03 — LOW: `vintage_label` and `build_date` Always Return `"unknown"` in Dev Mode

**File:** `backend/app/services/meta_service.py` (documented as a known limitation)

The `meta_service.py` returns `vintage_label="unknown"` and `build_date="unknown"` because no
metadata table exists in the database. The Phase 3 DoD item "correct vintage string shown for
the active TRI year" requires a non-`"unknown"` value in the map footer.

This is an acknowledged known limitation from the Phase 2 memory notes
(`vintage_label and build_date always return "unknown" (no metadata table)`). It will prevent
the Phase 3 DoD from being satisfied without either:
1. A metadata table (new BE story, requires a schema migration outside the current ADR-001
   DDL), or
2. A hardcoded stub value returned by `meta_service.py` until real ingestion metadata is
   available, or
3. The Phase 3 DoD item amended to accept `"unknown"` during development (human decision)

This finding does not block Phase 3 *start*, but it will block Phase 3 *close* if not
resolved.

**Fix:** Requires human decision on which option to pursue. Until resolved, document this as
B-003 in the Active Blockers table (Phase 3 DoD gate risk, not an immediate dispatch blocker).

---

## 10. Orchestration — MEDIUM (Structural)

### Finding O-01 — MEDIUM: Phase 3 Opened Before PMTiles Prerequisite Confirmed

**Files:** `docs/product/TOXMAP_PROGRESS_TRACKER.md` header, `CURRENT_PHASE.txt`

**PROGRESS_TRACKER header:**
```
| **Active Phase** | `3` — Core Map UI |
| **Phase Start Date** | 2026-07-26 |
```

**Phase 3 prerequisite gate:**
```
| PMTiles | Manual wrangler r2 object put basemap_us.pmtiles | ⬜ | OPS |
```

`CURRENT_PHASE.txt` was incremented to `3` before the prerequisite gate was confirmed as ✅.
The PM Core Loop §7 states: "Are ALL DoD items for the current phase now ✅?" before phase
advancement. The PMTiles gate was not a Phase 2 DoD item — but it was a Phase 3 *entry*
prerequisite explicitly noted in the tracker, and the PM's own Phase Advancement Checklist
(§Gate 2→3) does not include it (an oversight in the checklist itself).

This is a structural gap: prerequisites that are not Phase N DoD items and not Phase N+1 DoD
items fall outside the PM's automated gate check. They exist only in the Phase N+1 body, where
they can be missed during the gate-to-phase-open transition.

**Fix:** Add a standing rule to the PM Phase Advancement Checklist note:
> "Before writing N+1 to `CURRENT_PHASE.txt`, verify all prerequisite gates listed in the
> Phase N+1 section header (⚠️ pre-dispatch gates) in addition to the Phase N DoD items."

This is a prompt-level fix, not a protected file.

---

## 11. New Findings Summary

| ID | Dimension | Severity | File(s) | Finding | Fix Owner |
|----|-----------|----------|---------|---------|-----------|
| C-01 | Agentic Readiness | 🔴 **High** | `CONTEXT_SUMMARY.md` | Phase shows `0 (Foundation)`; actual phase is `3`; constrained-context path broken | PM |
| C-02 | Consistency | 🔴 **High** | `agents/backend-engineer/prompt.md`, `agents/phase-manager/prompt.md` | `loaded_years`/`db_build_info` in agent prompts vs. `available_years`/`source` in API contract and implementation | PM / BE |
| C-03 | Orchestration | 🔴 **High** | `docs/product/TOXMAP_PROGRESS_TRACKER.md` | B-002 (PMTiles upload) missing from Active Blockers table; Phase 3 dispatch risk | PM |
| M-01 | Consistency | 🟡 **Medium** | `docs/product/TOXMAP_PROGRESS_TRACKER.md` | Phase 3 Epics 3.2 and 3.3–3.6 collapsed to two mega-rows; story-level tracking and QA mapping impossible | PM |
| M-02 | Reliability | 🟡 **Medium** | `frontend/package.json` | `react-map-gl ^7.1.7` incompatible with `maplibre-gl ^4.5.0`; Phase 3 first compile will fail | FE (human approval) |
| M-03 | Reliability | 🟡 **Medium** | `tests/conftest.py` | `DATABASE_URL_SYNC` default uses `toxmap_test`; Docker service creates `toxmap`; zero-config host-side test run fails | QA (human decision) |
| L-01 | Maturity | 🟢 **Low** | `docs/product/TOXMAP_PROGRESS_TRACKER.md` | Phase 1 section header reads "*(In Progress)*"; should be "*(Complete)*" | PM |
| L-02 | Maturity | 🟢 **Low** | `docs/product/TOXMAP_PROGRESS_TRACKER.md` | Milestones M2 and M3 show "—" in Declared column; M2 should be `2026-07-26` | PM |
| L-03 | Agentic Readiness | 🟢 **Low** | `backend/app/services/meta_service.py` | `vintage_label`/`build_date` always `"unknown"` in dev; blocks Phase 3 DoD "correct vintage string shown" | BE / human decision |
| O-01 | Orchestration | 🟡 **Medium** | `agents/phase-manager/prompt.md` | PM Phase Advancement Checklist lacks a step to verify Phase N+1 prerequisite gates before incrementing `CURRENT_PHASE.txt` | PM |

---

## 12. Fixes Applicable This Session (No Human Approval Required)

The following can be applied immediately without touching any protected file or external system:

| Priority | Fix | File(s) | Finding |
|----------|-----|---------|---------|
| 1 | Update `CONTEXT_SUMMARY.md` Phase section: `3 (Core Map UI)` + `Last Updated: 2026-07-26` + active milestone | `CONTEXT_SUMMARY.md` | C-01 |
| 2 | `agents/backend-engineer/prompt.md`: `loaded_years` → `available_years`; `db_build_info` → `source: "fastapi-dev"` (story 2.7.3 + Done criteria) | `agents/backend-engineer/prompt.md` | C-02 |
| 3 | `agents/phase-manager/prompt.md`: same field name fix in Gate 2→3 checklist | `agents/phase-manager/prompt.md` | C-02 |
| 4 | Add B-002 row to Active Blockers table in PROGRESS_TRACKER | `docs/product/TOXMAP_PROGRESS_TRACKER.md` | C-03 |
| 5 | Phase 1 section header: `*(In Progress)*` → `*(Complete)*` | `docs/product/TOXMAP_PROGRESS_TRACKER.md` | L-01 |
| 6 | Set M2 Declared date to `2026-07-26` in Milestone History | `docs/product/TOXMAP_PROGRESS_TRACKER.md` | L-02 |
| 7 | Add prerequisite gate check step to PM Phase Advancement Checklist | `agents/phase-manager/prompt.md` | O-01 |
| 8 | Expand Phase 3 story mega-rows to individual rows from roadmap | `docs/product/TOXMAP_PROGRESS_TRACKER.md` | M-01 |

**Require human decision before acting:**

| Fix | Finding | Decision needed |
|-----|---------|----------------|
| Upgrade `react-map-gl ^7.1.7` → `^8.0.0` | M-02 | Confirm upgrade; note in PR description |
| Change `DATABASE_URL_SYNC` default to `toxmap` or add `toxmap_test` creation to onboarding | M-03 | Choose isolation vs. zero-config |
| Resolve `vintage_label = "unknown"` in dev mode | L-03 | Stub value, new metadata table, or amended DoD |

---

## 13. Confirmed Strengths (No New Issues)

- **Security middleware:** `SecurityHeadersMiddleware` correctly implemented as pure ASGI (not
  `BaseHTTPMiddleware`), avoiding the event-loop conflict with asyncpg. The fix applied during
  Phase 2 holds — no regressions.
- **Rate limiting:** `slowapi` at 60/minute per IP with `get_remote_address` key; 429 on
  request #61 verified. No IP spoofing bypass via X-Forwarded-For because the app is run
  behind a reverse proxy in production (Cloudflare).
- **Error sanitization:** The global `Exception` handler returns `{"detail": "Internal server
  error", "code": "INTERNAL_ERROR"}` — no tracebacks, no SQLAlchemy paths, no file system
  structure in any 500 response.
- **SQL injection posture:** All 17 endpoints use SQLAlchemy ORM or parameterized Core
  expressions. Zero f-string SQL found across all routers and services.
- **SHA pinning:** All GitHub Actions remain pinned. No mutable `@vX` tags in any workflow
  file.
- **Seed data integrity:** Both immutable seed values (`89319BHPCP7MILE` copper `8205.0` lbs;
  `VAD070358684` AVTEX FIBERS INC) verified in `seed.sql`, Parquet, and API responses.
- **Test isolation:** `seed_db` is function-scoped with `yield` teardown; `db_connection` is
  session-scoped; `-p no:xdist` enforced in `addopts`. No race conditions possible in the
  current test configuration.

---

## 14. Phase 3 Dispatch Status

`CURRENT_PHASE.txt = 3`. All Phase 3 stories are ⬜ Not Started. Two conditions must be
confirmed before the FE agent is dispatched:

1. **B-002 cleared:** OPS confirms `basemap_us.pmtiles` uploaded to Cloudflare R2. Phase
   Manager must verify this before dispatch, not assume it.
2. **C-02 fixed:** BE agent prompt and PM Gate 2→3 checklist corrected to `available_years` /
   `source`. FE agent must read the correct field names before writing `meta.ts`.

Once both are confirmed, the recommended first dispatch is:
> **→ FE Agent | Phase 3 stories 3.1.1, 3.1.2, 3.1.4** (scaffold → map → layout shell)
> followed by **QA Agent | Phase 3 E2E stub creation** in parallel.

Story 3.1.3 (PMTiles basemap layer) depends on B-002 being confirmed ✅. Story 3.1.5 (data
vintage indicator) depends on C-02 being fixed and L-03 (vintage_label stub) being resolved.

---

## 15. Autonomous Development Feasibility Verdict

**Phase 3 (FE stories 3.1.1–3.1.5): Ready with two pre-conditions** (B-002 confirmed + C-02
fixed). Stories 3.1.1 and 3.1.4 can start immediately after C-02 is applied. Stories 3.1.3
and 3.1.5 depend on B-002 and L-03 respectively.

**Phase 3 (FE stories 3.2.x–3.6.x): Ready after 3.1.x foundation is in place.** M-01 (story
granularity) should be resolved before dispatch so the PM can track individual stories.

**Phase 3 QA (E2E stubs): Ready immediately.** QA can write feature file skeletons and step
stubs for T-01, T-03, T-08, and UX invariants 1–4, 7–9 without waiting for FE to complete any
stories — this is the expected parallel-track pattern.

**Phase 3 OPS (Playwright CI job): Ready after first E2E scenario passes**, per the tracker.

After the C-01/C-02/C-03 fixes are applied, the corpus is consistent enough for Phase 3
autonomous execution. Apply fixes 1–8 from §12 before dispatching any agent.

---

*End of V12 Audit. Combined findings across all audit sessions: V7 (5) + V8 (6) + V9 (4) +
V10 (10) + V11 (10) + V12 (10) = 45 findings resolved or mitigated across 7 agent prompts,
AGENTS.md, GOVERNANCE.md, CONTEXT_SUMMARY.md, PROGRESS_TRACKER.md, CHANGELOG.md, CI workflow
files, `conftest.py`, `pyproject.toml`, `bandit.yaml`, `frontend/package.json`, and test
feature stubs.*
