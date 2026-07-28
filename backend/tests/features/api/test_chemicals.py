"""pytest-bdd test runner for Feature F3 — Chemicals."""

from pytest_bdd import scenarios
from tests.steps.api_steps import *  # noqa: F401,F403

scenarios("api/chemicals.feature")
