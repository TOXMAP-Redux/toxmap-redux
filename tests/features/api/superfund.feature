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

  # ── Contaminant enrichment (7.BUG.16–7.BUG.18 regression tests) ────────────

  @regression @7BUG18
  Scenario: MANGANESE contaminant has correct ATSDR ToxFAQs toxid=23
    When I GET "/api/v1/superfund/WY5571924179"
    Then the response status is 200
    And contaminant "MANGANESE" has atsdr_url containing "toxid=23"

  @regression @7BUG18
  Scenario: MANGANESE does NOT link to Methylene Chloride toxid=42
    When I GET "/api/v1/superfund/WY5571924179"
    Then the response status is 200
    And contaminant "MANGANESE" atsdr_url does NOT contain "toxid=42"

  @regression @7BUG17
  Scenario: Superfund contaminants have CAS numbers from lookup
    When I GET "/api/v1/superfund/WY5571924179"
    Then the response status is 200
    And contaminant "MANGANESE" has cas_number "7439-96-5"
    And contaminant "TRICHLOROETHENE" has cas_number "79-01-6"

  @regression @7BUG18
  Scenario: MERCURY has correct ATSDR ToxFAQs toxid=24
    When I GET "/api/v1/superfund/WY5571924179"
    Then the response status is 200
    And contaminant "MERCURY" has atsdr_url containing "toxid=24"

  @regression @7BUG18
  Scenario: TCE has correct ATSDR ToxFAQs toxid=30
    When I GET "/api/v1/superfund/WY5571924179"
    Then the response status is 200
    And contaminant "TRICHLOROETHENE" has atsdr_url containing "toxid=30"

  @regression @7BUG17
  Scenario: PAH chemicals have correct CAS from supplementary lookup
    When I GET "/api/v1/superfund/WY5571924179"
    Then the response status is 200
    And contaminant "BENZO[A]PYRENE" has cas_number "50-32-8"

  # ── epa_progress_url ingestion (6.UX.1 regression tests) ───────────────────

  @regression @6UX1
  Scenario: Superfund detail has epa_progress_url populated from SEMS site_id
    When I GET "/api/v1/superfund/VAD070358684"
    Then the response status is 200
    And the response field "epa_progress_url" is not null
    And the response field "epa_progress_url" contains "cumulis.epa.gov/supercpad"

  @regression @6UX1
  Scenario: epa_progress_url uses correct SEMS site_id format
    When I GET "/api/v1/superfund/VAD070358684"
    Then the response status is 200
    And the response field "epa_progress_url" matches pattern "id=\d{7}"

  @regression @6UX1
  Scenario: Browse endpoint includes epa_progress_url in GeoJSON properties
    When I GET "/api/v1/superfund/browse?state=VA"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And every feature has property "epa_progress_url" that is not null
