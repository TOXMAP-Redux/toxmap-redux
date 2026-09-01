# tests/steps/export_steps.py
"""
Export functionality step implementations for E2E tests.

Covers:
- CSV download (results export)
- Map screenshot (PNG export)
- File download verification
"""

from pytest_bdd import when, then, parsers
from playwright.sync_api import Page, expect

from ._shared import (
    MAP_TIMEOUT,
    DOWNLOAD_TIMEOUT,
)


# ── Map screenshot ────────────────────────────────────────────────────────────


@then('the map screenshot button is visible')
def map_screenshot_button_visible(page: Page) -> None:
    """6.EXPORT.7: Verify the map screenshot button is rendered on the page."""
    btn = page.locator('[data-testid="map-screenshot-btn"]')
    expect(btn).to_be_visible()


@then('the map screenshot button is enabled')
def map_screenshot_button_enabled(page: Page) -> None:
    """6.EXPORT.7: Verify the map screenshot button is not disabled."""
    btn = page.locator('[data-testid="map-screenshot-btn"] button')
    expect(btn).to_be_enabled()


@when('I click the map screenshot button')
def click_map_screenshot_button(page: Page) -> None:
    """6.EXPORT.8: Click the map screenshot button to trigger download."""
    btn = page.locator('[data-testid="map-screenshot-btn"] button')
    expect(btn).to_be_enabled(timeout=MAP_TIMEOUT)
    btn.click()


@then('a PNG file is downloaded')
def png_file_downloaded(page: Page) -> None:
    """6.EXPORT.8: Verify that clicking screenshot triggers a PNG download."""
    btn = page.locator('[data-testid="map-screenshot-btn"] button')
    with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_info:
        btn.click()
    download = download_info.value
    filename = download.suggested_filename
    assert filename.endswith('.png'), f'Expected PNG file, got: {filename}'


@then(parsers.parse('the downloaded file name contains "{substring}"'))
def downloaded_filename_contains(page: Page, substring: str) -> None:
    """6.EXPORT.8: Verify downloaded filename contains expected substring."""
    btn = page.locator('[data-testid="map-screenshot-btn"] button')
    with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_info:
        btn.click()
    download = download_info.value
    filename = download.suggested_filename
    assert substring.lower() in filename.lower(), (
        f'Expected filename containing "{substring}", got: {filename}'
    )


# ── CSV export (future) ───────────────────────────────────────────────────────
# These steps will be implemented when CSV export functionality is added


@when('I click the export to CSV button')
def click_export_csv_button(page: Page) -> None:
    """Click the CSV export button (future functionality)."""
    btn = page.locator('[data-testid="export-csv-btn"]')
    expect(btn).to_be_visible()
    btn.click()


@then('a CSV file is downloaded')
def csv_file_downloaded(page: Page) -> None:
    """Verify that CSV export triggers a file download."""
    btn = page.locator('[data-testid="export-csv-btn"]')
    with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_info:
        btn.click()
    download = download_info.value
    filename = download.suggested_filename
    assert filename.endswith('.csv'), f'Expected CSV file, got: {filename}'
