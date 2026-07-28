"""pytest-bdd test runner for Feature: superfund."""

from pytest_bdd import scenarios
from tests.steps.api_steps import *  # noqa: F401,F403

scenarios("api/superfund.feature")
