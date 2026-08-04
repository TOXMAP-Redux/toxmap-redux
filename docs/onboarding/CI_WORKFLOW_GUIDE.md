# CI Workflow Guide

> **Audience:** New contributors and maintainers  
> **Last Updated:** 2026-08-04

This document explains the TOXMAP continuous integration (CI) workflow, what each job does, and how to interpret the artifacts it produces.

---

## Overview

The CI workflow (`.github/workflows/ci.yml`) runs automatically on:
- Every push to `main`
- Every pull request targeting `main`

It implements **5 quality gates** defined in [CONTRIBUTING.md §6](../../CONTRIBUTING.md):

| Gate | Name | Required When | Job |
|------|------|---------------|-----|
| 1 | Unit Tests | Always | `python-unit` |
| 2 | API Contract Tests | Backend changes | `python-api` |
| 3 | E2E / UX Invariants | Frontend changes | `e2e` |
| 4 | Scenario-specific | Story closes a Gherkin scenario | `e2e` |
| 5 | Performance Benchmarks | Query/render-path changes | `benchmarks` |

---

## Job Dependency Graph

```
┌─────────────────┐     ┌─────────────────────────┐
│  python-lint    │     │  frontend-lint          │
│  (ruff, mypy)   │     │ (Prettier, ESLint, tsc) │
└────────┬────────┘     └────────┬────────────────┘
         │                       │
         ▼                       │
┌─────────────────┐              │
│  python-unit    │              │
│  (Gate 1)       │              │
└────────┬────────┴──────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  python-api     │     │      e2e        │
│  (Gate 2)       │     │  (Gate 3 + 4)   │
└─────────────────┘     └─────────────────┘

         │
         ▼
┌─────────────────┐
│   benchmarks    │  ← Only on PRs
│   (Gate 5)      │
└─────────────────┘
```

---

## Jobs Explained

### 1. `python-lint` — Code Quality Checks

**Purpose:** Catch formatting and type errors before running any tests.

| Step | Tool | What It Checks |
|------|------|----------------|
| `ruff format --check` | Ruff | Python code formatting (PEP 8 style) |
| `ruff check` | Ruff | Python linting (unused imports, complexity, etc.) |
| `mypy` | Mypy | Static type checking for `app/` and `ingestion/` |

**Fix failures locally:**
```bash
cd backend
ruff format .          # Auto-fix formatting
ruff check --fix .     # Auto-fix lint issues
mypy app ingestion     # Check types
```

---

### 2. `python-unit` — Unit Tests (Gate 1)

**Purpose:** Run fast, isolated unit tests with no external dependencies.

**What runs:** `pytest tests/unit/` with coverage reporting.

**Artifacts produced:**
- `unit-test-results/unit-results.xml` — JUnit XML test report
- `unit-test-results/coverage.xml` — Code coverage data (uploaded to Codecov)

**Run locally:**
```bash
cd backend
pytest ../tests/unit/ -v --cov=app --cov-report=term-missing
```

---

### 3. `python-api` — API Contract Tests (Gate 2)

**Purpose:** Verify API endpoints match the contract in `TOXMAP_API_CONTRACT.md`.

**Services required:** PostGIS 16 database container.

**What runs:**
1. Alembic migrations (`alembic upgrade head`)
2. Load seed data (`psql -f tests/fixtures/seed.sql`)
3. Start FastAPI server in background
4. Run Gherkin feature tests (`pytest tests/features/api/`)
5. Run Schemathesis contract validation

**Artifacts produced:**
- `api-test-results/api-results.xml` — API test results
- `api-test-results/schemathesis.txt` — OpenAPI contract validation report

**Run locally:**
```bash
# Start local PostGIS
docker compose up -d postgres

# Run API tests
cd backend
pytest ../tests/features/api/ -v

# Run Schemathesis
pip install schemathesis
schemathesis run http://localhost:8000/openapi.json --checks all
```

---

### 4. `frontend-lint` — Frontend Code Quality

**Purpose:** Ensure TypeScript code is formatted, linted, and type-safe.

| Step | Tool | What It Checks |
|------|------|----------------|
| `prettier --check` | Prettier | Code formatting (JS/TS/CSS) |
| `eslint` | ESLint | Code quality, best practices |
| `tsc --noEmit` | TypeScript | Type checking |

**Fix failures locally:**
```bash
cd frontend
npx prettier --write src/    # Auto-fix formatting
npx eslint src/ --fix        # Auto-fix lint issues
npx tsc --noEmit             # Check types
```

---

### 5. `e2e` — End-to-End Tests (Gate 3 + Gate 4)

**Purpose:** Test the full application stack in a browser using Playwright.

**Services required:** Full Docker Compose stack (backend + frontend + PostGIS).

