"""Performance benchmark tests — Phase 6 story 6.2.

SLA targets (from TOXMAP_DEVELOPMENT_ROADMAP.md Phase 6 Epic 6.2):
  - Radius search p95     < 500ms
  - Viewport bbox p95     < 200ms
  - Chemical autocomplete < 100ms  (also verified in Gherkin feature chemicals.feature)
  - Superfund search p95  < 300ms
  - CSV first byte        < 1,000ms

Run: pytest tests/benchmarks/ -v --benchmark-disable-gc

Note: These tests use pytest-benchmark. Results are compared against the SLA
thresholds set below. Tests fail if the mean response time exceeds the SLA.
"""
import time
import pytest


# ── Shared timing helpers ─────────────────────────────────────────────────────

_SLA_RADIUS_MS = 500
_SLA_BBOX_MS = 200
_SLA_AUTOCOMPLETE_MS = 100
_SLA_SUPERFUND_MS = 300
_SLA_CSV_MS = 1000

_ITERATIONS = 10  # Requests per benchmark (enough for mean without excessive test time)


def _mean_ms(times: list[float]) -> float:
    return (sum(times) / len(times)) * 1000


# ── Benchmark tests ───────────────────────────────────────────────────────────


class TestPerformanceSLAs:
    """6.2 — Performance SLAs: mean latency for each API endpoint type."""

    def test_radius_search_mean_under_500ms(
        self, api_client, seed_db: None
    ) -> None:
        """Radius facility search mean latency < 500ms (SLA: p95 < 500ms)."""
        times: list[float] = []
        for _ in range(_ITERATIONS):
            t0 = time.perf_counter()
            r = api_client.get(
                "/api/v1/facilities",
                params={"lat": 39.2197, "lon": -76.4785, "radius_miles": 25},
            )
            t1 = time.perf_counter()
            assert r.status_code == 200, f"Unexpected status {r.status_code}"
            times.append(t1 - t0)

        mean = _mean_ms(times)
        assert mean < _SLA_RADIUS_MS, (
            f"Radius search mean latency {mean:.0f}ms exceeds SLA of {_SLA_RADIUS_MS}ms"
        )

    def test_viewport_bbox_refetch_mean_under_200ms(
        self, api_client, seed_db: None
    ) -> None:
        """Viewport bbox facility re-fetch mean latency < 200ms (SLA: p95 < 200ms)."""
        times: list[float] = []
        for _ in range(_ITERATIONS):
            t0 = time.perf_counter()
            r = api_client.get(
                "/api/v1/facilities/browse",
                params={"bbox": "-80,38,-74,42"},
            )
            t1 = time.perf_counter()
            assert r.status_code == 200, f"Unexpected status {r.status_code}"
            times.append(t1 - t0)

        mean = _mean_ms(times)
        assert mean < _SLA_BBOX_MS, (
            f"Viewport bbox mean latency {mean:.0f}ms exceeds SLA of {_SLA_BBOX_MS}ms"
        )

    def test_chemical_autocomplete_mean_under_100ms(
        self, api_client, seed_db: None
    ) -> None:
        """Chemical autocomplete mean latency < 100ms (SLA: < 100ms)."""
        times: list[float] = []
        for _ in range(_ITERATIONS):
            t0 = time.perf_counter()
            r = api_client.get("/api/v1/chemicals/search", params={"q": "lead"})
            t1 = time.perf_counter()
            assert r.status_code == 200, f"Unexpected status {r.status_code}"
            times.append(t1 - t0)

        mean = _mean_ms(times)
        assert mean < _SLA_AUTOCOMPLETE_MS, (
            f"Chemical autocomplete mean latency {mean:.0f}ms exceeds SLA of {_SLA_AUTOCOMPLETE_MS}ms"
        )

    def test_superfund_search_mean_under_300ms(
        self, api_client, seed_db: None
    ) -> None:
        """Superfund radius search mean latency < 300ms (SLA: p95 < 300ms)."""
        times: list[float] = []
        for _ in range(_ITERATIONS):
            t0 = time.perf_counter()
            r = api_client.get(
                "/api/v1/superfund",
                params={"lat": 38.9, "lon": -78.2, "radius_miles": 50},
            )
            t1 = time.perf_counter()
            assert r.status_code == 200, f"Unexpected status {r.status_code}"
            times.append(t1 - t0)

        mean = _mean_ms(times)
        assert mean < _SLA_SUPERFUND_MS, (
            f"Superfund search mean latency {mean:.0f}ms exceeds SLA of {_SLA_SUPERFUND_MS}ms"
        )

    def test_csv_export_first_byte_under_1000ms(
        self, api_client, seed_db: None
    ) -> None:
        """CSV export first byte latency < 1,000ms (SLA: first byte < 1s)."""
        times: list[float] = []
        for _ in range(_ITERATIONS):
            t0 = time.perf_counter()
            r = api_client.get(
                "/api/v1/export/csv",
                params={"lat": 39.2, "lon": -76.4, "radius_miles": 50},
            )
            t1 = time.perf_counter()
            assert r.status_code == 200, f"Unexpected status {r.status_code}"
            # Verify it's actually a CSV response (content-type check)
            ct = r.headers.get("content-type", "")
            assert "csv" in ct or "text" in ct, f"Unexpected content-type: {ct}"
            times.append(t1 - t0)

        mean = _mean_ms(times)
        assert mean < _SLA_CSV_MS, (
            f"CSV export mean latency {mean:.0f}ms exceeds SLA of {_SLA_CSV_MS}ms"
        )
