"""pytest-bdd runner for: UCD 2011 task scenarios (T-01 through T-09).

Phase coverage:
- Phase 3: T-01, T-03, T-08 (TRI search + map)
- Phase 4: T-02, T-04 (Superfund overlay)
- Phase 5: T-05, T-06, T-09 (Demographics overlay)
"""
from pytest_bdd import scenarios
from tests.steps.e2e_steps import *  # noqa: F401,F403

scenarios("ucd_task_scenarios.feature")
