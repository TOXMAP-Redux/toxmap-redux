Feature: Chemical Search and Autocomplete

  Background:
    Given the seed database is loaded

  Scenario: Get all chemicals returns sorted list
    When I GET "/api/v1/chemicals"
    Then the response status is 200
    And the response is a JSON array
    And the response contains a chemical named "AMMONIA"

  Scenario: Chemical autocomplete returns matches
    When I GET "/api/v1/chemicals/search?q=cop"
    Then the response status is 200
    And the response is a JSON array
    And the first result name contains "COPPER"

  Scenario: Autocomplete too short returns 422
    When I GET "/api/v1/chemicals/search?q=c"
    Then the response status is 422

  # 7.BUG.20 regression tests: ATSDR URL family inheritance
  @regression @7.BUG.20
  Scenario: Direct chemical match has ATSDR URL (LEAD)
    When I GET "/api/v1/chemicals/search?q=LEAD"
    Then the response status is 200
    And the response is a JSON array
    And the response contains a chemical named "LEAD" with atsdr_url containing "toxid=22"

  @regression @7.BUG.20
  Scenario: Family member has ATSDR URL via inheritance (ZINC COMPOUNDS)
    When I GET "/api/v1/chemicals/search?q=ZINC"
    Then the response status is 200
    And the response is a JSON array
    And the response contains a chemical named "ZINC COMPOUNDS" with atsdr_url containing "toxid=54"

  @regression @7.BUG.20
  Scenario: Family member has ATSDR URL via inheritance (LEAD AND LEAD COMPOUNDS)
    When I GET "/api/v1/chemicals/search?q=LEAD"
    Then the response status is 200
    And the response is a JSON array
    And the response contains a chemical named "LEAD  AND LEAD COMPOUNDS" with atsdr_url containing "toxid=22"
