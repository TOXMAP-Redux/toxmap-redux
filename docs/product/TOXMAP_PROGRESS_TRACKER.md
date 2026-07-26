# TOXMAP Progress Tracker

**Owner:** Phase Manager Agent  
**Last Updated:** 2026-07-21 (cross-reference audit V1)  
**Source of truth for:** `CURRENT_PHASE.txt` · DoD status · active assignments · blockers  

> This file is updated by the Phase Manager at the end of every development session.  
> Read this before any code is written. If this disagrees with `CURRENT_PHASE.txt`, `CURRENT_PHASE.txt` wins.

---

## Current Status

| Field | Value |
|-------|-------|
| **Active Phase** | `0` — Foundation |
| **Active Milestone** | M0 — Dev Environment Ready |
| **Phase Lead** | OPS |
| **Phase Start Date** | 2026-07-16 |
| **Stories Completed** | 0 of 33 points |
| **Open Blockers** | None |

---

## Phase Summary

| Phase | Name | Status | Milestone | Completed |
|-------|------|--------|-----------|-----------|
| **0** | Foundation | 🔄 In Progress | M0 — Dev Environment Ready | — |
| **1** | Data Pipeline | ⬜ Not Started | M1 — Data Pipeline Working | — |
| **2** | Core API | ⬜ Not Started | M2 — Core API Green | — |
| **3** | Core Map UI | ⬜ Not Started | M3 — First Shareable Demo | — |
| **4** | Superfund Overlay | ⬜ Not Started | M4 — Superfund Layer | — |
| **5** | Demographics Overlay | ⬜ Not Started | M5 — Demographics Layer | — |
| **6** | Full QA Pass | ⬜ Not Started | M6 — Feature Complete | — |
| **7** | Production Deploy | ⬜ Not Started | M7 — MVP Shipped 🚀 | — |

**Legend:** ✅ Complete · 🔄 In Progress · ⬜ Not Started · 🚫 Blocked

---

## Phase 0 — Foundation

**Lead:** OPS  
**Goal:** Every developer can run the full stack locally. CI green. Security baseline established.  
**Total points:** 33

### Definition of Done Checklist

- [ ] `docker compose up` → all three services start and are healthy within 60 seconds
- [ ] `curl http://localhost:8000/health` → `{"status": "ok"}`
- [ ] React app loads at `http://localhost:3000`
- [ ] `SELECT PostGIS_version();` returns a version string inside the container
- [ ] `pytest tests/unit/` → green (no failures)
- [ ] GitHub Actions `ci.yml` shows a green check on `main`
- [ ] `SECURITY.md` present at repo root; linked from `README.md`
- [ ] All third-party GitHub Actions pinned to full 40-char SHA; `security.yml` green on `main`
- [ ] `tests/fixtures/seed.sql` exists and `psql -f tests/fixtures/seed.sql` runs without errors

### Story Status

**Epic 0.1 — Repository Setup** `OPS`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 0.1.1 | GitHub repo, main branch protection, README skeleton, .gitignore | 1 | ⬜ | OPS | — |
| 0.1.2 | Monorepo directory structure | 1 | ⬜ | OPS | — |
| 0.1.3 | Create `.github/` templates: `pull_request_template.md`, `ISSUE_TEMPLATE/{bug_report,rfc,agent-escalation}.md`, `CODEOWNERS`. **Do NOT modify existing `CONTRIBUTING.md`** — it is already authored. | 1 | ⬜ | OPS | — |

**Epic 0.2 — Docker Compose Local Stack** `OPS + BE + FE`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 0.2.1 | `docker-compose.yml` with postgres, backend, frontend | 3 | ⬜ | OPS | Needs 0.1.2 first |
| 0.2.2 | PostgreSQL with PostGIS 3.4 enabled on startup | 2 | ⬜ | OPS | — |
| 0.2.3 | Backend Dockerfile: Python 3.12 + FastAPI + health endpoint | 2 | ⬜ | BE | Needs 0.2.1 |
| 0.2.4 | Frontend Dockerfile: Node 22 + Vite dev server | 2 | ⬜ | FE | Needs 0.2.1 |
| 0.2.5 | Volume mount for hot reload (`./backend:/app`) | 1 | ⬜ | OPS | — |

