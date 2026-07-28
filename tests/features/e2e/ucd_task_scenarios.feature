# UCD 2011 Task Scenarios
# Full spec: docs/testing/TOXMAP_ACCEPTANCE_TESTS.md Feature 7
# Phase 3: T-01, T-03, T-08 implemented
# Phase 4: T-02, T-04 (Superfund overlay required)
# Phase 5: T-05, T-06, T-09 (Demographics overlay required)
Feature: UCD 2011 Task Scenarios

  Background:
    Given the application is running at "http://localhost:3000"
    And the seed database is loaded

  # ── T-01 (Phase 3) ────────────────────────────────────────────────────────

  Scenario: T-01 Lead compounds near Sparrows Point MD
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I type "LEAD COMPOUNDS" into the chemical field
    And I select year "2008"
    And I click "Search"
    Then the results sidebar shows "BETHLEHEM STEEL CORP - SPARROWS POINT"
    When I click on "BETHLEHEM STEEL CORP - SPARROWS POINT" in the results
    Then the facility detail panel opens
    And the detail panel shows "12,485 lbs"
    And the release quantities are formatted with commas

  # ── T-03 (Phase 3) ────────────────────────────────────────────────────────

  Scenario: T-03 Copper releases near Ely Nevada
    Given I am on the map page
    When I type "Ruth, NV" into the location field
    And I type "COPPER" into the chemical field
    And I select year "2008"
    And I click "Search"
    Then the results sidebar shows "ROBINSON NEVADA MINING CO"
    When I click on "ROBINSON NEVADA MINING CO" in the results
    Then the facility detail panel opens
    And the detail panel shows "8,205 lbs"

  # ── T-08 (Phase 3) ────────────────────────────────────────────────────────

  Scenario: T-08 ATSDR ToxFAQ link opens in new tab preserving map state
    Given I am on the map page
    When I type "AMMONIA" into the chemical field
    And I select the chemical "AMMONIA" from autocomplete
    Then the ATSDR link is visible for the selected chemical
    And the ATSDR link opens in a new tab

  # ── T-02 (Phase 4 — Superfund overlay) ───────────────────────────────────

  Scenario: T-02 Superfund chemical list accessible within 2 clicks
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    Then the results sidebar shows "AVTEX FIBERS INC"
    When I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    And the contaminants list is visible

  # ── T-04 (Phase 4 — Superfund overlay) ───────────────────────────────────

  Scenario: T-04 Styrene Superfund site found near Front Royal VA
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    Then the results sidebar shows "AVTEX FIBERS INC"
    When I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    And the contaminants list contains "STYRENE"
    And the EPA site progress profile link is present

  # ── T-05 (Phase 5 — Demographics) ────────────────────────────────────────
  @skip
  Scenario: T-05 TRI styrene sites and under-18 demographic overlay
    Given I open the TOXMAP application
    Then a demographics scenario stub exists

  # ── T-06 (Phase 5 — Demographics) ────────────────────────────────────────
  @skip
  Scenario: T-06 Income demographic layer applied
    Given I open the TOXMAP application
    Then a demographics scenario stub exists

  # ── T-07 (Phase 3 — API verified; E2E optional) ───────────────────────────
  @skip
  Scenario: T-07 Largest chlorine release SC vs nationwide
    Given I open the TOXMAP application
    Then a chlorine scenario stub exists

  # ── T-09 (Phase 5 — Demographics) ────────────────────────────────────────
  @skip
  Scenario: T-09 Benzene releases and cancer mortality co-occurrence
    Given I open the TOXMAP application
    Then a demographics scenario stub exists

