"""Pydantic response schemas for chemical endpoints.

Phase 2 — stories 2.5.x.
"""

from __future__ import annotations

from pydantic import BaseModel


class ChemicalSummary(BaseModel):
    id: int
    cas_number: str | None = None
    name: str
    category: str | None = None
    atsdr_url: str | None = None
    pubchem_url: str | None = None


class ChemicalSearch(BaseModel):
    id: int
    cas_number: str | None = None
    name: str
    atsdr_url: str | None = None
    pubchem_url: str | None = None
