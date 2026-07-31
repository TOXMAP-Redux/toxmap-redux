# tests/conftest.py
#
# pytest fixtures for all TOXMAP test layers.
#
# ── Driver note (M-6) ─────────────────────────────────────────────────────────
# Tests use psycopg2 (SYNCHRONOUS) for fixture setup and teardown.
# The FastAPI application uses asyncpg (ASYNC) via SQLAlchemy 2.0 async engine.
# These are two independent connection pools — psycopg2 is used ONLY in conftest.py.
# Both drivers are needed: asyncpg cannot execute raw DDL-containing seed SQL blocks,
# and psycopg2 is not compatible with FastAPI's async context.
# See pyproject.toml [project.optional-dependencies] test group for psycopg2-binary.
#
# ── Thread safety (9.5) ───────────────────────────────────────────────────────
# Tests MUST run single-threaded. Do NOT use pytest-xdist (-n auto).
# The session-scoped db_connection is shared across function-scoped seed_db fixtures.
# Parallel execution would cause TRUNCATE races and corrupt test state.
# The pyproject.toml [tool.pytest.ini_options] addopts = "-p no:xdist" enforces this.
# ─────────────────────────────────────────────────────────────────────────────

import os
# M-12: Set TESTING=1 before any app module is imported. database.py reads this
# at module-load time to select NullPool — prevents asyncpg connections created
# in one event loop from being reused in another ("attached to different loop").
os.environ["TESTING"] = "1"
import pytest
import psycopg2
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import create_app

# M-4: use explicit env var instead of undefined get_db_url() function.
# Strip SQLAlchemy driver prefix (+psycopg2) if present — psycopg2.connect()
# uses libpq DSN format (postgresql://...) not SQLAlchemy URL format.
_raw_db_url = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://postgres:postgres@localhost:5432/toxmap"
)
DATABASE_URL_SYNC = _raw_db_url.replace("+psycopg2", "")

SEED_SQL = Path(__file__).parent / "fixtures" / "seed.sql"


@pytest.fixture(scope="session")
def db_connection():
    conn = psycopg2.connect(DATABASE_URL_SYNC)
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def seed_db(db_connection):
    """Load seed data before each test; remove only seed rows after.

    Teardown removes ONLY the rows inserted by seed.sql (identified by their
    explicit seed IDs / tri_facility_ids), so that real ingested data in the
    shared toxmap database is not wiped between test runs.

    NOTE: seed.sql now does its own DELETE of these same rows before INSERT,
    making the script idempotent. This teardown provides cleanup after test
    completion so the database returns to its pre-test state.
    """
    with db_connection.cursor() as cur:
        cur.execute(SEED_SQL.read_text())
    db_connection.commit()
    yield
    # Remove only the seed rows (not real ingested data).
    # These MUST match the facility IDs in tests/fixtures/seed.sql exactly.
    _seed_facility_ids = [
        '21219BTHLS3RD',   # Bethlehem Steel (T-01)
        '89319BHPCP7MILE', # Robinson Nevada (T-03)
        '22630FRTRY0001',  # Front Royal Plastics
        '29801DSTLR0001',  # Borden Chemicals
        '70663ENTGR0001',  # Enterprise Gas
        '77536EXXO00001',  # ExxonMobil
        '77536LYND00001',  # LyondellBasell
        '99501ANCHO0001',  # Alaska Mining (CONUS filter test)
        '22630SMRLG0001',  # Small Release Facility (green tier test)
    ]
    # Seed EPA IDs for Superfund (T-04, UCD-17 all 3 status types):
    _seed_epa_ids = ['VAD070358684', 'VAD980554587', 'VAD987654321', 'VAD123456789']
    # Seed FIPS codes for census (T-05):
    _seed_fips = ['51187', '48201', '45003']
    with db_connection.cursor() as cur:
        if _seed_facility_ids:
            cur.execute(
                "DELETE FROM release_events WHERE facility_id IN "
                "(SELECT id FROM facilities WHERE tri_facility_id = ANY(%s))",
                (_seed_facility_ids,)
            )
            cur.execute(
                "DELETE FROM facilities WHERE tri_facility_id = ANY(%s)",
                (_seed_facility_ids,)
            )
        if _seed_epa_ids:
            cur.execute(
                "DELETE FROM superfund_sites WHERE epa_id = ANY(%s)",
                (_seed_epa_ids,)
            )
        if _seed_fips:
            cur.execute(
                "DELETE FROM census_county WHERE fips_code = ANY(%s)",
                (_seed_fips,)
            )
    db_connection.commit()


@pytest.fixture(scope="session")
def api_client():
    app = create_app()
    return TestClient(app)


@pytest.fixture(scope="session")
def browser_base_url():
    # NOTE: pytest-playwright injects its own `base_url` from --base-url (set in pyproject.toml).
    # This fixture is provided for step helpers that cannot use pytest-playwright's page fixture
    # directly. Prefer page.goto("/") in E2E step functions rather than page.goto(browser_base_url)
    # to avoid constructing a double-path URL when --base-url is already set.
    return os.getenv("TEST_BASE_URL", "http://localhost:3000")


@pytest.fixture
def step_context():
    """Shared mutable dict for passing response state between pytest-bdd step functions.

    Named `step_context` (not `context`) to avoid shadowing pytest-playwright's built-in
    `context` fixture (BrowserContext). See V10-A in docs/audits/TOXMAP_AGENTIC_AUDIT_V10.md.

    Must be function-scoped (default) so each test scenario starts with a clean dict.
    Usage in steps: step_context["response"] = ...; assert step_context["response"].status_code == 200
    """
    return {}


def pytest_bdd_apply_tag(tag: str, function):
    """Auto-skip scenarios tagged with @skip in feature files.
    This allows future-phase scenario stubs to live in the feature file
    without breaking the current phase's test run.
    """
    if tag == 'skip':
        marker = pytest.mark.skip(reason='@skip-tagged scenario — not yet implemented in this phase')
        marker(function)
        return True
    return None
