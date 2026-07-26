# Contributing to TOXMAP

Welcome — and thank you for considering a contribution. TOXMAP is an open-source clone of the EPA/NLM TOXMAP application, built to make environmental health data accessible to everyone at zero cost.

> **AI agents:** See [AGENTS.md](AGENTS.md) for your specific operational guidelines.  
> **Project governance:** See [GOVERNANCE.md](docs/GOVERNANCE.md) for decision-making process.

---

## Table of Contents

1. [Getting Started](#2-getting-started)
2. [Types of Contributions](#3-types-of-contributions)
3. [Development Workflow](#4-development-workflow)
4. [Code Style](#5-code-style)
5. [Testing Requirements](#6-testing-requirements)
6. [Pull Request Process](#7-pull-request-process)
7. [Adding New Features](#8-adding-new-features)
8. [Working with Seed Data](#9-working-with-seed-data)
9. [Documentation Standards](#10-documentation-standards)
10. [Dependency Policy](#11-dependency-policy)
11. [First-Time Contributors](#12-first-time-contributors)

---

## 1. Getting Started

### Prerequisites

| Tool           | Minimum Version                    | Why                                             |
|----------------|------------------------------------|-------------------------------------------------|
| Docker Desktop | ≥ 4.35 (latest stable recommended) | Full stack via `docker compose`                 |
| Git            | 2.40+                              | Branch management                               |
| Node.js        | 22.x                               | Frontend development                            |
| Python         | 3.12+                              | Backend + ingestion (optional for pure FE work) |
| `psql`         | 16+                                | Direct DB access for debugging                  |

### Local Setup

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/toxmap.git
cd toxmap

# 2. Start the full stack
docker compose up

# 3. Wait for health checks (~30 seconds), then verify:
curl http://localhost:8000/health          # {"status": "ok"}
open http://localhost:3000                  # React app

# 4. Load seed data
docker compose exec backend psql -U postgres -d toxmap -f /app/tests/fixtures/seed.sql

# 5. Run the full test suite
docker compose exec backend pytest tests/
pytest tests/features/e2e/

# 6. Confirm seed assertions (should all return rows)
docker compose exec postgres psql -U postgres -d toxmap -c \
  "SELECT tri_facility_id, total_release_lbs FROM release_events re
   JOIN facilities f ON f.id = re.facility_id
   WHERE f.tri_facility_id = '89319BHPCP7MILE' AND re.reporting_year = 2008;"
# Expected: tri_facility_id=89319BHPCP7MILE, total_release_lbs=8205.0
```

### Working Without Docker

If you only want to contribute to the frontend:

```bash
cd frontend
npm install
VITE_DATA_SOURCE=api VITE_API_URL=http://localhost:8000 npm run dev
```

If you only want to contribute to the backend:

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

---

## 3. Types of Contributions

| Type                                    | Welcome?        | How to Start                                                |
|-----------------------------------------|-----------------|-------------------------------------------------------------|
| Bug fix                                 | ✅ Always        | Open an issue, reference the failing Gherkin scenario       |
| Story from roadmap                      | ✅ Always        | Comment on the GitHub issue for the story you want          |
| New test (Gherkin step or E2E)          | ✅ Always        | Reference the scenario in `TOXMAP_ACCEPTANCE_TESTS.md`      |
| Performance improvement                 | ✅               | Include before/after `pytest-benchmark` output in PR        |
| Documentation fix                       | ✅ Always        | Direct PR, no issue needed for typos/clarifications         |
| New optional data layer (nuclear, NPRI) | ✅               | Must have a story in the roadmap or open an RFC issue first |
| New required feature (F-xx)             | ⚠️ RFC required | See §8 — requires product approval                          |
| Changing an ADR                         | ⚠️ RFC required | See [GOVERNANCE.md](docs/GOVERNANCE.md)       |
| Changing API contract shape             | ⚠️ RFC required | Breaking change; requires maintainer approval               |
| Changing seed data values               | ⚠️ RFC required | Must trace to a primary source (NLM/UCD/EPA)                |

---

## 4. Development Workflow

### Branching Strategy (GitHub Flow)

```
main                    ← always deployable; protected
  └─ feat/2.1.1-restrict-to-state     ← feature branch per story
  └─ fix/ux-invariant-8-commas        ← bug fix branch
  └─ test/t03-playwright-steps        ← test-only branch
  └─ docs/update-screen-catalog       ← docs-only branch
```

**Branch naming convention:**
```
<type>/<story-id>-<short-description>
```

Types: `feat` · `fix` · `test` · `docs` · `refactor` · `perf` · `chore`

**Rules:**
- Branch off `main` only
- One story per branch
- Branches older than 30 days without activity will be closed
- Never commit directly to `main` — all changes via PR

### Commit Messages

Follow the Conventional Commits spec:

```
<type>(<scope>): <subject in imperative mood, ≤72 chars>

[optional body: what and why, not how]

[optional footer: Closes #42, References #15]
```

**Good examples:**
```
feat(api): add bbox scoping to facility search endpoint

Implements story 2.1.4. Results are now scoped to the viewport
bounding box, eliminating empty placeholder rows (UX invariant 2).

Closes #87

test(e2e): implement Playwright steps for T-03 copper Nevada scenario

All 6 steps in T-03 now pass against seeded Robinson Nevada Mining Co
fixture (8,205 lbs copper, land medium, year 2008).

fix(frontend): move facility popup close button to bottom of panel

Resolves UX invariant 9 failure. Close link now always in viewport
regardless of popup content height.
```

**Bad examples:**
```
WIP                            # not descriptive
fixed stuff                    # no type, no scope, past tense
feat: added the thing          # past tense, vague
```

---

## 5. Code Style

### Python

```bash
# Format
ruff format backend/

# Lint + auto-fix
ruff check --fix backend/

# Type check
mypy backend/app backend/ingestion
```

Key rules:
- All function parameters and return types annotated
- No `print()` — use `logging.getLogger(__name__)`
- No bare `except:` — always catch a specific exception type
- PostGIS queries use **parameterized inputs only** (never f-string SQL)
- Async all the way down in `app/` — no sync I/O in async routes

### TypeScript / React

```bash
# Format
npx prettier --write frontend/src/

# Lint
npx eslint frontend/src/ --fix

# Type check
npx tsc --noEmit
```

Key rules:
- No `any` — use `unknown` + type guards where necessary
- Functional components only; no class components
- All interactive elements must have `data-testid` for Playwright
- `useQuery` / `useMutation` from React Query for all API calls
- No direct `fetch()` calls outside `api/` module

### SQL

- Table and column names: `snake_case`
- PostGIS functions: `UPPERCASE` (`ST_DWithin`, `ST_GeomFromText`)
- All migrations via Alembic — no manual `psql` schema changes
- New columns must exist in `TOXMAP_API_CONTRACT.md` before being written to the DB

---

## 6. Testing Requirements

Every PR must satisfy the following gates. CI enforces these automatically.

### Gate 1 — Unit Tests (always required)
```bash
pytest tests/unit/ -v
```
All tests must pass. Coverage must not decrease from the baseline on `main`.

### Gate 2 — API Contract (required for any backend change)
```bash
pytest tests/features/api/<changed_feature>.feature -v
schemathesis run http://localhost:8000/openapi.json --checks response_schema_conformance
```
No new Schemathesis failures allowed.

### Gate 3 — E2E (required for any frontend change)
```bash
pytest tests/features/e2e/ux_invariants.feature
```
All 10 UX invariants must pass.

### Gate 4 — Scenario-Specific (required when a story closes a scenario)
The PR description must identify which Gherkin scenario(s) the story addresses, and those scenarios must show green in CI.

### Gate 5 — Performance (required for changes to query or render path)
```bash
pytest tests/benchmarks/ --benchmark-only --benchmark-compare
```
No p95 regression beyond +20% from baseline.

### Test File Naming

| File type            | Location              | Naming pattern             |
|----------------------|-----------------------|----------------------------|
| Unit test            | `tests/unit/`         | `test_<module>.py`         |
| API Gherkin feature  | `tests/features/api/` | `<domain>.feature`         |
| E2E Gherkin feature  | `tests/features/e2e/` | `<scenario_group>.feature` |
| Step implementations | `tests/steps/`        | `<layer>_steps.py`         |
| Benchmarks           | `tests/benchmarks/`   | `bench_<endpoint>.py`      |

---

## 7. Pull Request Process

### Before Opening a PR

- [ ] Branch is up to date with `main`
- [ ] All CI gates pass locally (see §6)
- [ ] PR description uses the template (see below)
- [ ] Linked to a GitHub issue or roadmap story

### PR Description Template

```markdown
## Summary
<!-- What does this change do and why? -->

## Related
- Closes #
- Story: <!-- TOXMAP_DEVELOPMENT_ROADMAP.md Phase X, Story X.X.X -->

## Type of Change
- [ ] Bug fix (non-breaking)
- [ ] Feature / enhancement (non-breaking)
- [ ] Breaking change — ADR or API contract update required
- [ ] Chore — tests, docs, deps, or refactor

## How to Test
<!--
Steps for the reviewer to verify this change locally.
Include required env vars, Docker Compose flags, or seed data.
Attach before/after screenshots for UI changes.
-->

### Gherkin Scenarios Affected
<!-- Scenario(s) that now pass because of this PR. Omit section if none. -->

## Checklist
- [ ] Branch is up to date with `main`
- [ ] `tests/fixtures/seed.sql` unchanged *(or RFC #\_\_\_ linked — requires 2 approvals)*
- [ ] `docs/api/TOXMAP_API_CONTRACT.md` unchanged *(or RFC #\_\_\_ linked — requires 2 approvals)*
- [ ] No ADR modified *(or RFC #\_\_\_ linked — requires unanimous maintainer approval)*
- [ ] AI-generated commits: squash subject ends with `[agent]`

```

### Review Criteria

Reviewers will check:
1. Does the implementation match the acceptance criteria exactly?
2. Does it break any existing passing Gherkin scenario?
3. Does it introduce any deviation from the locked architecture decisions (ADR-001, ADR-004)?
4. Are there `data-testid` attributes on all new interactive elements?
5. Does the commit history tell a coherent story?

### Merge Policy

- Minimum **1 human reviewer approval** for all PRs
- **2 approvals** required for changes to: ingestion scripts, API contract, any ADR
- Squash-merge is preferred to keep `main` history clean
- **When squash-merging a branch where any commit was `[agent]`-tagged, the squash commit subject must retain `[agent]` at the end of the subject line** to preserve agent traceability in `main` history
- CI must be green at the time of merge (no "merge anyway" exceptions)

---

## 8. Adding New Features

### For stories already in the roadmap

Just implement the story. Reference the story ID in your PR.

### For new requirements (not in the roadmap)

Open a **Request for Comment (RFC)** issue with the label `rfc`:

```markdown
**Title:** RFC: Add [feature name]

**Problem:** What user problem does this solve?
**Proposed Solution:** How would it work?
**Data Source:** What EPA/NLM dataset powers this?
**Functional Requirement:** Proposed F-xx addition to TOXMAP_TECH_STACK_ANALYSIS.md
**Acceptance Criteria:** What Gherkin scenario would prove it works?
**ADR Impact:** Does this require changing ADR-001 or ADR-004?
**Effort Estimate:** Story points?
```

RFC issues are discussed for at least **5 business days** before any code is written. Maintainers add `rfc-accepted` or `rfc-rejected` labels.

### For changes to locked architecture decisions (ADR changes)

See [GOVERNANCE.md §ADR Lifecycle](docs/GOVERNANCE.md).

---

## 9. Working with Seed Data

Seed data is sourced from real-world publications. Precision matters for environmental health data.

### Adding a new test facility

1. Verify the story in `TOXMAP_DEVELOPMENT_ROADMAP.md` requires a new seed facility
2. Assign a facility ID following the EPA format: `ZIPCODEFIRST5CHARSOFNAME` (e.g., `21219BTHLS3RD`)
3. Add the facility to `TOXMAP_TEST_SEED_DATA.md` with a `Source Citation` column entry
4. Add the `INSERT` statement to `tests/fixtures/seed.sql`
5. Open a PR with the `seed-data` label — requires 2 reviewer approvals

### Modifying existing seed data values

**This requires an RFC issue.** Seed values that originated from the UCD 2011 study or NLM articles are **pinned to their source documents** and cannot be changed without a primary-source citation for the new value.

The following values are immutable without source-cited RFC:

| Value                                             | Source                 |
|---------------------------------------------------|------------------------|
| `89319BHPCP7MILE` copper = `8205.0` lbs to `land` | UCD 2011 study, Task 3 |
| `VAD070358684` = AVTEX FIBERS INC, FRONT ROYAL VA | UCD 2011 study, Task 4 |
| AVTEX contaminants include STYRENE                | UCD 2011 study, Task 4 |

---

## 10. Documentation Standards

### When documentation is required

| Change                     | Required docs update                                              |
|----------------------------|-------------------------------------------------------------------|
| New API endpoint           | Add to `TOXMAP_API_CONTRACT.md` (RFC required)                    |
| New functional requirement | Add to `TOXMAP_TECH_STACK_ANALYSIS.md §3` (RFC required)          |
| New optional data layer    | Update data sources table in `TOXMAP_TECH_STACK_ANALYSIS.md §2.2` |
| New Gherkin scenario       | Update `TOXMAP_ACCEPTANCE_TESTS.md` (RFC required)                |
| New roadmap story          | Update `TOXMAP_DEVELOPMENT_ROADMAP.md` (maintainer only)          |
| New seed record            | Update `TOXMAP_TEST_SEED_DATA.md`                                 |

### Inline code documentation

```python
async def get_facilities_near(
    lat: float,
    lon: float,
    radius_miles: float,
    session: AsyncSession,
) -> list[Facility]:
    """
    Returns TRI facilities within radius_miles of the given coordinates.

    Uses PostGIS ST_DWithin with EPSG:3857 reprojection for accurate
    distance calculation in meters.

    Args:
        lat: Center latitude (WGS84)
        lon: Center longitude (WGS84)
        radius_miles: Search radius. Max 500 per API contract.
        session: Async SQLAlchemy session

    Returns:
        List of Facility ORM objects within the radius.
        Returns empty list (not None) if no facilities found.
    """
```

---

## 11. Dependency Policy

### Adding a new dependency

Before adding a `pip install` or `npm install`:

1. **Check for CVEs** using `pip-audit` or `npm audit`
2. **Check the license** — MIT, Apache 2.0, BSD are acceptable; GPL and AGPL require maintainer discussion
3. **Check the bundle size impact** (npm only): use `bundlephobia.com`
4. **Add to PR description** with justification: what problem does this library solve that the existing stack cannot?
5. Use exact version pinning in `pyproject.toml` / `package.json`

### Updating existing dependencies

- Minor + patch updates: PR with `chore(deps):` commit type, no review required if CI passes
- Major version updates: require maintainer review; check for breaking changes

### Banned packages

| Package                              | Reason                                         |
|--------------------------------------|------------------------------------------------|
| `mapbox-gl` (Mapbox proprietary v3+) | Proprietary license; use `maplibre-gl` instead |
| `react-google-maps`                  | Requires Google API key; $0 budget constraint  |
| Any ESRI SDK                         | Proprietary; ADR-001 explicitly rejects ESRI   |

---

## 12. First-Time Contributors

Not sure where to start? Look for issues labeled:

- `good-first-issue` — small, self-contained, well-documented
- `test-needed` — add a Gherkin step implementation for an existing scenario
- `docs` — documentation improvements
- `Phase 0` — infrastructure setup stories (no domain knowledge required)

**Recommended first contribution path:**
1. Get the Docker stack running locally (§2)
2. Run the test suite — see which scenarios are skipped or failing
3. Pick one `@pytest.mark.skip` step in `tests/steps/api_steps.py` and implement it
4. Open a PR — the CI will confirm whether your implementation is correct

**Getting help:**
- Open a `[question]` issue — maintainers respond within 3 business days
- Check the Q&A tab on existing closed issues first

---

*Thank you for helping make environmental health data accessible to everyone.*

