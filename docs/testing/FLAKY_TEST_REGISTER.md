# Flaky Test Register

> **This is a PUBLIC HEALTH APPLICATION.** Every flaky test is a reliability risk.

**Purpose:** Track flaky tests, their root causes, and remediation progress. No test should remain in this register for more than one sprint (2 weeks).

**Process:**
1. When a test exhibits flaky behavior, add it to this register
2. Investigate root cause within 48 hours
3. Fix the root cause (do not just add retries)
4. Remove from register when fixed

---

## Currently Tracked Flaky Tests

| Test Name | Date Marked | Failure Rate | Suspected Cause | Owner | Target Fix Date | Status |
|-----------|-------------|--------------|-----------------|-------|-----------------|--------|
| *(none currently tracked)* | — | — | — | — | — | — |

---

## Resolved Flaky Tests (Historical)

| Test Name | Date Marked | Date Resolved | Root Cause | Resolution |
|-----------|-------------|---------------|------------|------------|
| *(none resolved yet)* | — | — | — | — |

---

## Common Flaky Test Patterns

### 1. Race Conditions (Async)
**Symptom:** Test passes locally, fails in CI; or intermittent failures  
**Cause:** Async operation not properly awaited  
**Fix:** Add explicit `await` or `asyncio.sleep()` with condition check

### 2. Time-Dependent Assertions
**Symptom:** Fails at specific times (midnight, month boundaries)  
**Cause:** Assertions depend on `datetime.now()`  
**Fix:** Use `pytest-freezegun` to mock time

### 3. Database State Leakage
**Symptom:** Test passes in isolation, fails in full suite  
**Cause:** Previous test left state in database  
**Fix:** Ensure `seed_db` fixture uses `function` scope and truncates all tables

### 4. Playwright Timing
**Symptom:** Element not found / timeout errors  
**Cause:** Implicit waits insufficient for dynamic content  
**Fix:** Use explicit `page.wait_for_selector()` with reasonable timeout

### 5. Port Conflicts
**Symptom:** Connection refused errors in CI only  
**Cause:** Previous test left server running; port not released  
**Fix:** Use dynamic port allocation or ensure proper teardown

### 6. Network Flakiness
**Symptom:** Geocoding tests fail intermittently  
**Cause:** External API (Photon) rate limiting or timeout  
**Fix:** Mock external calls in tests; use recorded responses

---

## Adding a Test to This Register

```markdown
| test_facility_search_radius | 2026-08-04 | 15% | Race condition in async bbox filter | QA | 2026-08-11 | 🔄 Investigating |
```

**Status values:**
- 🔄 Investigating — Root cause analysis in progress
- 🔧 Fix in Progress — Solution identified, PR in progress
- ✅ Fixed — Removed from "Currently Tracked" to "Resolved"
- 🚫 Escalated — Requires architectural change, escalated to BE/FE