**What runs:**
1. Start Docker Compose stack
2. Load seed data
3. Run UX invariant tests (Chromium) — Gate 3
4. Run UCD task scenario tests (Chromium) — Gate 4
5. Run smoke tests (Firefox) — Cross-browser validation

**Artifacts produced:**
- `e2e-test-results/e2e-invariants-chromium.xml` — UX invariant results
- `e2e-test-results/e2e-ucd-chromium.xml` — UCD task scenario results
- `e2e-test-results/e2e-smoke-firefox.xml` — Firefox smoke test results

**Run locally:**
```bash
# Start full stack
docker compose up -d

# Install Playwright
cd backend
playwright install chromium

# Run E2E tests
pytest ../tests/features/e2e/ux_invariants.feature -v --browser chromium
pytest ../tests/features/e2e/ucd_task_scenarios.feature -v --browser chromium
```

---

### 6. `benchmarks` — Performance Benchmarks (Gate 5)

**Purpose:** Detect performance regressions in query and render paths.

**When it runs:** Only on pull requests (not pushes to main).

**What runs:**
1. Start PostGIS database
2. Run migrations and load seed data
3. Run `pytest tests/benchmarks/` with benchmark comparison
4. Fail if p95 latency increases by more than 20%

**Artifacts produced:**
- `benchmark-results/.benchmarks/` — Benchmark history for comparison

**Run locally:**
```bash
cd backend
pytest ../tests/benchmarks/ --benchmark-only
```

---

## Understanding Artifacts

GitHub Actions artifacts are files produced during CI that you can download for debugging.

### How to Access Artifacts

1. Go to **Actions** tab in the GitHub repository
2. Click on the workflow run you want to inspect
3. Scroll to the **Artifacts** section at the bottom
4. Click on an artifact name to download

### Artifact Contents

| Artifact | Contents | Use Case |
|----------|----------|----------|
| `unit-test-results` | `unit-results.xml`, `coverage.xml` | Debug failing unit tests, view code coverage |
| `api-test-results` | `api-results.xml`, `schemathesis.txt` | Debug API failures, check OpenAPI contract violations |
| `e2e-test-results` | Multiple JUnit XML files | Debug E2E failures, check UX invariant violations |
| `benchmark-results` | `.benchmarks/` directory | Compare performance across commits |

### Interpreting JUnit XML

The `*-results.xml` files are in JUnit format. You can:
- Open them in VS Code with a JUnit extension
- View them in GitHub's **Summary** tab (auto-parsed)
- Use tools like `junit2html` to generate HTML reports

---

## Troubleshooting

### CI is Red — What Do I Do?

1. **Check the job that failed** — Click on the red X in the GitHub Actions run
2. **Read the error message** — Expand the failing step
3. **Download artifacts** — Get detailed test reports
4. **Reproduce locally** — Use the "Run locally" commands above

### Common Failures

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `python-lint` fails | Code not formatted | Run `ruff format backend/` |
| `python-unit` fails | Test assertion error | Check `unit-results.xml` for details |
| `python-api` fails | API shape mismatch | Compare response to `TOXMAP_API_CONTRACT.md` |
| `frontend-lint` fails | TypeScript error | Run `npx tsc --noEmit` locally |
| `e2e` fails | UI element not found | Check if `data-testid` attributes are present |
| `benchmarks` fails | Performance regression | Profile the slow query/component |

### Flaky Tests

If a test passes locally but fails in CI (or vice versa):
1. Check for timing issues (add explicit waits in E2E tests)
2. Check for environment differences (CI uses Ubuntu, you may use macOS)
3. Check for missing seed data (CI loads `tests/fixtures/seed.sql`)

---

## Security: Action Pinning

All third-party GitHub Actions are pinned to full 40-character SHA hashes, not version tags. This prevents supply chain attacks where a malicious actor could hijack a tag.

Example:
```yaml
# ✅ Good — pinned to SHA
uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # v5.1.0

# ❌ Bad — mutable tag
uses: actions/checkout@v4
```

See [docs/security/PINNED_ACTIONS.md](../security/PINNED_ACTIONS.md) for the full list of verified SHA → tag mappings.

---

## Related Documentation

- [CONTRIBUTING.md §6](../../CONTRIBUTING.md) — CI gate requirements
- [TOXMAP_ACCEPTANCE_TESTS.md](../testing/TOXMAP_ACCEPTANCE_TESTS.md) — Gherkin scenarios
- [TOXMAP_API_CONTRACT.md](../api/TOXMAP_API_CONTRACT.md) — API specification
- [TEST_ID_REGISTRY.md](../testing/TEST_ID_REGISTRY.md) — Playwright `data-testid` values
