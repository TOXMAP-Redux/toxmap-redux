"""pytest-bdd runner for: facility_search."""
from pytest_bdd import scenarios
from tests.steps.api_steps import *  # noqa: F401,F403
scenarios("api/facility_search.feature")
