# TOXMAP Agents Guide

> **This file is the operational contract for AI coding agents working on the TOXMAP codebase.**  
> Project governance: see [GOVERNANCE.md](docs/GOVERNANCE.md).

**Version:** 1.4 · **Date:** 2026-07-28 · **Status:** Active

---

## 0. Entry Point — Start Here

**Every development session begins with the Phase Manager.**

Before any code is written, load `agents/phase-manager/prompt.md`. The Phase Manager reads `CURRENT_PHASE.txt`, checks `docs/product/TOXMAP_PROGRESS_TRACKER.md`, and dispatches the correct agent for the current phase.

| I want to... | Action |
|-------------|--------|
| Start a new development session | Load `agents/phase-manager/prompt.md` first |
| Know what phase we're in | Read `CURRENT_PHASE.txt` |
| Know what stories are open | Read `docs/product/TOXMAP_PROGRESS_TRACKER.md` |
| Know which agent to run | Ask the Phase Manager |
| Advance to the next phase | Phase Manager verifies DoD and increments `CURRENT_PHASE.txt` |

**Single-agent shortcut:** If running without a Phase Manager agent, read `CURRENT_PHASE.txt` + your agent's prompt + `TOXMAP_DEVELOPMENT_ROADMAP.md §5` for the current phase. Then proceed. Do NOT increment `CURRENT_PHASE.txt` yourself — flag for human review.

---

## 1. Project Context (Read Before Every Session)

Before generating any code, an agent MUST load the three **Always** files and then selectively load numbered files based on the work at hand.

**Tier 1 — Always (every session, non-negotiable):**

| File | Why |
|------|-----|
| [CURRENT_PHASE.txt](CURRENT_PHASE.txt) | Single digit — the active phase. Read first. Every session. |
| [TOXMAP_PROGRESS_TRACKER.md](docs/product/TOXMAP_PROGRESS_TRACKER.md) | Running DoD, active assignments, and blockers |
| [CONTEXT_SUMMARY.md](CONTEXT_SUMMARY.md) | ≤ 1,000-token digest of invariants, guardrails, protected files, and per-role links. **For short / context-constrained sessions, stop here** — these three files are the minimum viable context for routine implementation tasks. |

**Tier 2 — Load on demand (based on the work at hand):**

| # | File | Load when… |
|---|------|------------|
| 1 | [TOXMAP_DEVELOPMENT_ROADMAP.md](docs/product/TOXMAP_DEVELOPMENT_ROADMAP.md) | Starting a new story or when story scope is unclear |
| 2 | [ADR-001-fastapi-postgis-react.md](docs/adr/ADR-001-fastapi-postgis-react.md) | Touching the stack, API shape, or data model |
| 3 | [ADR-004-zero-budget-hosting.md](docs/adr/ADR-004-zero-budget-hosting.md) | Touching deployment, hosting, or build pipeline |
| 4 | [TOXMAP_API_CONTRACT.md](docs/api/TOXMAP_API_CONTRACT.md) | Implementing or testing any endpoint |
| 5 | [TOXMAP_TEST_SEED_DATA.md](docs/testing/TOXMAP_TEST_SEED_DATA.md) | Writing tests or touching ingestion / seed data |
| 6 | [TOXMAP_ACCEPTANCE_TESTS.md](docs/testing/TOXMAP_ACCEPTANCE_TESTS.md) | Implementing a story that closes a Gherkin scenario |
| 7 | [TOXMAP_SCREEN_CATALOG.md](docs/product/TOXMAP_SCREEN_CATALOG.md) | Any frontend work |
| 8 | [GLOSSARY.md](docs/GLOSSARY.md) | Encountering an unfamiliar domain term |

**Minimum context for opening a PR:** Tier 1 (all three) + files 1, 2, and the Gherkin feature file for the story being worked.

---

## 2. What Agents MAY Do Autonomously

These actions are pre-approved and do not require human review before a PR is opened:

