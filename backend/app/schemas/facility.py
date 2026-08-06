"""Pydantic response schemas for facility and release-event endpoints.

Phase 2 — story 2.1.1 through 2.3.x.
ADR-007 — Chemical families for transparent right-to-know search.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Color-band helper
# ---------------------------------------------------------------------------


def assign_color_band(total_lbs: float | None) -> str:
    """Map total release pounds to a NLM color band."""
    if total_lbs is None:
        return "green"
    if total_lbs >= 100_000:
        return "red"
    if total_lbs >= 10_000:
        return "orange"
    if total_lbs >= 1_000:
        return "yellow"
    return "green"


# ---------------------------------------------------------------------------
# ADR-007: Chemical family search expansion
# ---------------------------------------------------------------------------


class SearchExpansion(BaseModel):
    """Info about chemical family search expansion (ADR-007)."""

    expanded: bool = False
    family_name: str | None = None
    searched_chemicals: list[str] = []
    description: str | None = None
    nlm_url: str | None = None
    epa_note: str = (
        "Facilities may report this element and its compounds separately or combined. "
        "Results include all related reporting categories."
    )


# ---------------------------------------------------------------------------
# GET /api/v1/facilities — FeatureCollection
# ---------------------------------------------------------------------------


class FacilityFeatureProperties(BaseModel):
    id: int
    tri_facility_id: str
    name: str
    city: str | None = None
    state_code: str | None = None
    naics_code: str | None = None
    naics_desc: str | None = None
    total_release_lbs: float | None = None
    reporting_year: int
    color_band: str
    unit_of_measure: str = "Pounds"
    marker_shape: str = "circle"


class FacilityFeature(BaseModel):
    type: str = "Feature"
    geometry: dict[str, Any]
    properties: FacilityFeatureProperties


class FacilityCollectionMeta(BaseModel):
    total_count: int
    returned_count: int
    truncated: bool
    query: dict[str, Any]
    # ADR-007: Search expansion info when chemical family is expanded
    search_expansion: SearchExpansion | None = None


class FacilityCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[FacilityFeature]
    meta: FacilityCollectionMeta


# ---------------------------------------------------------------------------
# GET /api/v1/facilities/{tri_facility_id} — FacilityDetail
# ---------------------------------------------------------------------------


class TopChemical(BaseModel):
    chemical_name: str
    cas_number: str | None = None
    total_release_lbs: float
    unit_of_measure: str = "Pounds"
    atsdr_url: str | None = None
    pubchem_url: str | None = None


class FacilityDetail(BaseModel):
    id: int
    tri_facility_id: str
    name: str
    address: str | None = None
    city: str | None = None
    state_code: str | None = None
    zip_code: str | None = None
    county: str | None = None
    naics_code: str | None = None
    naics_desc: str | None = None
    location: dict[str, float]
    latest_year: int | None = None
    top_chemicals: list[TopChemical]
    # 7.BUG.29: All-years aggregate for TOTAL row + "Other chemicals" calculation
    total_release_lbs: float | None = None


# ---------------------------------------------------------------------------
# GET /api/v1/facilities/{tri_facility_id}/releases — ReleaseEventSchema
# ---------------------------------------------------------------------------


class ReleaseEventSchema(BaseModel):
    reporting_year: int
    chemical_name: str
    cas_number: str | None = None
    total_release_lbs: float | None = None
    air_release_lbs: float | None = None
    water_release_lbs: float | None = None
    land_release_lbs: float | None = None
    underground_release_lbs: float | None = None
    off_site_lbs: float | None = None  # TRI Field 88 — off-site transfers
    unit_of_measure: str
    form_type: str


# ---------------------------------------------------------------------------
# GET /api/v1/releases/largest — LargestReleaseResponse
# ---------------------------------------------------------------------------


class LargestReleaseResponse(BaseModel):
    tri_facility_id: str
    name: str
    city: str | None = None
    state_code: str
    chemical_name: str
    cas_number: str | None = None
    reporting_year: int
    total_release_lbs: float
    unit_of_measure: str
    location: dict[str, float]
