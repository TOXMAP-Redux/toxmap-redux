Feature: API Metadata Endpoint

  Background:
    Given the seed database is loaded

  Scenario: Meta endpoint returns required fields
    When I GET "/api/v1/meta"
    Then the response status is 200
    And the response field "source" equals "fastapi-dev"
    And the response field "available_years" is a non-empty list
    And the response field "vintage_label" is not null