- ✅ Implement a story from the current sprint backlog (Phase 0–7 in the roadmap)
- ✅ Write or fill in Gherkin step implementations in `tests/steps/`
- ✅ Add new pytest unit tests in `tests/unit/`
- ✅ Add new Playwright E2E tests that make an existing Gherkin scenario pass
- ✅ Fix a failing test (without modifying the Gherkin scenario or seed data)
- ✅ Add type annotations, docstrings, or comments to existing code
- ✅ Refactor code within a module without changing its public API
- ✅ Fix linting errors or type errors flagged by CI
- ✅ Add a new `ingestion/` script for a new optional data layer (nuclear, NPRI)
- ✅ Add a new optional layer endpoint that is already in the API contract
- ✅ Update `README.md` documentation for a feature that was just implemented
- ✅ Update `CHANGELOG.md` with entries for work completed in the current session (follow the format in the existing file; one entry per story shipped; use the commit type as the changelog category)
- ✅ Add or update entries in `docs/security/FINDINGS_REGISTER.md` or `docs/security/ACCEPTED_RISKS.md` (SEC agent only; requires justification)
- ✅ Update `docs/security/PINNED_ACTIONS.md` with verified SHA → tag mappings when pinning a new GitHub Action (OPS/SEC agents — follow the 5-step procedure in that file)
- ✅ Create a new stub workflow file in `.github/workflows/` with `# TODO:` markers for unimplemented steps (OPS agent; stub must pass YAML lint; no live credentials or `secrets.*` references)
- ✅ Rename or move a non-protected file within the same directory tree in a PR that passes CI and has 1 maintainer approval

---

## 3. What Agents MUST NOT Do Without Human Approval

These actions require a human maintainer to approve the change before any code is written:

| Action | Why It's Restricted |
|--------|---------------------|
| ❌ Modify any ADR file (`ADR-00*.md`) | Architecture decisions require human judgment; changes affect the entire system |
| ❌ Modify `TOXMAP_API_CONTRACT.md` | Any endpoint shape change breaks existing tests and consumer integrations |
| ❌ Modify `tests/fixtures/seed.sql` | Seed values are derived from real UCD 2011 study data; incorrect values invalidate all T-01–T-09 tests |
| ❌ Modify `TOXMAP_TEST_SEED_DATA.md` | Same reason; this is the source of truth for seed values |
| ❌ Modify `TOXMAP_ACCEPTANCE_TESTS.md` | Gherkin scenarios are the contract between product and QA; changes require PO approval |
| ❌ Modify `TOXMAP_DEVELOPMENT_ROADMAP.md` | Roadmap changes affect sprint planning; must be human-approved |
| ❌ Add a new endpoint not in the API contract | Represents a scope change; requires ADR-001 update |
| ❌ Change a Gherkin scenario's `Given/When/Then` assertions | Changes acceptance criteria, which changes the product |
| ❌ Delete any file listed in §4 (Protected Files) without an RFC — these are read-only for agents under any circumstances | Deletion of protected files changes the product contract or architecture; requires human RFC process |
| ❌ Delete a non-protected file in a PR — CI must pass; PR requires 1 maintainer approval | Standard PR review is sufficient for non-protected file removal |
| ❌ Modify **existing** service definitions in `docker-compose.yml` without an RFC | Changes to existing services break all contributors' local environments; adding a new test/debug-only service is permitted in a PR with 1 maintainer approval |
| ❌ Add a new `pip` or `npm` dependency without noting it in the PR description | Dependency additions have security, license, and bundle-size implications — the note must include: package, version, license, justification |
| ❌ Change the `color_band` tier thresholds | These are product decisions sourced from NLM design |
| ❌ Change marker shapes (circle/diamond) | Defined by original NLM TOXMAP screenshots; UX invariant 6 |
| ❌ Suppress a `bandit` or `semgrep` finding (`# nosec`, `# nosemgrep`) without adding an entry to `docs/security/FINDINGS_REGISTER.md` | Security suppressions require documented justification and maintainer review |
| ❌ Introduce a new third-party GitHub Action without pinning it to a full 40-char SHA | Mutable action tags are a supply chain attack vector (T-SEC-08) |
| ❌ Set `ALLOWED_ORIGINS` to `["*"]` in any configuration | Open CORS breaks the security model of the entire API |

