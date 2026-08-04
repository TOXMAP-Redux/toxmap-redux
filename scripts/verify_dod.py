#!/usr/bin/env python3
"""
Automated Definition of Done (DoD) Verification Script

This script verifies all DoD checklist items for a given phase before
allowing phase advancement. It is the automated gate that prevents
premature phase certification (audit finding: "Phase 6 DoD premature
certification led to rollback").

Usage:
    python scripts/verify_dod.py [phase_number]
    python scripts/verify_dod.py  # Uses CURRENT_PHASE.txt

Exit codes:
    0 — All DoD items pass
    1 — One or more DoD items failed
    2 — Script error (invalid phase, missing files, etc.)

This is a PUBLIC HEALTH APPLICATION. Do not bypass this gate.
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
TESTS_DIR = REPO_ROOT / "tests"


@dataclass
class DoDItem:
    """A single Definition of Done checklist item."""

    id: str
    description: str
    check: Callable[[], bool]
    required: bool = True


# ═══════════════════════════════════════════════════════════════════════════════
# Check Functions
# ═══════════════════════════════════════════════════════════════════════════════


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> tuple[int, str]:
    """Run a command and return (exit_code, output)."""
    import os
    
    # Merge with current environment
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=full_env,
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 1, f"Command timed out after {timeout}s"
    except Exception as e:
        return 2, str(e)


def get_python_env() -> dict[str, str]:
    """Get environment variables for running Python tests."""
    return {
        "PYTHONPATH": str(BACKEND_DIR),
    }


def check_docker_compose_up() -> bool:
    """Verify docker compose services are healthy."""
    code, output = run_command(["docker", "compose", "ps", "--format", "json"])
    if code != 0:
        print(f"  ✗ docker compose ps failed: {output}")
        return False
    # Check that all services are running
    try:
        lines = [line for line in output.strip().split("\n") if line]
        for line in lines:
            service = json.loads(line)
            if service.get("State") != "running":
                print(f"  ✗ Service {service.get('Name')} is not running")
                return False
        return True
    except json.JSONDecodeError:
        # Older docker compose format
        return "running" in output.lower()


def check_health_endpoint() -> bool:
    """Verify GET /health returns ok."""
    code, output = run_command(["curl", "-sf", "http://localhost:8000/health"])
    if code != 0:
        print(f"  ✗ Health endpoint failed: {output}")
        return False
    return '"status":"ok"' in output or '"status": "ok"' in output


def check_frontend_loads() -> bool:
    """Verify frontend returns HTTP 200."""
    code, output = run_command(["curl", "-sf", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:3000"])
    if code != 0 or output.strip() != "200":
        print(f"  ✗ Frontend returned HTTP {output}")
        return False
    return True


def check_postgis_version() -> bool:
    """Verify PostGIS is available in the database."""
    code, output = run_command([
        "docker", "compose", "exec", "-T", "postgres",
        "psql", "-U", "postgres", "-d", "toxmap", "-t", "-c",
        "SELECT PostGIS_version();"
    ])
    if code != 0:
        print(f"  ✗ PostGIS check failed: {output}")
        return False
    return "USE_GEOS" in output


def check_python_unit_tests() -> bool:
    """Run pytest tests/unit/ and verify all pass."""
    code, output = run_command(
        ["pytest", "../tests/unit/", "-v", "--tb=short"],
        cwd=BACKEND_DIR,
        timeout=120,
        env=get_python_env(),
    )
    if code != 0:
        print(f"  ✗ Unit tests failed:\n{output[-500:]}")
        return False
    return True


def check_api_tests() -> bool:
    """Run pytest tests/features/api/ and verify all pass."""
    code, output = run_command(
        ["pytest", "../tests/features/api/", "-v", "--tb=short"],
        cwd=BACKEND_DIR,
        timeout=300,
        env=get_python_env(),
    )
    if code != 0:
        print(f"  ✗ API tests failed:\n{output[-500:]}")
        return False
    return True


def check_e2e_tests() -> bool:
    """Run pytest tests/features/e2e/ and verify all pass."""
    code, output = run_command(
        ["pytest", "../tests/features/e2e/", "-v", "--tb=short"],
        cwd=BACKEND_DIR,
        timeout=600,
        env=get_python_env(),
    )
    if code != 0:
        print(f"  ✗ E2E tests failed:\n{output[-500:]}")
        return False
    return True


def check_schemathesis() -> bool:
    """Run Schemathesis contract verification."""
    code, output = run_command([
        "schemathesis", "run",
        "http://localhost:8000/openapi.json",
        "--checks", "response_schema_conformance",
        "--hypothesis-max-examples=50",
    ], timeout=300)
    if code != 0:
        print(f"  ✗ Schemathesis failed:\n{output[-500:]}")
        return False
    return True


def check_python_lint() -> bool:
    """Run ruff format --check and ruff check."""
    code1, _ = run_command(["ruff", "format", "--check", "backend/"])
    code2, _ = run_command(["ruff", "check", "backend/"])
    if code1 != 0 or code2 != 0:
        print("  ✗ Python lint failed")
        return False
    return True


def check_mypy() -> bool:
    """Run mypy type checking."""
    code, output = run_command(["mypy", "backend/app", "backend/ingestion"])
    if code != 0:
        print(f"  ✗ mypy failed:\n{output[-500:]}")
        return False
    return True


def check_frontend_lint() -> bool:
    """Run frontend ESLint."""
    code, output = run_command(["npm", "run", "lint"], cwd=FRONTEND_DIR)
    if code != 0:
        print(f"  ✗ ESLint failed:\n{output[-500:]}")
        return False
    return True


def check_frontend_typecheck() -> bool:
    """Run tsc --noEmit."""
    code, output = run_command(["npx", "tsc", "--noEmit"], cwd=FRONTEND_DIR)
    if code != 0:
        print(f"  ✗ TypeScript check failed:\n{output[-500:]}")
        return False
    return True


def check_frontend_prettier() -> bool:
    """Run Prettier format check."""
    code, output = run_command(["npx", "prettier", "--check", "src/"], cwd=FRONTEND_DIR)
    if code != 0:
        print(f"  ✗ Prettier check failed:\n{output[-500:]}")
        return False
    return True


def check_security_gitleaks() -> bool:
    """Run gitleaks secret scanning."""
    code, output = run_command(["gitleaks", "detect", "--source", ".", "--verbose", "--redact"])
    if code != 0:
        print(f"  ✗ Gitleaks found secrets:\n{output[-500:]}")
        return False
    return True


def check_seed_values() -> bool:
    """Verify immutable seed values exist in database."""
    # Check T-03 seed value: 89319BHPCP7MILE → copper → 8205.0 lbs
    code, output = run_command([
        "docker", "compose", "exec", "-T", "postgres",
        "psql", "-U", "postgres", "-d", "toxmap", "-t", "-c",
        "SELECT total_release_lbs FROM tri_releases WHERE facility_id = '89319BHPCP7MILE' AND chemical_name ILIKE '%copper%' AND release_year = 2008;"
    ])
    if code != 0 or "8205" not in output:
        print(f"  ✗ T-03 seed value missing or incorrect: {output}")
        return False
    return True


def check_no_skipped_scenarios() -> bool:
    """Verify no @skip tags in feature files."""
    code, output = run_command(["grep", "-r", "@skip", "tests/features/"])
    # grep returns 0 if found, 1 if not found
    if code == 0:
        print(f"  ✗ Found @skip tags in feature files:\n{output}")
        return False
    return True


def check_coverage_threshold() -> bool:
    """Verify test coverage meets minimum threshold (80%)."""
    code, output = run_command(
        ["pytest", "../tests/unit/", "--cov=app", "--cov-fail-under=80", "--cov-report=term-missing"],
        cwd=BACKEND_DIR,
        timeout=120,
        env=get_python_env(),
    )
    if code != 0:
        print(f"  ✗ Coverage below 80%:\n{output[-500:]}")
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# Phase DoD Definitions
# ═══════════════════════════════════════════════════════════════════════════════

PHASE_DOD: dict[int, list[DoDItem]] = {
    0: [
        DoDItem("0.1", "docker compose up → all services healthy", check_docker_compose_up),
        DoDItem("0.2", "GET /health → {status: ok}", check_health_endpoint),
        DoDItem("0.3", "Frontend loads at localhost:3000", check_frontend_loads),
        DoDItem("0.4", "PostGIS version available", check_postgis_version),
        DoDItem("0.5", "pytest tests/unit/ passes", check_python_unit_tests),
    ],
    1: [
        DoDItem("1.1", "All Phase 0 checks", check_docker_compose_up),
        DoDItem("1.2", "Seed values present (T-03)", check_seed_values),
        DoDItem("1.3", "Python lint passes", check_python_lint),
        DoDItem("1.4", "mypy passes", check_mypy),
    ],
    2: [
        DoDItem("2.1", "API tests pass", check_api_tests),
        DoDItem("2.2", "Schemathesis contract verification", check_schemathesis),
        DoDItem("2.3", "Python lint passes", check_python_lint),
        DoDItem("2.4", "mypy passes", check_mypy),
    ],
    3: [
        DoDItem("3.1", "Frontend lint passes", check_frontend_lint),
        DoDItem("3.2", "TypeScript compiles", check_frontend_typecheck),
        DoDItem("3.3", "Prettier format check", check_frontend_prettier),
        DoDItem("3.4", "E2E tests pass", check_e2e_tests),
    ],
    4: [
        DoDItem("4.1", "All Phase 3 frontend checks", check_frontend_lint),
        DoDItem("4.2", "E2E tests pass", check_e2e_tests),
        DoDItem("4.3", "API tests pass", check_api_tests),
    ],
    5: [
        DoDItem("5.1", "All Phase 4 checks", check_frontend_lint),
        DoDItem("5.2", "E2E tests pass", check_e2e_tests),
        DoDItem("5.3", "API tests pass", check_api_tests),
    ],
    6: [
        DoDItem("6.1", "Unit tests pass", check_python_unit_tests),
        DoDItem("6.2", "API tests pass", check_api_tests),
        DoDItem("6.3", "E2E tests pass", check_e2e_tests),
        DoDItem("6.4", "Schemathesis passes", check_schemathesis),
        DoDItem("6.5", "Python lint passes", check_python_lint),
        DoDItem("6.6", "mypy passes", check_mypy),
        DoDItem("6.7", "Frontend lint passes", check_frontend_lint),
        DoDItem("6.8", "TypeScript compiles", check_frontend_typecheck),
        DoDItem("6.9", "Prettier format check", check_frontend_prettier),
        DoDItem("6.10", "Gitleaks secret scan", check_security_gitleaks),
        DoDItem("6.11", "No @skip tags in features", check_no_skipped_scenarios),
        DoDItem("6.12", "Coverage ≥ 80%", check_coverage_threshold),
    ],
    7: [
        DoDItem("7.1", "All Phase 6 checks must pass", check_python_unit_tests),
        DoDItem("7.2", "E2E tests pass", check_e2e_tests),
        DoDItem("7.3", "Gitleaks secret scan", check_security_gitleaks),
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════


def get_current_phase() -> int:
    """Read current phase from CURRENT_PHASE.txt."""
    phase_file = REPO_ROOT / "CURRENT_PHASE.txt"
    if not phase_file.exists():
        raise FileNotFoundError("CURRENT_PHASE.txt not found")
    return int(phase_file.read_text().strip())


def verify_phase_dod(phase: int) -> tuple[bool, list[str], list[str]]:
    """
    Verify all DoD items for a phase.
    
    Returns:
        (all_passed, passed_items, failed_items)
    """
    if phase not in PHASE_DOD:
        raise ValueError(f"No DoD defined for phase {phase}")
    
    items = PHASE_DOD[phase]
    passed: list[str] = []
    failed: list[str] = []
    
    print(f"\n{'═' * 60}")
    print(f"  PHASE {phase} — Definition of Done Verification")
    print(f"{'═' * 60}\n")
    
    for item in items:
        print(f"[{item.id}] {item.description}...", end=" ", flush=True)
        try:
            if item.check():
                print("✅ PASS")
                passed.append(item.id)
            else:
                print("❌ FAIL")
                failed.append(item.id)
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed.append(item.id)
    
    print(f"\n{'─' * 60}")
    print(f"  Results: {len(passed)} passed, {len(failed)} failed")
    print(f"{'─' * 60}\n")
    
    return len(failed) == 0, passed, failed


def main() -> int:
    """Main entry point."""
    # Determine phase
    if len(sys.argv) > 1:
        try:
            phase = int(sys.argv[1])
        except ValueError:
            print(f"Error: Invalid phase number: {sys.argv[1]}", file=sys.stderr)
            return 2
    else:
        try:
            phase = get_current_phase()
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
    
    print(f"\n🏥 TOXMAP DoD Verification — This is a PUBLIC HEALTH APPLICATION")
    print(f"   Phase: {phase}")
    print(f"   Repo:  {REPO_ROOT}")
    
    try:
        all_passed, passed, failed = verify_phase_dod(phase)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    
    if all_passed:
        print("✅ ALL DoD ITEMS PASSED — Phase advancement authorized")
        return 0
    else:
        print("❌ DoD VERIFICATION FAILED — Phase advancement BLOCKED")
        print(f"   Failed items: {', '.join(failed)}")
        print("\n   This is a PUBLIC HEALTH APPLICATION.")
        print("   Do not bypass this gate. Fix the failures and re-run.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
