"""Pydantic response schemas for demographics endpoints.

Phase 2 — story 2.4.x.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

# Units are defined by the Census schema — hardcoded per API contract §demographics.
DEMOGRAPHICS_UNITS: dict[str, str] = {
    "total_pop": "people",
    "median_income": "$",
    "pct_under_18": "%",
    "pct_over_65": "%",
    "pct_nonwhite": "%",
    "cancer_mortality_female_per_100k": "per 100,000",
}


class DemographicsFeatureProperties(BaseModel):
    fips_code: str
    name: str
    state_code: str | None = None
    census_year: int
    total_pop: int | None = None
    median_income: float | None = None
    pct_under_18: float | None = None
    pct_over_65: float | None = None
    pct_nonwhite: float | None = None
    cancer_mortality_female_per_100k: float | None = None


class DemographicsCollectionMeta(BaseModel):
    total_count: int
    census_year: int
    state: str | None = None
    units: dict[str, str]


class DemographicsFeature(BaseModel):
    type: str = "Feature"
    geometry: dict[str, Any]
    properties: DemographicsFeatureProperties


class DemographicsCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[DemographicsFeature]
    meta: DemographicsCollectionMeta