---

## 4. Protected Files (Read-Only for Agents)

These files must never be modified by an agent under any circumstances. If a change seems necessary, open an issue instead.

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
SECURITY.md                         ← Security policy; changes require Security Engineer + Maintainer approval
```

---

## 5. Mandatory Pre-PR Checklist

> **CI automatically enforces:** ruff format/lint, mypy, Prettier, ESLint, tsc, pytest unit/API/E2E gates, and Docker build correctness via `ci.yml`.
> This checklist covers only the items that require **agent judgment** and cannot be caught by CI alone.

**Always:**
- [ ] `pytest tests/unit/` passes locally with zero failures
- [ ] No new `any` types introduced in TypeScript (CI ESLint may miss context-specific usages)
- [ ] No new `# type: ignore` comments added in Python without an inline justification comment
- [ ] All new Python functions have type annotations on parameters and return values
- [ ] All new **exported / public-API** TypeScript functions and React components have a JSDoc summary *(recommended for internal helpers, not required)*

**For backend changes:**
- [ ] All API Gherkin scenarios for the modified endpoint still pass: `pytest tests/features/api/<feature>.feature`
- [ ] Schemathesis does not report new failures: `schemathesis run http://localhost:8000/openapi.json --checks response_schema_conformance`
- [ ] Response shape matches the contract in `TOXMAP_API_CONTRACT.md` exactly (field names, types, nullability)

**For frontend changes:**
- [ ] Relevant UX invariants pass: `pytest tests/features/e2e/ux_invariants.feature`
- [ ] No element with text "Quick Search" exists in DOM (UX invariant 4)
- [ ] No element with text "Demographics" as primary nav label (UX invariant 4)
- [ ] Numbers ≥ 1,000 are comma-formatted in all rendered output (UX invariant 8)

**For data/ingestion changes:**
- [ ] `psql -f tests/fixtures/seed.sql` still runs without errors (seed.sql not modified)
- [ ] Seed assertion values from §9 of `TOXMAP_TEST_SEED_DATA.md` still hold: `89319BHPCP7MILE` copper = `8205.0` lbs to land

**For E2E/Playwright changes:**
- [ ] The specific UCD task scenario being implemented passes: `pytest tests/features/e2e/ -k "T-0X"`
- [ ] No previously passing scenario was broken

---

## 6. Code Style Constraints

### Python (Backend + Ingestion)

```python
# CORRECT: type annotations on all functions
async def get_facilities_near(
    lat: float,
    lon: float,
    radius_miles: float,
    session: AsyncSession,
) -> list[Facility]:
    ...

# WRONG: missing types, missing async
def get_facilities(lat, lon, radius):
    ...
```

- **Formatter:** `ruff format` (configured in `pyproject.toml`)
- **Linter:** `ruff check --fix`
- **Type checker:** `mypy` — no unresolved errors
- **Max line length:** 100
- **Import order:** standard library → third-party → local (`isort` compatible)
- **No** `print()` in production code — use `logging.getLogger(__name__)`

### TypeScript (Frontend)

```typescript
// CORRECT: explicit return type, named component
export function FacilityMarker({ facility }: FacilityMarkerProps): JSX.Element {
  return <Marker ... />;
}

// WRONG: implicit any, anonymous function
export default ({ f }) => <Marker data={f} />;
```

- **Formatter:** `prettier` (`.prettierrc` in repo root)
- **Linter:** `eslint` with `@typescript-eslint/recommended`
- **No `any`** — use `unknown` with type guards if necessary
- **React:** functional components only; no class components
- **`data-testid`** attributes required on all interactive elements and panels for Playwright

### SQL (Migrations + Queries)

- All table/column names: `snake_case`
- All PostGIS functions: uppercase (`ST_DWithin`, not `st_dwithin`)
- New columns must have a corresponding entry in `TOXMAP_API_CONTRACT.md` before being added — if missing, do not add the column; open an issue instead

