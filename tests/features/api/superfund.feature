Feature: Superfund Site Search

  Background:
    Given the seed database is loaded

  # ── Browse mode (no radius constraint) — added 2026-07-28 ────────────────────

  Scenario: Browse endpoint returns all Superfund sites without radius
    When I GET "/api/v1/superfund/browse"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And superfund site "VAD070358684" is in the results

  Scenario: Browse endpoint with state filter
    When I GET "/api/v1/superfund/browse?state=VA"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And every feature has property "state_code" = "VA"

  Scenario: Browse endpoint with NPL status filter
    When I GET "/api/v1/superfund/browse?status=NPL"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And every feature has property "status" = "NPL"

  # ── Radius search ────────────────────────────────────────────────────────────

  Scenario: T-04 — AVTEX FIBERS found near Front Royal VA
    When I GET "/api/v1/superfund?lat=38.9179&lon=-78.1942&radius_miles=10"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And superfund site "VAD070358684" is in the results

  Scenario: Superfund detail for AVTEX FIBERS
    When I GET "/api/v1/superfund/VAD070358684"
    Then the response status is 200
    And the response field "epa_id" equals "VAD070358684"
    And the response field "name" equals "AVTEX FIBERS INC"
    And the response field "city" equals "FRONT ROYAL"

  Scenario: Superfund detail 404 for unknown site
    When I GET "/api/v1/superfund/DOESNOTEXIST"
    Then the response status is 404
