"""SQLAlchemy ORM model: nuclear_plants table.

Story 1.1.3 — nuclear_plants + PostGIS POINT geometry.
NLM 2013 redesign: optional nuclear plant layer.
"""

from geoalchemy2 import Geometry
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NuclearPlant(Base):
    """U.S. commercial nuclear power plant (optional overlay layer)."""

    __tablename__ = "nuclear_plants"

    id: Mapped[int] = mapped_column(primary_key=True)
    plant_name: Mapped[str] = mapped_column(Text, nullable=False)
    operator: Mapped[str | None] = mapped_column(Text)
    state_code: Mapped[str | None] = mapped_column(String(2))
    # status: 'Operating', 'Shutdown', etc.
    status: Mapped[str | None] = mapped_column(Text)
    location: Mapped[object] = mapped_column(Geometry("POINT", srid=4326), nullable=False)
