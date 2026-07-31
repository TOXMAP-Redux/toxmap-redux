"""SQLAlchemy ORM models package.

Import all models here so Alembic's autogenerate can discover them when
``env.py`` imports this module (via ``from app.models import *``).

Story 1.1.1–1.1.3: all 7 tables defined.
ADR-007: Chemical families for transparent right-to-know search.
"""

from app.models.census_county import CensusCounty
from app.models.chemical import Chemical
from app.models.chemical_family import ChemicalFamily, ChemicalFamilyMember
from app.models.facility import Facility
from app.models.npri_facility import NpriFacility
from app.models.nuclear_plant import NuclearPlant
from app.models.release_event import ReleaseEvent
from app.models.superfund_site import SuperfundSite

__all__ = [
    "CensusCounty",
    "Chemical",
    "ChemicalFamily",
    "ChemicalFamilyMember",
    "Facility",
    "NpriFacility",
    "NuclearPlant",
    "ReleaseEvent",
    "SuperfundSite",
]
