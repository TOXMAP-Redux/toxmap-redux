"""Pydantic response schemas for chemical endpoints.

Phase 2 — stories 2.5.x.
ADR-007 — Chemical families for transparent right-to-know search.
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


class ChemicalFamilyInfo(BaseModel):
    """Info about a chemical family for search expansion."""

    family_name: str
    description: str | None = None
    nlm_url: str | None = None
    epa_url: str | None = None
    member_chemicals: list[str]  # Names of all chemicals in the family


class ChemicalSearch(BaseModel):
    id: int
    cas_number: str | None = None
    name: str
    atsdr_url: str | None = None
    pubchem_url: str | None = None
    # ADR-007: Family info for search expansion
    family: ChemicalFamilyInfo | None = None
