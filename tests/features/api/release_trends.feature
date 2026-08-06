Feature: Release Trends

  Background:
    Given the seed database is loaded

  Scenario: T-07 — SC chlorine largest release
    When I GET "/api/v1/releases/largest?chemical=chlorine&state=SC&year=2008"
    Then the response status is 200
    And the response field "total_release_lbs" equals 85000.0

  Scenario: T-07 — Nationwide chlorine largest release
    When I GET "/api/v1/releases/largest?chemical=chlorine&year=2008"
    Then the response status is 200
    And the response field "total_release_lbs" equals 342500.0

  Scenario: Facility releases time series
    When I GET "/api/v1/facilities/89319BHPCP7MILE/releases?from_year=2006&to_year=2010"
    Then the response status is 200
    And the response is a JSON array
    And the first result field "chemical_name" equals "COPPER"

  # ── Regression: 7.BUG.29 — Facility detail top_chemicals all-years ──────────
  # CRITICAL FIX: Facility detail top_chemicals must aggregate across ALL years,
  # not just the latest year. The total_release_lbs in the detail response must
  # match the sum of all chemicals across all years.
  #
  # Test data: ExxonMobil (77536EXXO00001) has benzene releases in seed.sql:
  #   2006: 35,600 lbs | 2007: 31,200 lbs | 2008: 28,400 lbs → Total: 95,200 lbs

  Scenario: Regression 7.BUG.29 — Facility detail returns all-years total
    When I GET "/api/v1/facilities/77536EXXO00001"
    Then the response status is 200
    And the response field "total_release_lbs" equals 95200.0

  Scenario: Regression 7.BUG.29 — Facility detail top_chemicals sum matches total
    When I GET "/api/v1/facilities/77536EXXO00001"
    Then the response status is 200
    And the response field "top_chemicals" is a non-empty list
    And the sum of top_chemicals total_lbs equals facility total_release_lbs

  Scenario: Regression 7.BUG.29 — Multi-year facility detail: Bethlehem Steel
    # Bethlehem Steel: 2006=15830 + 2007=14210 + 2008=12485 = 42525 lbs
    When I GET "/api/v1/facilities/21219BTHLS3RD"
    Then the response status is 200
    And the response field "total_release_lbs" equals 42525.0

  Scenario: Regression 7.BUG.29 — Multi-year facility detail: Robinson Nevada
    # Robinson Nevada: 2006=9100 + 2007=7890 + 2008=8205 = 25195 lbs
    When I GET "/api/v1/facilities/89319BHPCP7MILE"
    Then the response status is 200
    And the response field "total_release_lbs" equals 25195.0
