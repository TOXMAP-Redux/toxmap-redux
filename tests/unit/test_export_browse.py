# tests/unit/test_export_browse.py
"""
Unit tests for the browse export endpoint (no spatial constraint).

Regression tests for defect 6.EXPORT.16:
- Empty CSV when searching by state without map location
- Root cause: /api/v1/export/csv required lat/lon; frontend fell back to Kansas center
- Fix: Added /api/v1/export/csv/browse endpoint without spatial constraint

These tests verify that the browse endpoint:
1. Returns data when filtering by state only
2. Returns data when filtering by chemical only
3. Returns data when filtering by both state and chemical
4. Correctly filters results to match the requested state
"""
import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def client(seed_db):
    """FastAPI test client with seeded database."""
    app = create_app()
    with TestClient(app) as c:
        yield c


class TestExportCsvBrowse:
    """Tests for GET /api/v1/export/csv/browse endpoint."""

    def test_browse_export_returns_csv_header(self, client: TestClient) -> None:
        """Browse endpoint returns valid CSV with header row."""
        response = client.get("/api/v1/export/csv/browse")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        
        content = response.text
        lines = content.strip().split("\n")
        assert len(lines) >= 1, "CSV should have at least a header row"
        
        header = lines[0]
        assert "tri_facility_id" in header
        assert "chemical_name" in header
        assert "state_code" in header

    def test_browse_export_state_filter_returns_data(self, client: TestClient) -> None:
        """Browse with state filter returns facilities in that state.
        
        Regression test for 6.EXPORT.16: State-filtered export must return data
        without requiring lat/lon coordinates.
        """
        # Filter to NV where seed data (BHP COPPER - 7 MILE) is located
        response = client.get("/api/v1/export/csv/browse?state=NV")
        assert response.status_code == 200
        
        content = response.text
        lines = content.strip().split("\n")
        
        # Must have header + at least 1 data row
        assert len(lines) >= 2, "State filter should return at least 1 facility"
        
        # All data rows should have NV in state column
        header = lines[0].split(",")
        state_idx = header.index("state_code")
        
        for line in lines[1:]:
            cols = line.split(",")
            assert cols[state_idx] == "NV", f"Expected NV, got {cols[state_idx]}"

    def test_browse_export_chemical_filter(self, client: TestClient) -> None:
        """Browse with chemical filter returns matching facilities."""
        response = client.get("/api/v1/export/csv/browse?chemical=COPPER")
        assert response.status_code == 200
        
        content = response.text
        lines = content.strip().split("\n")
        
        # Must have header + at least 1 data row (seed has copper releases)
        assert len(lines) >= 2, "Chemical filter should return at least 1 facility"

    def test_browse_export_combined_filters(self, client: TestClient) -> None:
        """Browse with state + chemical filters returns matching facilities."""
        response = client.get("/api/v1/export/csv/browse?state=NV&chemical=COPPER")
        assert response.status_code == 200
        
        content = response.text
        lines = content.strip().split("\n")
        
        # Seed data has BHP COPPER in NV with copper releases
        assert len(lines) >= 2, "Combined filters should return at least 1 facility"

    def test_browse_export_respects_limit(self, client: TestClient) -> None:
        """Browse endpoint respects the limit parameter."""
        response = client.get("/api/v1/export/csv/browse?limit=1")
        assert response.status_code == 200
        
        content = response.text
        lines = content.strip().split("\n")
        
        # Header + exactly 1 data row
        assert len(lines) == 2, f"Expected 2 lines (header + 1 row), got {len(lines)}"

    def test_browse_export_filename_includes_state(self, client: TestClient) -> None:
        """Filename includes state code when state filter is used."""
        response = client.get("/api/v1/export/csv/browse?state=NV")
        assert response.status_code == 200
        
        content_disposition = response.headers.get("content-disposition", "")
        assert "NV" in content_disposition, f"Filename should include state: {content_disposition}"

    def test_browse_export_invalid_state_rejected(self, client: TestClient) -> None:
        """Invalid state code (>2 chars) is rejected."""
        response = client.get("/api/v1/export/csv/browse?state=INVALID")
        assert response.status_code == 422  # Validation error

    def test_browse_export_limit_max_5000(self, client: TestClient) -> None:
        """Browse endpoint allows up to 5000 rows (higher than spatial endpoint)."""
        response = client.get("/api/v1/export/csv/browse?limit=5000")
        assert response.status_code == 200
        
    def test_browse_export_limit_exceeds_max(self, client: TestClient) -> None:
        """Limit >5000 is rejected."""
        response = client.get("/api/v1/export/csv/browse?limit=5001")
        assert response.status_code == 422
