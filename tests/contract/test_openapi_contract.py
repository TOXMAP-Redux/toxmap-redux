"""Schemathesis contract tests — Layer 4.

Validates API responses against OpenAPI schema.
Runs as part of `pytest tests/contract/` or the full test suite.

Requires: running API server on localhost:8000
"""

import pytest
import schemathesis
from hypothesis import settings, HealthCheck

# Load OpenAPI schema from the running server
# Uses the same endpoint as CI: http://localhost:8000/openapi.json
schema = schemathesis.from_uri("http://localhost:8000/openapi.json")


# Configure hypothesis settings for API testing
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    deadline=5000,  # 5 second deadline per test
)
@schema.parametrize()
def test_api_contract(case: schemathesis.Case) -> None:
    """Test all API endpoints against their OpenAPI schema.
    
    Schemathesis generates test cases from the OpenAPI spec and validates:
    - Response status codes match documented codes
    - Response body conforms to documented schema
    - Required fields are present
    - Field types are correct
    
    This test function is parametrized by Schemathesis to generate
    individual test cases for each endpoint/method combination.
    """
    response = case.call()
    case.validate_response(response)


# Mark as integration test requiring running services
pytestmark = [
    pytest.mark.integration,
    pytest.mark.contract,
]
