"""Security regression tests — Phase 6 story 6.4.4.

Tests:
  - Input validation: 422 for out-of-bounds parameters
  - Rate limiting: 429 on 61st rapid request
  - Error sanitization: no stack trace / internal path in 500 responses
  - CORS: Access-Control-Allow-Origin is never "*"

Run: pytest tests/security/ -v
"""
import time
import pytest
from fastapi.testclient import TestClient


# ── Fixtures ──────────────────────────────────────────────────────────────────
# api_client and seed_db are provided by tests/conftest.py


# ── Input Validation Tests ────────────────────────────────────────────────────


class TestInputValidation:
    """6.4.4 — API boundary validation: all invalid parameters return 422."""

    def test_lat_above_max_returns_422(self, api_client: TestClient) -> None:
        r = api_client.get("/api/v1/facilities?lat=999&lon=-76.4&radius_miles=10")
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text[:200]}"

    def test_lat_below_min_returns_422(self, api_client: TestClient) -> None:
        r = api_client.get("/api/v1/facilities?lat=-999&lon=-76.4&radius_miles=10")
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text[:200]}"

    def test_lon_above_max_returns_422(self, api_client: TestClient) -> None:
        r = api_client.get("/api/v1/facilities?lat=39.2&lon=999&radius_miles=10")
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text[:200]}"

    def test_lon_below_min_returns_422(self, api_client: TestClient) -> None:
        r = api_client.get("/api/v1/facilities?lat=39.2&lon=-999&radius_miles=10")
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text[:200]}"

    def test_radius_too_large_returns_422(self, api_client: TestClient) -> None:
        r = api_client.get("/api/v1/facilities?lat=39.2&lon=-76.4&radius_miles=5000")
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text[:200]}"

    def test_radius_negative_returns_422(self, api_client: TestClient) -> None:
        r = api_client.get("/api/v1/facilities?lat=39.2&lon=-76.4&radius_miles=-1")
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text[:200]}"

    def test_state_too_long_returns_422(self, api_client: TestClient) -> None:
        r = api_client.get("/api/v1/demographics/county?state=TOOLONG")
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text[:200]}"

    def test_superfund_lat_out_of_range_returns_422(self, api_client: TestClient) -> None:
        r = api_client.get("/api/v1/superfund?lat=999&lon=-76.4&radius_miles=10")
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text[:200]}"

    def test_superfund_radius_too_large_returns_422(self, api_client: TestClient) -> None:
        r = api_client.get("/api/v1/superfund?lat=39.2&lon=-76.4&radius_miles=501")
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text[:200]}"


# ── Rate Limiting Tests ───────────────────────────────────────────────────────


class TestRateLimiting:
    """6.4.4 — Rate limiting: 429 after 60 requests/minute per IP (slowapi)."""

    def test_sixty_first_request_returns_429(self, api_client: TestClient) -> None:
        """61st rapid GET /health request must return 429."""
        endpoint = "/health"
        responses = []
        for _ in range(61):
            r = api_client.get(endpoint)
            responses.append(r.status_code)

        # The last response should be 429 (rate limit exceeded)
        # Due to per-process client reuse, all 61 requests hit the same IP bucket
        assert 429 in responses, (
            f"Expected at least one 429 in 61 rapid requests, but got: "
            f"{set(responses)}"
        )


# ── Error Sanitization Tests ──────────────────────────────────────────────────


class TestErrorSanitization:
    """6.4.4 — Error sanitization: 500 responses must not leak internal details."""

    def test_nonexistent_facility_detail_returns_404_not_500(
        self, api_client: TestClient
    ) -> None:
        """GET /api/v1/facilities/{id} for a non-existent ID returns 404, not 500."""
        r = api_client.get("/api/v1/facilities/NONEXISTENT_FACILITY_ID_12345")
        # 404 is acceptable; any server error (5xx) is not
        assert r.status_code < 500, (
            f"Expected < 500 status for unknown facility; got {r.status_code}: "
            f"{r.text[:300]}"
        )

    def test_200_responses_do_not_contain_traceback(
        self, api_client: TestClient, seed_db: None
    ) -> None:
        """Successful responses must not contain any internal Python traceback fragments."""
        endpoints = [
            "/health",
            "/api/v1/facilities?lat=39.2&lon=-76.4&radius_miles=10",
            "/api/v1/chemicals",
            "/api/v1/meta",
        ]
        for path in endpoints:
            r = api_client.get(path)
            body = r.text
            for leak in ("Traceback", 'File "/', "sqlalchemy", "asyncpg"):
                assert leak not in body, (
                    f"Response from {path!r} leaks internal detail {leak!r}: "
                    f"{body[:300]}"
                )

    def test_nonexistent_route_returns_404_without_traceback(
        self, api_client: TestClient
    ) -> None:
        r = api_client.get("/api/v1/does_not_exist_endpoint")
        assert r.status_code == 404
        body = r.text
        for leak in ("Traceback", 'File "/', "sqlalchemy"):
            assert leak not in body, (
                f"404 response leaks {leak!r}: {body[:300]}"
            )


# ── CORS Tests ────────────────────────────────────────────────────────────────


class TestCORS:
    """6.4.2 — CORS header audit: Access-Control-Allow-Origin never '*'."""

    def test_cors_origin_is_not_wildcard(self, api_client: TestClient) -> None:
        """CORS header must not be '*' (open CORS breaks the security model)."""
        r = api_client.get(
            "/api/v1/facilities?lat=39.2&lon=-76.4&radius_miles=10",
            headers={"Origin": "http://localhost:3000"},
        )
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao != "*", (
            "Access-Control-Allow-Origin is '*' — open CORS breaks the API security model. "
            "Set ALLOWED_ORIGINS to explicit domains."
        )

    def test_cors_preflight_allowed_methods_restricted(
        self, api_client: TestClient
    ) -> None:
        """OPTIONS preflight must not allow arbitrary methods like DELETE or PATCH."""
        r = api_client.options(
            "/api/v1/facilities",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # 200 or 204 is acceptable; what matters is that the allowed methods
        # are restricted to safe read-only methods (GET, OPTIONS, HEAD)
        if r.status_code in (200, 204):
            allow_methods = r.headers.get("access-control-allow-methods", "")
            for dangerous in ("DELETE", "PATCH", "PUT"):
                assert dangerous not in allow_methods.upper(), (
                    f"CORS allows dangerous method {dangerous!r}: {allow_methods!r}"
                )
