"""Pydantic response schema for GET /api/v1/meta.

Phase 2 — story 2.7.3.
"""

from __future__ import annotations

from pydantic import BaseModel


class MetaResponse(BaseModel):
    vintage_label: str
    build_date: str
    available_years: list[int]
    latest_year: int | None = None
    total_facility_count: int
    total_release_event_count: int
    source: str = "fastapi-dev"