---

## 7. Commit Message Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer: References #issue, Closes #issue]
```

**Types:** `feat` · `fix` · `test` · `refactor` · `docs` · `chore` · `perf`  
**Scopes by agent role:**

| Agent | Authoritative Scopes | Notes |
|-------|---------------------|-------|
| BE | `api` · `ingestion` · `infra` · `seed` | Use `api` for endpoint code; `ingestion` for BE-specific pipeline work |
| DE | `ingestion` · `data` | Use `ingestion` for ingest scripts; `data` for Parquet build and census scripts |
| FE | `frontend` | All React, TypeScript, and DuckDB WASM frontend code |
| QA | `test` · `e2e` · `seed` · `infra` | `seed` for seed.sql changes (requires human approval); `infra` for conftest, CI test jobs |
| SEC | `security` | All security tooling, middleware, CI jobs, and documentation |
| OPS | `infra` · `ci` · `docker` · `deploy` | `infra` for repo config; `ci` for workflow files; `docker` for Dockerfiles/Compose |
| PM | *(process only — no code commits)* | `chore(phase-manager)` for CURRENT_PHASE.txt; `docs(phase-manager)` for PROGRESS_TRACKER |

> **Scope conflicts:** `infra` is shared between OPS and QA. OPS uses it for repo/CI/Docker infrastructure; QA uses it for pytest configuration (`conftest.py`, `pyproject.toml` test settings). Both usages are valid — the PR description should clarify if ambiguous.

**Examples:**
```
feat(api): add restrict_to_state parameter to GET /api/v1/facilities

Implements story 2.1.2 from TOXMAP_DEVELOPMENT_ROADMAP.md Phase 2.
Closes #42

test(e2e): implement Playwright steps for T-01 lead-compound scenario

Step implementations for Feature 7 (UCD 2011 Task Scenarios).
All steps in T-01 now pass: pytest tests/features/e2e/ -k "T-01"

fix(frontend): comma-format release quantities in ResultsTable

Resolves UX invariant 8 failure. 8205 now renders as 8,205 lbs.
```

**Agent-specific rule:** If a commit was generated by an AI agent, append `[agent]` to the subject line:
```
feat(api): add viewport bbox scoping to facility search [agent]
```

---

## 8. Handling Ambiguity

When requirements are unclear, an agent MUST follow this decision tree:

```
1. Is the answer in the acceptance criteria for this story?
      YES → follow the acceptance criteria exactly
      NO  ↓

2. Is there a Gherkin scenario that would fail if I implement it one way?
      YES → implement the way that makes the scenario pass
      NO  ↓

3. Is there a screenshot in TOXMAP_SCREEN_CATALOG.md that answers it?
      YES → implement to match the screenshot
      NO  ↓

4. Does the API contract specify the behavior?
      YES → follow the contract
      NO  ↓

5a. If GitHub write access is available:
    Open a GitHub issue tagged [clarification-needed] and halt. Do not proceed.

5b. If GitHub write access is NOT available:
    Create a file named `docs/escalations/ESCALATION_[YYYYMMDD_HHMMSS].md` containing:
    - The story ID and acceptance criterion that is ambiguous
    - The two candidate interpretations (A and B)
    - The interpretation you are proceeding with, and why
    Add a comment in the code at the decision point: `# ASSUMPTION: <one sentence>`
    Mark the PR description with: "⚠️ ASSUMPTION MADE — requires human review before merge"
    Do not merge without human confirmation.
