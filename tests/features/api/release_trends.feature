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
