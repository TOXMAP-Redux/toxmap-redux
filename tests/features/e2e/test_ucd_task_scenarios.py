"""pytest-bdd runner for: UCD 2011 task scenarios (T-01 through T-09).

Phase coverage:
- Phase 3: T-01, T-03, T-08 (TRI search + map)
- Phase 4: T-02, T-04 (Superfund overlay)
- Phase 5: T-05, T-06, T-09 (Demographics overlay)

Step definitions are imported via tests/features/e2e/conftest.py.
"""
from pytest_bdd import scenarios

scenarios("e2e/ucd_task_scenarios.feature")
