"""Pydantic response schemas for Superfund site endpoints.

Phase 2 — stories 2.6.x.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class SuperfundFeatureProperties(BaseModel):
    id: int
    epa_id: str
    name: str
    city: str | None = None
    state_code: str | None = None
    status: str | None = None
    hrs_score: float | None = None
    npl_date: str | None = None
    contaminants: list[str] = []
    marker_shape: str = "diamond"


class SuperfundFeature(BaseModel):
    type: str = "Feature"
    geometry: dict[str, Any]
    properties: SuperfundFeatureProperties


class SuperfundCollectionMeta(BaseModel):
    total_count: int


class SuperfundCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[SuperfundFeature]
    meta: SuperfundCollectionMeta


class SuperfundContaminant(BaseModel):
    name: str
    cas_number: str | None = None
    atsdr_url: str | None = None
    pubchem_url: str | None = None


class SuperfundDetail(BaseModel):
    id: int
    epa_id: str
    name: str
    address: str | None = None
    city: str | None = None
    state_code: str | None = None
    zip_code: str | None = None
    county: str | None = None
    status: str | None = None
    hrs_score: float | None = None
    npl_date: str | None = None
    contaminants: list[SuperfundContaminant] = []
    epa_progress_url: str | None = None
    location: dict[str, float]
