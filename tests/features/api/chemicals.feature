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