**Epic 0.3 — CI/CD Pipeline** `OPS`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 0.3.1 | `ci.yml`: lint + unit tests on every PR | 3 | ⬜ | OPS | — |
| 0.3.2 | `build-data.yml` stub (no-op success) | 1 | ⬜ | OPS | — |
| 0.3.3 | Codecov integration | 2 | ⬜ | OPS | — |

**Epic 0.4 — Test Infrastructure** `QA`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 0.4.1 | `tests/conftest.py`: `seed_db` fixture | 3 | ⬜ | QA | Needs 0.4.2 |
| 0.4.2 | `tests/fixtures/seed.sql` from seed data doc | 2 | ⬜ | QA | Critical first file |
| 0.4.3 | pytest-playwright configured in `pyproject.toml` | 2 | ⬜ | QA | — |
| 0.4.4 | pytest-bdd configured: `bdd_features_base_dir` | 1 | ⬜ | QA | — |

**Epic 0.5 — Security Foundation** `SEC`

| Story | Description | Points | Status | Agent | Notes |
|-------|-------------|--------|--------|-------|-------|
| 0.5.1 | `SECURITY.md` at repo root; linked from README | 2 | ⬜ | SEC | — |
| 0.5.2 | `.github/dependabot.yml` for pip + npm + actions | 1 | ⬜ | SEC | — |
| 0.5.3 | `security.yml`: gitleaks + pip-audit + npm audit + bandit | 3 | ⬜ | SEC | — |
| 0.5.4 | Pin all Actions to 40-char SHA; document in `PINNED_ACTIONS.md` | 1 | ⬜ | SEC | **Blocked on OPS 0.3.1** — `ci.yml` must exist before SEC can pin its Actions. Do not start until OPS 0.3.1 ✅ |

---

## Phase 1 — Data Pipeline *(Not Started)*

**Lead:** DE  
**Goal:** Real TRI data queryable in PostGIS. Parquet build pipeline operational.  
**Total points:** 48  
**Prerequisites:** Phase 0 DoD complete

*Full story table will be populated when Phase 0 advances.*

**DoD Preview:**
- [ ] `alembic upgrade head` applies all tables without error
- [ ] `python -m ingestion.tri_ingest --year 2022` completes in < 30 minutes
- [ ] T-03 seed: `89319BHPCP7MILE` → copper → `8205.0` lbs → `land` → year `2008`
- [ ] T-04 seed: `VAD070358684` → `AVTEX FIBERS INC` → `FRONT ROYAL, VA`
- [ ] `tri_2022.parquet` and `tri_2022.meta.json` present after `build_parquet.py`
- [ ] `manifest.json` in R2 contains 2022 entry with non-empty `epa_vintage_label`
- [ ] `build-data.yml` has all 3 cron triggers visible in the GitHub Actions tab
- [ ] SEC story 1.SEC.1 complete: all ingestion scripts (1.2.x–1.4.x) reviewed; no SSRF patterns; `ALLOWED_DATA_URL_PREFIXES` allow-list confirmed in place

---

## Phase 2 — Core API *(Not Started)*

**Lead:** BE  
**Total points:** 62  
**Prerequisites:** Phase 1 DoD complete

**DoD Preview:**
- [ ] `pytest tests/features/api/` → F1–F6 pass, 0 failures
- [ ] Schemathesis `--checks all` → zero failures
- [ ] T-01, T-03, T-07 API assertions pass
- [ ] Input validation: 422 for out-of-bounds params; 429 on 61st rapid request
- [ ] All 17 domain endpoints + `GET /api/v1/meta` visible at Swagger UI `/docs`

---

## Phase 3 — Core Map UI *(Not Started)*

