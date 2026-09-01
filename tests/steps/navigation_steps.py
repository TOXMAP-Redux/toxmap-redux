# tests/steps/navigation_steps.py
"""
Navigation and background step implementations for E2E tests.

Covers:
- Application startup (given steps)
- Map page navigation
- Banner dismissal
"""

from pytest_bdd import given
from playwright.sync_api import Page

from ._shared import (
    BASE_URL,
    MAP_TIMEOUT,
    dismiss_banner_if_present,
)


@given('the application is running at "http://localhost:3000"')
def app_running() -> None:
    """No-op: the running app is a precondition, not something we start in tests."""


@given('the seed database is loaded', target_fixture='seed_db_loaded')
def seed_database_loaded(seed_db) -> None:  # noqa: ARG001
    """Triggers the session-scoped seed_db fixture to ensure data is seeded."""


@given('I am on the map page')
def i_am_on_map_page(page: Page) -> None:
    """Navigate to the TOXMAP app and wait for the map container to be ready."""
    page.goto(BASE_URL)
    page.wait_for_selector('[data-testid="map-container"]', timeout=MAP_TIMEOUT)
    dismiss_banner_if_present(page)


@given('I am on the map page in browse mode')
def i_am_on_map_page_browse(page: Page) -> None:
    """Navigate to the map page (default state shows MapContentsPanel)."""
    page.goto(BASE_URL)
    page.wait_for_selector('[data-testid="map-container"]', timeout=MAP_TIMEOUT)
    dismiss_banner_if_present(page)
