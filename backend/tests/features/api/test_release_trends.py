"""pytest-bdd test runner for Feature: release_trends."""

from pytest_bdd import scenarios
from tests.steps.api_steps import *  # noqa: F401,F403

scenarios("api/release_trends.feature")
