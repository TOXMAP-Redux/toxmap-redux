"""pytest-bdd runner for: UX invariants (10 non-negotiable UI constraints).

Phase coverage:
- Phase 3: Invariants 1, 2, 3, 4, 7, 8, 9
- Phase 4: Invariant 6
- Phase 5: Invariants 5, 10
"""
from pytest_bdd import scenarios
from tests.steps.e2e_steps import *  # noqa: F401,F403

scenarios("ux_invariants.feature")
