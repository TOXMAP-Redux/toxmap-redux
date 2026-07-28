"""SQLAlchemy ORM model: npri_facilities table.

Story 1.1.3 — npri_facilities + PostGIS POINT geometry.
NLM 2013 redesign: optional Canadian National Pollutant Release Inventory layer.
"""

from geoalchemy2 import Geometry
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NpriFacility(Base):
    """Canadian NPRI facility (optional overlay layer)."""

    __tablename__ = "npri_facilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    npri_id: Mapped[str] = mapped_column(String(12), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    province: Mapped[str | None] = mapped_column(String(2))
    location: Mapped[object] = mapped_column(Geometry("POINT", srid=4326), nullable=False)
