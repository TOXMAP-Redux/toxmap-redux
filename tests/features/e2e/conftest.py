# tests/features/e2e/conftest.py
"""
pytest-bdd step registration for E2E tests.

This conftest imports all step modules to make their step definitions
available to feature files in this directory.

In pytest-bdd 8.x, step definitions are registered as pytest fixtures.
They must be imported into a conftest.py that pytest can discover.
"""

# Import step modules explicitly to register step fixtures with pytest-bdd
# noqa comments suppress false-positive F401 (imported but unused) errors
from tests.steps.navigation_steps import *  # noqa: F401,F403
from tests.steps.search_steps import *  # noqa: F401,F403
from tests.steps.results_steps import *  # noqa: F401,F403
from tests.steps.facility_steps import *  # noqa: F401,F403
from tests.steps.superfund_steps import *  # noqa: F401,F403
from tests.steps.demographics_steps import *  # noqa: F401,F403
from tests.steps.map_layer_steps import *  # noqa: F401,F403
from tests.steps.export_steps import *  # noqa: F401,F403
from tests.steps.regression_steps import *  # noqa: F401,F403
from tests.steps.stubs_steps import *  # noqa: F401,F403
