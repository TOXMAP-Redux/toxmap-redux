# TOXMAP — How to Run Tests

**Last Updated:** 2026-07-30  
**Related Docs:** [TOXMAP_TESTING_STRATEGY.md](TOXMAP_TESTING_STRATEGY.md) · [TOXMAP_TEST_PLAN_LAYER5_E2E.md](TOXMAP_TEST_PLAN_LAYER5_E2E.md)

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Environment Setup](#2-environment-setup)
3. [Running Tests Locally](#3-running-tests-locally)
   - [Unit Tests (Layer 1)](#31-unit-tests-layer-1)
   - [API Contract Tests (Layer 4)](#32-api-contract-tests-layer-4)
   - [E2E Browser Tests (Layer 5)](#33-e2e-browser-tests-layer-5)
   - [Accessibility Tests](#34-accessibility-tests)
   - [Visual Regression Tests](#35-visual-regression-tests)
4. [CI/CD Pipeline (Headless)](#4-cicd-pipeline-headless)
5. [Test Execution Quick Reference](#5-test-execution-quick-reference)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Docker** + Docker Compose | v24+ | PostGIS database container |
| **Python** | 3.11+ | Backend, test runner (pytest) |
| **Node.js** | 24+ | Frontend dev server |
| **Playwright** | 1.40+ | Browser automation for E2E |

### Install Playwright Browsers (One-Time)

```bash
# From project root after pip install -e ".[dev]"
playwright install chromium firefox webkit
```

---

## 2. Environment Setup

### Step 1: Start the Docker Services

```bash
# Start PostGIS (database), backend (FastAPI), and frontend (Vite)
docker compose up -d

# Verify all services are healthy
docker compose ps
```

Expected output:
```
NAME              STATUS
toxmap-postgres   Up (healthy)   0.0.0.0:5433->5432/tcp
toxmap-backend    Up (healthy)   0.0.0.0:8000->8000/tcp
toxmap-frontend   Up             0.0.0.0:3000->3000/tcp
```

### Step 2: Seed the Database

The E2E tests require deterministic seed data from `tests/fixtures/seed.sql`:

```bash
# Copy and execute seed file
docker cp tests/fixtures/seed.sql toxmap-postgres:/tmp/seed.sql
docker exec toxmap-postgres psql -U postgres -d toxmap -f /tmp/seed.sql
```

Verify seed data loaded:
```bash
docker exec toxmap-postgres psql -U postgres -d toxmap -c \
  "SELECT COUNT(*) as facilities FROM facilities; SELECT COUNT(*) as superfund FROM superfund_sites;"
```

Expected: `15` facilities, `2` Superfund sites (or similar based on current seed.sql).

### Step 3: Verify Backend Health

```bash
curl -s http://localhost:8000/api/v1/health | jq
```

Expected: `{"status": "healthy", "database": "connected"}`

### Step 4: Verify Frontend

Open http://localhost:3000 in a browser. The map should load with TRI markers visible.

---

## 3. Running Tests Locally

All test commands assume you're in the project root directory.

### 3.1 Unit Tests (Layer 1)

Unit tests run without external services (no Docker required).

```bash
# Run all unit tests
PYTHONPATH=.:backend pytest tests/unit/ -v

# Run with coverage
PYTHONPATH=.:backend pytest tests/unit/ -v --cov=backend/app --cov-report=term-missing

# Run a specific test file
PYTHONPATH=.:backend pytest tests/unit/test_schemas.py -v
```

**Timing:** ~5-10 seconds

---

### 3.2 API Contract Tests (Layer 4)

Requires PostGIS + FastAPI running (see [Environment Setup](#2-environment-setup)).

```bash
# Run all API Gherkin feature tests
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/api/ -v --tb=short

# Run a specific endpoint's tests
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/api/ -v -k "facilities"
```

**Timing:** ~30-60 seconds

---

### 3.3 E2E Browser Tests (Layer 5)

Requires the **full stack** running: PostGIS + FastAPI + Frontend (see [Environment Setup](#2-environment-setup)).

#### Headed Mode (Watch the Browser)

Use `--headed` to see the browser window during test execution:

```bash
# Run ALL E2E tests with visible browser
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/e2e/ -v --tb=short --headed

# Run only UCD task scenarios
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/e2e/test_ucd_task_scenarios.py -v --headed

# Run only UX invariant tests
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/e2e/test_ux_invariants.py -v --headed
```

#### Headless Mode (Default)

Omit `--headed` for headless execution (faster, no visible browser):

```bash
# Headless E2E (default)
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/e2e/ -v --tb=short
```

#### Run Specific Scenarios

```bash
# T-01: Lead compounds near Sparrows Point MD
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/e2e/ -v -k "t01" --headed

# T-07: Largest chlorine release
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/e2e/ -v -k "t07" --headed

# All invariants only
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/e2e/test_ux_invariants.py -v --headed

# Specific invariant (e.g., Invariant 8: comma formatting)
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/e2e/ -v -k "commaformatted" --headed
```

#### Cross-Browser Testing

```bash
# Run with Firefox instead of Chromium
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/e2e/ -v --browser firefox

# Run with WebKit (Safari engine)
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/e2e/ -v --browser webkit
```

**Timing:** ~2-3 minutes for full suite (41 tests)

---

### 3.4 Accessibility Tests

WCAG 2.1 AA compliance tests using axe-core:

```bash
# Run accessibility tests
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/a11y/ -v --headed
```

**Test file:** `tests/a11y/test_wcag_compliance.py`

---

### 3.5 Visual Regression Tests

Pixel-diff tests for UI consistency:

```bash
# Run visual regression tests (generates snapshots on first run)
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/visual/ -v --headed
```

**Test file:** `tests/visual/test_visual_regression.py`  
**Snapshots:** `tests/visual/snapshots/`  
**Diffs:** `tests/visual/diffs/`

---

## 4. CI/CD Pipeline (Headless)

The CI pipeline (`.github/workflows/ci.yml`) runs all tests in **headless mode** automatically.

### How CI Runs E2E Tests

```yaml
# From ci.yml - E2E job configuration
- name: Install Playwright browsers
  run: playwright install --with-deps chromium firefox

- name: Run UX invariant E2E tests (Chromium)
  run: |
    pytest tests/features/e2e/ux_invariants.feature -v --tb=short \
      --browser chromium \
      --junitxml=reports/e2e-invariants-chromium.xml
  env:
    DATABASE_URL_SYNC: postgresql+psycopg2://postgres:postgres@localhost:5432/toxmap

- name: Run UCD task scenario E2E tests (Chromium)
  run: |
    pytest tests/features/e2e/ucd_task_scenarios.feature -v --tb=short \
      --browser chromium \
      --junitxml=reports/e2e-ucd-chromium.xml

- name: Run E2E smoke tests (Firefox)
  run: |
    pytest tests/features/e2e/ -v --tb=short \
      --browser firefox \
      -k "T-01 or Invariant_1" \
      --junitxml=reports/e2e-smoke-firefox.xml
```

### Key CI Configuration Details

| Setting | Value | Notes |
|---------|-------|-------|
| **Default browser** | Chromium | Headless, no `--headed` flag |
| **Cross-browser** | Firefox smoke tests | Subset of tests for coverage |
| **Database** | PostGIS service container | Port 5432 (not 5433) |
| **Playwright install** | `--with-deps` | Installs system dependencies |
| **Artifacts** | JUnit XML reports | Uploaded for test result visualization |

### Headless vs. Headed Summary

| Mode | Flag | Use Case |
|------|------|----------|
| **Headless** | *(default)* | CI/CD, automated runs, faster |
| **Headed** | `--headed` | Local debugging, watching test execution |

---

## 5. Test Execution Quick Reference

### One-Liner Commands

```bash
# ─── Unit Tests (no Docker) ───────────────────────────────────────────────────
PYTHONPATH=.:backend pytest tests/unit/ -v

# ─── API Tests (requires PostGIS + Backend) ───────────────────────────────────
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/api/ -v

# ─── E2E Tests (requires full stack) ──────────────────────────────────────────
# Headless (CI style)
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/e2e/ -v

# Headed (debugging)
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/e2e/ -v --headed

# ─── Smoke Tests Only (fast) ──────────────────────────────────────────────────
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/features/e2e/ -v -k "t01 or t03 or t08" --headed

# ─── All Tests (full suite) ───────────────────────────────────────────────────
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5433/toxmap" \
  PYTHONPATH=.:backend pytest tests/ -v --ignore=tests/benchmarks --ignore=tests/security
```

### Test Coverage by Category

| Category | Test Count | Location | Requires |
|----------|------------|----------|----------|
| **Unit** | ~20+ | `tests/unit/` | Python only |
| **API Contract** | ~40+ | `tests/features/api/` | PostGIS + Backend |
| **E2E UCD Tasks** | 16 | `tests/features/e2e/test_ucd_task_scenarios.py` | Full stack |
| **E2E UX Invariants** | 25 | `tests/features/e2e/test_ux_invariants.py` | Full stack |
| **Accessibility** | 3+ | `tests/a11y/` | Full stack |
| **Visual** | 3+ | `tests/visual/` | Full stack |

---

## 6. Troubleshooting

### Problem: "Playwright browser not found"

```bash
# Solution: Install browsers
playwright install chromium firefox webkit
```

### Problem: "Connection refused on port 5433"

The PostGIS container isn't running or uses a different port.

```bash
# Check container status
docker compose ps

# Restart services
docker compose down -v && docker compose up -d
```

### Problem: "No results to verify" / Empty Seed Data

The database wasn't seeded properly.

```bash
# Re-seed the database
docker exec toxmap-postgres psql -U postgres -d toxmap -c "TRUNCATE facilities, superfund_sites, chemicals RESTART IDENTITY CASCADE;"
docker cp tests/fixtures/seed.sql toxmap-postgres:/tmp/seed.sql
docker exec toxmap-postgres psql -U postgres -d toxmap -f /tmp/seed.sql
docker restart toxmap-backend
```

### Problem: Tests Timeout Waiting for Map

The frontend or backend may not be fully ready.

```bash
# Check backend health
curl http://localhost:8000/api/v1/health

# Check frontend
curl -I http://localhost:3000

# Restart if needed
docker compose restart backend frontend
```

### Problem: "blocked by sandbox" on macOS

Playwright Chromium may be blocked by macOS Gatekeeper.

```bash
# Option 1: Run outside VS Code terminal
# Open Terminal.app and run the pytest command there

# Option 2: Use headed mode (often bypasses the issue)
pytest tests/features/e2e/ -v --headed

# Option 3: Use Firefox instead
pytest tests/features/e2e/ -v --browser firefox
```

### Problem: Flaky Tests / Timing Issues

Tests use condition-based waits, but complex UI operations may occasionally timeout.

```bash
# Add reruns for flaky test mitigation
pip install pytest-rerunfailures
pytest tests/features/e2e/ -v --reruns 2 --reruns-delay 1
```

---

## Appendix: Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL_SYNC` | (required) | PostgreSQL connection string for sync driver |
| `PYTHONPATH` | `.:backend` | Ensures imports resolve correctly |
| `BASE_URL` | `http://localhost:3000` | Frontend URL for Playwright |
| `TESTING` | `1` | Enables test mode in FastAPI |

---

## See Also

- [TOXMAP_TESTING_STRATEGY.md](TOXMAP_TESTING_STRATEGY.md) — Testing goals and architecture
- [TOXMAP_TEST_PLAN_LAYER5_E2E.md](TOXMAP_TEST_PLAN_LAYER5_E2E.md) — Detailed E2E test plan
- [TOXMAP_TEST_SEED_DATA.md](TOXMAP_TEST_SEED_DATA.md) — Seed data specifications
- [TEST_ID_REGISTRY.md](TEST_ID_REGISTRY.md) — `data-testid` attribute registry