```

**Never guess about:**
- Seed data values (always from `TOXMAP_TEST_SEED_DATA.md`)
- API response shapes (always from `TOXMAP_API_CONTRACT.md`)
- Color codes for markers (always from `TOXMAP_SCREEN_CATALOG.md §Marker Icon Design Reference`)
- UX label text (always from the UX Architecture Decisions table in ADR-001)

---

## 9. Scope Boundaries by Sprint Phase

An agent working on a given phase MUST NOT implement stories from a future phase. This prevents out-of-order dependencies and scope creep.

| If current phase is... | Agent may work on stories from... | Agent must NOT work on... |
|------------------------|----------------------------------|--------------------------|
| Phase 0 | Phase 0 only | Phase 1+ |
| Phase 1 | Phase 0–1 | Phase 2+ |
| Phase 2 | Phase 0–2 | Phase 3+ |
| Phase 3 | Phase 0–3 | Phase 4+ |
| ... | Phase 0–N | Phase N+1+ |

**Exception:** A QA agent implementing Gherkin step stubs may write the step file for the current AND next phase, as long as the steps are marked `@pytest.mark.skip("Not yet implemented")`.

---

## 10. Data Integrity Rules

These rules exist because TRI data and Superfund data are used for **real public health decisions**. Incorrect data is actively harmful.

1. **Never invent TRI facility IDs.** IDs follow the EPA format: `ZIPCODEFIRST5CHARSOFNAME`. If you need a new test facility, use a fictional but format-compliant ID from `TOXMAP_TEST_SEED_DATA.md`.

2. **Never alter the two exact UCD 2011 values:**
   - `89319BHPCP7MILE` → copper → `8205.0` lbs → `land` medium → year `2008`
   - `VAD070358684` → AVTEX FIBERS INC → `FRONT ROYAL, VA`
   These are cited from a peer-reviewed source. Changing them breaks T-01/T-03/T-04.

3. **Never use `0` as a default for `total_release_lbs`.** Use `null`/`None` when data is missing — `0` means the facility reported zero releases, which is a meaningful data point.

4. **Never hardcode EPA TRI column names.** Always use `TRI_COLUMN_MAP` from `tri_parser.py`. Column names change between EPA release years.

5. **The `meta.units` object in demographics responses must be populated from the database, not hardcoded.** This allows unit changes when Census data formats change.

---

## 11. Security Guardrails

Every agent — regardless of role — must follow these rules on every PR. The Security Engineer agent additionally owns the tooling that enforces them in CI.

### Credential and Secret Rules
- **Never commit credentials.** No API keys, Cloudflare tokens, database passwords, or bearer tokens in any committed file.
- **Never add `VITE_` prefixed env vars that contain secrets.** Vite inlines all `VITE_`-prefixed variables into the public browser bundle. They are visible to any user who reads the page source.
- **Never log sensitive values** (API tokens, database connection strings, internal paths) in FastAPI routes or ingestion scripts.

### Query Safety Rules
- **PostGIS queries must use parameterized inputs.** Never use f-strings or string concatenation to construct SQL with user input. The pattern is:

```python
# CORRECT: parameterized
result = await session.execute(
    select(Facility).where(Facility.state_code == state)
)

# WRONG: SQL injection risk
result = await session.execute(
    text(f"SELECT * FROM facilities WHERE state_code = '{state}'")
)
```

- **DuckDB WASM queries must use `$variable` parameterization.** Never interpolate user-supplied values into DuckDB SQL template literals in React hooks.

### Parameter Validation Rules
- **The `restrict_to_state` parameter must be validated** as a 2-letter uppercase string before reaching the database layer. Reject with 422 for any other value.
- **The `radius_miles` parameter must be capped at 500** on `/api/v1/facilities` and `/api/v1/superfund` — anything larger triggers an expensive full-table PostGIS scan. Reject with 422 for `radius_miles > 500`. **Exception:** The `/api/v1/facilities/browse` and `/api/v1/superfund/browse` endpoints have no radius constraint (return all facilities/sites for browse mode).
- **The `lat`/`lon` parameters must be validated** to WGS84 bounds (`lat` ∈ [−90, 90], `lon` ∈ [−180, 180]). Reject with 422 for out-of-range values.
- **All parameter validation must happen in Pydantic schemas** — not in router functions, not in service layer functions. Validation belongs at the API boundary.

### Dependency Rules
- **New pip or npm dependencies must be noted in the PR description** with: package name, version, license, and a one-sentence justification. Maintainer checks for CVEs before merge.
- **New GitHub Actions must be pinned to a full 40-character SHA** in the same commit they are introduced. Readable tag comments are required (e.g., `# v3.0.0`). Never use `@latest`.
- **File uploads are not in scope for this project.** Do not add any file upload endpoint.