**Lead:** FE  
**Total points:** 72  
**Prerequisites:** Phase 2 DoD complete

**DoD Preview:**
- [ ] T-01, T-03, T-08 Playwright scenarios pass
- [ ] UX invariants 1, 2, 3, 4, 7, 8, 9 pass
- [ ] Data vintage label visible in map footer

---

## Phase 4 — Superfund Overlay *(Not Started)*

**Lead:** FE  
**Total points:** 21  
**Prerequisites:** Phase 3 DoD complete

**DoD Preview:**
- [ ] T-02, T-04 Playwright scenarios pass
- [ ] UX invariant 6 passes (distinct icons)

---

## Phase 5 — Demographics Overlay *(Not Started)*

**Lead:** FE  
**Total points:** 33  
**Prerequisites:** Phase 4 DoD complete

**DoD Preview:**
- [ ] T-05, T-06, T-09 Playwright scenarios pass
- [ ] UX invariants 5, 10 pass

---

## Phase 6 — Full QA Pass *(Not Started)*

**Lead:** QA  
**Total points:** 51  
**Prerequisites:** Phase 5 DoD complete

**DoD Preview:**
- [ ] `pytest tests/features/ --tb=short` exits 0 (all scenarios pass — count grows; do not gate on hardcoded number)
- [ ] All 5 performance SLAs pass
- [ ] `pytest tests/security/` → 0 failures
- [ ] Semgrep OWASP-Top-Ten clean

---

## Phase 7 — Production Deploy *(Not Started)*

**Lead:** FE + OPS  
**Total points:** 51  
**Prerequisites:** Phase 6 DoD complete

**DoD Preview:**
- [ ] App live at Cloudflare Pages URL
- [ ] `VITE_DATA_SOURCE=duckdb` + T-01/T-03 smoke pass
- [ ] Page < 3s on 4G; $0/month; security headers present

---

## Active Blockers

*No active blockers.*

| ID | Phase | Story | Description | Blocking DoD Item | Assigned To | Opened | Status |
|----|-------|-------|-------------|------------------|-------------|--------|--------|

---

## Milestone History

| Milestone | Name | Declared | Notes |
|-----------|------|----------|-------|
| M0 | Dev Environment Ready | — | Phase 0 in progress |
| M1 | Data Pipeline Working | — | |
| M2 | Core API Green | — | |
| M3 | First Shareable Demo | — | |
| M4 | Superfund Layer | — | |
| M5 | Demographics Layer | — | |
| M6 | Feature Complete | — | |
| M7 | MVP Shipped 🚀 | — | |

---

## Session Log

