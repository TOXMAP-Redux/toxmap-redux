"""pytest-bdd runner for: UX invariants (10 non-negotiable UI constraints).

Phase coverage:
- Phase 3: Invariants 1, 2, 3, 4, 7, 8, 9
- Phase 4: Invariant 6
- Phase 5: Invariants 5, 10

Step definitions are imported via tests/features/e2e/conftest.py.
"""
from pytest_bdd import scenarios

scenarios("e2e/ux_invariants.feature")
