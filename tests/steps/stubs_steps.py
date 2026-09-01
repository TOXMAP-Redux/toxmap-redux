# tests/steps/stubs_steps.py
"""
Stub step implementations for scenarios that are not yet implemented.

These steps allow tests to be skipped gracefully while documenting
the intended functionality. When the corresponding features are implemented,
these stubs should be replaced with real assertions.
"""

import pytest
from pytest_bdd import then, given


# ── Phase 5: Demographics stubs ───────────────────────────────────────────────


@then('a demographics scenario stub exists')
def demographics_stub() -> None:
    """Placeholder for Phase 5 demographics scenario."""
    pytest.skip('Phase 5 scenario — not yet implemented')


@then('a demographics invariant stub exists')
def demographics_invariant_stub() -> None:
    """Placeholder for Phase 5 demographics UX invariant."""
    pytest.skip('Phase 5 invariant — not yet implemented')


# ── Phase 3: T-07 Chlorine stub ───────────────────────────────────────────────


@then('a chlorine scenario stub exists')
def chlorine_stub() -> None:
    """Placeholder for T-07 chlorine search scenario."""
    pytest.skip('Phase 3 E2E — T-07 covered by API tests; E2E pending')


# ── Application state stubs ───────────────────────────────────────────────────


@given('I open the TOXMAP application')
def open_toxmap_application() -> None:
    """
    Stub for opening the TOXMAP application.
    
    This step is used in scenarios that need to reset the application state.
    In most cases, the `I am on the map page` step should be used instead.
    """
    pytest.skip('Use "I am on the map page" step instead')
