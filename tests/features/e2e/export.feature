# Export Feature (Epic 6.EXPORT)
# Data export functionality for TRI facilities, Superfund sites, and map screenshots.
# Full spec: docs/product/TOXMAP_PROGRESS_TRACKER.md Epic 6.EXPORT
Feature: Data Export

  Background:
    Given the application is running at "http://localhost:3000"
    And the seed database is loaded

  # ── Story 6.EXPORT.1–4: ResultsTable CSV Export ────────────────────────────

  @export @csv
  Scenario: Export search results as CSV
    Given I am on the map page
    When I perform a search for "LEAD COMPOUNDS" near "Sparrows Point, MD"
    Then the search results panel is visible
    And a CSV export button with test ID "export-csv-btn" is visible
    When I click the CSV export button
    Then a CSV file is downloaded

  @export @csv
  Scenario: Export button disabled during loading
    Given I am on the map page
    When I perform a search for "BENZENE" near "Houston, TX"
    And I click the CSV export button while it is loading
    Then no duplicate download is triggered

  # ── Story 6.EXPORT.5–6: FacilityDrawer Single-Facility Export ──────────────

  @export @csv @drawer
  Scenario: Export single facility releases as CSV
    Given I am on the map page
    When I perform a search for "LEAD COMPOUNDS" near "Sparrows Point, MD"
    And I click on a facility marker
    And the facility detail drawer opens
    Then a CSV export button with test ID "facility-export-btn" is visible in the drawer header
    When I click the facility export button
    Then a CSV file is downloaded containing facility release history

  # ── Story 6.EXPORT.7–8: Map Screenshot Export ─────────────────────────────

  @export @screenshot
  Scenario: Export map view as PNG screenshot
    Given I am on the map page
    Then the map screenshot button with test ID "map-screenshot-btn" is visible
    When I click the map screenshot button
    Then a PNG image is downloaded
    And the PNG contains OSM attribution watermark

  # ── Story 6.EXPORT.9–10: Superfund Contaminants Export ─────────────────────

  @export @csv @superfund
  Scenario: Export Superfund site contaminants as CSV
    Given I am on the map page
    And the Superfund layer is visible
    When I click on a Superfund site marker
    And the Superfund detail drawer opens with contaminants
    Then a CSV export button with test ID "superfund-export-btn" is visible
    When I click the Superfund export button
    Then a CSV file is downloaded containing site contaminants

  @export @csv @superfund
  Scenario: Superfund export button hidden when no contaminants
    Given I am on the map page
    And I open a Superfund site with no contaminants
    Then no CSV export button is visible in the Superfund drawer

  # ── Regression Tests (Defects Fixed 2026-08-08) ────────────────────────────

  @export @csv @regression @6.EXPORT.16
  Scenario: Nationwide search CSV export returns data (non-spatial browse)
    # Regression: Empty CSV when searching by state without map location
    # Root cause: /api/v1/export/csv required lat/lon; frontend fell back to Kansas center
    # Fix: Added /api/v1/export/csv/browse endpoint without spatial constraint
    Given I am on the map page
    When I select "TRI" dataset
    And I filter to state "NJ"
    And I search for "LEAD" without specifying a location
    Then the search results show facilities in NJ
    When I click the CSV export button
    Then the downloaded CSV is not empty
    And the CSV contains rows with state "NJ"

  @export @screenshot @regression @6.EXPORT.17
  Scenario: Map screenshot produces non-blank PNG
    # Regression: Blank screenshot due to WebGL buffer clearing
    # Root cause: WebGL clears drawing buffer after each frame render
    # Fix: Added preserveDrawingBuffer={true} to MapLibre Map component
    Given I am on the map page
    And the map has finished loading tiles
    When I click the map screenshot button
    Then the downloaded PNG has file size greater than 10KB
    And the PNG is not blank (contains pixel data)