### Frontend Security Rules
- **`dangerouslySetInnerHTML` is prohibited.** Zero occurrences allowed in `frontend/src/`. CI grep enforces this.
- **All `<a target="_blank">` links must include `rel="noopener noreferrer"`** to prevent reverse tabnapping.
- **Error boundaries must not expose internal exception messages** to users — render a generic fallback UI.

### CI Security Gate Rules
- **The `security.yml` workflow must stay green.** An agent must not open a PR that fails the gitleaks, pip-audit, npm audit, or bandit jobs.
- **Never disable a security CI check with `continue-on-error: true`** without an `[agent-escalation]` issue and maintainer approval.
- **Finding suppressions (`# nosec`, `# nosemgrep`) require** a justification comment on the line above AND an entry in `docs/security/FINDINGS_REGISTER.md`.

### Security Role Reference
The Security Engineer agent (`agents/security-engineer/prompt.md`) owns the stories and tooling that enforce all of the above rules in automation. Consult that prompt for:
- Full threat model (T-SEC-01 through T-SEC-15)
- Pydantic validator reference patterns
- Rate limiting implementation (`slowapi`)
- Error sanitization patterns
- CSP / COEP / COOP configuration for DuckDB WASM
- Production `_headers` file spec

---

## 12. When to Escalate to a Human

Open a GitHub issue tagged `[agent-escalation]` and stop work when:

- A required change conflicts with a protected file
- A Gherkin scenario cannot be made to pass without changing the seed data
- Two acceptance criteria in different stories directly contradict each other
- A dependency (npm/pip) has a **Critical or High CVE with no patched version available** in a compatible range and no equivalent drop-in replacement exists — *first attempt a version bump or package swap; escalate only when that is not possible*
- The Schemathesis output shows a response shape mismatch that cannot be fixed without modifying the API contract
- Any story requires a new database table not in the ADR-001 data model
- A `gitleaks` scan finds a **confirmed secret in git commit history** (not a false positive) — do not attempt history rewrite; escalate to Maintainer immediately
- A security control (e.g., COEP/COOP header) causes a regression in a previously passing Playwright test and no workaround exists within the current architecture

**If GitHub write access is unavailable**, do not silently stop. Instead:

1. Create a file named `docs/escalations/ESCALATION_[YYYYMMDD_HHMMSS].md`.
2. The file must contain: (a) the triggering condition from the list above, (b) the exact
   story and change that was blocked, (c) the recommended resolution or the question that
   needs human judgment.
3. Do not open a PR that merges until a human has acknowledged this file.
4. In your session output, clearly state: *"docs/escalations/ESCALATION_[timestamp].md written — human review
   required before proceeding."*

---

## 13. Reference Quick Links

