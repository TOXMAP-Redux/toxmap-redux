# tests/features/api/conftest.py
"""
pytest-bdd step registration for API tests.

This conftest imports the API step module to make step definitions
available to feature files in this directory.
"""

# Import API steps module to register step fixtures with pytest-bdd
from tests.steps.api_steps import *  # noqa: F401,F403
