"""SQLAlchemy ORM model: facilities table.

Story 1.1.1 — facilities + PostGIS POINT geometry + GIST index.
"""

from geoalchemy2 import Geometry
from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Facility(Base):
    """TRI facility with PostGIS point geometry (SRID 4326)."""

    __tablename__ = "facilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    tri_facility_id: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    state_code: Mapped[str | None] = mapped_column(String(2))
    zip_code: Mapped[str | None] = mapped_column(String(10))
    county: Mapped[str | None] = mapped_column(Text)
    naics_code: Mapped[str | None] = mapped_column(String(6))
    naics_desc: Mapped[str | None] = mapped_column(Text)
    # frs_id: EPA Facility Registry Service ID — cross-program linkage
    frs_id: Mapped[str | None] = mapped_column(String(12))
    # primary_sic: original SIC code for pre-2006 data (RY 1987-2005)
    primary_sic: Mapped[str | None] = mapped_column(String(4))
    # location: WGS84 point geometry — required; not nullable
    location: Mapped[object] = mapped_column(Geometry("POINT", srid=4326), nullable=False)

    releases: Mapped[list["ReleaseEvent"]] = relationship(  # noqa: F821
        back_populates="facility", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_facilities_location", "location", postgresql_using="gist"),
        Index("idx_facilities_state", "state_code"),
    )