| Need to know... | Go to |
|-----------------|-------|
| **What phase are we in?** | `CURRENT_PHASE.txt` |
| **What's done / open / blocked?** | `docs/product/TOXMAP_PROGRESS_TRACKER.md` |
| **Which agent runs next?** | `agents/phase-manager/prompt.md` |
| Stack decisions | [ADR-001](docs/adr/ADR-001-fastapi-postgis-react.md) |
| Production hosting | [ADR-004](docs/adr/ADR-004-zero-budget-hosting.md) |
| Endpoint shapes + example JSON | [TOXMAP_API_CONTRACT.md](docs/api/TOXMAP_API_CONTRACT.md) |
| Seed data + exact assertion values | [TOXMAP_TEST_SEED_DATA.md](docs/testing/TOXMAP_TEST_SEED_DATA.md) §9 |
| Which Gherkin scenario covers this endpoint | [TOXMAP_ACCEPTANCE_TESTS.md](docs/testing/TOXMAP_ACCEPTANCE_TESTS.md) |
| UI layout + design | [TOXMAP_SCREEN_CATALOG.md](docs/product/TOXMAP_SCREEN_CATALOG.md) |
| Sprint stories + DoD | [TOXMAP_DEVELOPMENT_ROADMAP.md](docs/product/TOXMAP_DEVELOPMENT_ROADMAP.md) |
| UX label text | [ADR-001 §UX Architecture Decisions](docs/adr/ADR-001-fastapi-postgis-react.md) |
| Marker colors/shapes | [TOXMAP_SCREEN_CATALOG.md §Marker Icon Design Reference](docs/product/TOXMAP_SCREEN_CATALOG.md) |
| Performance SLAs | [TOXMAP_API_CONTRACT.md §Performance SLAs](docs/api/TOXMAP_API_CONTRACT.md) |
| Threat model + T-SEC-xx IDs | [agents/security-engineer/prompt.md §Threat Model](agents/security-engineer/prompt.md) |
| Security tooling + guardrails | [GOVERNANCE.md §8](docs/GOVERNANCE.md) |
| Suppressed findings | [docs/security/FINDINGS_REGISTER.md](docs/security/FINDINGS_REGISTER.md) |
| Accepted risks | [docs/security/ACCEPTED_RISKS.md](docs/security/ACCEPTED_RISKS.md) |
| `data-testid` values for Playwright | [docs/testing/TEST_ID_REGISTRY.md](docs/testing/TEST_ID_REGISTRY.md) |
| **Open escalations (human review needed)** | [`docs/escalations/`](docs/escalations/) — one file per blocked story |

---

## 14. Inter-Agent Handoff Protocol

When an agent completes a story that unblocks another agent, it MUST signal completion clearly. The Phase Manager uses these signals to update `TOXMAP_PROGRESS_TRACKER.md` and dispatch the next agent.

### Completion Signal Format

Include this at the end of every agent session output or PR description when work unblocks another agent:

```
## Handoff Signal

**Stories completed:** [list story IDs]
**Unblocked agents:** [which agents can now proceed]
**Files produced:** [list key output files / endpoints]
**Blockers encountered:** [any escalations written or issues opened]
**Next recommended dispatch:** [agent role + story IDs]
```

### Critical Handoff Dependencies

| Completing agent | Completing story | Unblocks |
|-----------------|-----------------|---------|
| BE | 1.1.4 (schema complete) | **DE can now start 1.2.1** (TRI ingestion requires all tables to exist) |
| DE | 1.2.6 (TRI ingestion validated) | **SEC can now complete 1.SEC.1** (scripts exist to review) |
| DE | 1.5.1 (Parquet build pipeline) | **OPS can now start 1.5.2** (build-data.yml upgrade needs the pipeline command) |
| OPS | 0.3.1 (ci.yml created) | **SEC can now run 0.5.4** (SHA-pin ci.yml Actions; requires the file to exist first) |
| BE | Phase 2 complete | **FE can start Phase 3** (all API endpoints must be live before frontend uses them) |
| FE | 3.1.5 (data vintage indicator) | Confirms **`GET /api/v1/meta`** (BE story 2.7.3) is working in dev mode |
| FE | 7.1.1–7.1.8 complete (DuckDB WASM hooks, Phase 7) | **DE 7.DE.1** can begin — Parquet column parity review (DuckDB WASM hooks now exist; DE audits that Parquet column names match API contract field names as used in those hooks) |

### No Circular Dependency Rule

If an agent discovers it is waiting on another agent who is also waiting on it, this is a **circular dependency blocker**. The agent MUST:
1. Stop work immediately
2. Open an `[agent-escalation]` issue (or write `docs/escalations/ESCALATION_[YYYYMMDD_HHMMSS].md`) identifying both agents and the circular dependency
3. Propose a resolution: typically, one agent delivers a minimal stub or interface contract so the other can proceed
4. Surface to the Phase Manager for resolution — do NOT attempt to resolve circular dependencies unilaterally

