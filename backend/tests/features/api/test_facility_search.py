"""pytest-bdd test runner for Feature F1 — Facility Search.

Story 2.QA.1: implements @scenarios binding so pytest collects all
scenarios from facility_search.feature.
"""

import pytest
from pytest_bdd import scenarios

from tests.steps.api_steps import *  # noqa: F401,F403 — import step definitions

scenarios("api/facility_search.feature")