| Date | Phase | Action | Agent | Notes |
|------|-------|--------|-------|-------|
| 2026-07-16 to 2026-07-20 | — | Governance, architecture, security documentation complete | PM / @VictorCannestro | LICENSE, CODE_OF_CONDUCT.md, CONTRIBUTING.md, GOVERNANCE.md, MAINTAINERS.md, CHANGELOG.md, CONTEXT_SUMMARY.md, CURRENT_PHASE.txt, all agent prompts, ADRs, API contract, acceptance tests, seed data doc, roadmap, security docs authored; v1–v4 agentic audits complete |
| 2026-07-20 | — | Progress tracker initialized | PM | Phase 0 in progress; no stories started |
| 2026-07-20 | — | V5 agentic audit complete | PM | 4 new findings (V5-A low / V5-B fixed / V5-C fixed / V5-D fixed); V5-E (escalation fallback) officially closed; all V4 fixes confirmed intact; overall score 8.8/10 |
| 2026-07-20 | — | V6 agentic audit complete | PM | 6 new findings (V6-A BE endpoint count / V6-B hardcoded scenario count / V6-C security email / V6-D PM blocker table escalation fallback / V6-E story 0.5.4 dependency / V6-F agent escalation cross-reference); V6-A,C,D,E applied in-session; V6-B partially applied (gate fixed, dispatch guide not); V6-F partially applied (BE+DE fixed, FE/OPS/QA/SEC deferred); overall score 8.3/10 across 5 explicit dimensions |
| 2026-07-20 | — | V7 agentic audit complete (full) | PM | 5 findings (V7-A/A′ dispatch guide hardcoded counts / V7-B 4 agent prompts missing escalation fallback / V7-C CODEOWNERS missing SECURITY.md / V7-D FE "11"→"10" / V7-E protected files hardcoded counts); all 5 fully resolved in-session with maintainer permission for protected files; roadmap "15 endpoints" → "17" + TOXMAP_TECH_STACK_ANALYSIS.md same; overall score 8.5/10 |
| 2026-07-21 | — | Testing suite audit complete (V1) | PM | 11 findings across 9 files — 3 high (stray code fence L3, Feature 1 count 13→14 in L4, missing chart bar testids), 4 medium (invariant count 11→10 in 3 locations, FastAPI 0.11→≥0.111.0, duplicate registry entry, data-active attribute clarification), 4 low (browser_base_url conflict, CB-10 ambiguity, feature numbering note, E2E Phase 0 steps missing from tracker); all 11 resolved in-session; TOXMAP_TESTING_AUDIT.md created; overall testing score 8.7/10 |
| 2026-07-21 | — | Testing ↔ product/architecture cross-reference audit complete (V1) | PM | 9 actionable findings (3 high: API contract Warren County null→148.7, Roadmap Phase 2 DoD missing Feature 9, Layer 4 missing 5 performance SLAs + CA-10 mislabeled; 3 medium: Feature 4 marker_shape assertion missing, geocode/map-metadata out-of-scope undocumented; 3 low: future layer stubs unscaffolded, F5 cancer mortality unit missing, Security test plan undocumented); all 9 resolved in-session; 4 structural gaps documented; TOXMAP_CROSS_REFERENCE_AUDIT.md created; consistency score 7.8/10 |
| 2026-07-21 | — | V8 agentic audit complete (full) | PM | 6 new findings (V8-A HIGH: CONTEXT_SUMMARY.md UX invariants diverged from FE prompt on 5 of 10 invariants — critical constrained-context path broken; V8-B MEDIUM: OPS prompt broken file path `docs/onboarding/TOXMAP_CONTRIBUTING.md`; V8-C MEDIUM: CHANGELOG.md ownership conflict with AGENTS.md §2; V8-D MEDIUM: §14 handoff table wrong phase trigger for DE Phase 7; V8-E LOW: Phase 2 DoD endpoint count "17" vs "17 domain + meta"; V8-F LOW: Docker Desktop floor ≥4.25 outdated); all 6 resolved in-session; pre-fix score 8.6/10 → post-fix 9.4/10 |
| 2026-07-21 | 0 | `README.md` authored (project landing page) | PM / @VictorCannestro | Full project README with personality: project backstory, quick start, feature overview, architecture, data sources, acceptance tests table, roadmap table, contributing guide links, security section, acknowledgments. Satisfies Gate 0→1 DoD item "SECURITY.md linked from README.md". |
| 2026-07-23 | — | V9 agentic audit complete (full) | PM | 4 new findings (V9-A HIGH: story 7.2.4 dual-owned by FE and OPS prompts — PM assigns to OPS; V9-B MEDIUM: OPS prompt story 1.5.2 spec instructed `wrangler-action@v3` mutable tag with no Phase 1 SEC pinning story — violates AGENTS.md §11; V9-C MEDIUM: OPS Phase 0 "entirely yours" overstates scope — misleads solo-agent shortcut path; V9-D LOW: CONTEXT_SUMMARY Phase Sequence "17 endpoints" echo of V8-E not applied to this location); all 4 resolved in-session; pre-fix score 9.1/10 → post-fix 9.6/10 |

---

*This file is maintained exclusively by the Phase Manager agent. Do not edit manually.*  
*See `agents/phase-manager/prompt.md` for the Phase Manager's operational rules.*

