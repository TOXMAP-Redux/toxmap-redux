"""SQLAlchemy ORM model: superfund_sites table.

Story 1.1.3 — superfund_sites + PostGIS POINT geometry + indexes.
NLM 2006 enhancement: Superfund/NPL sites overlay.
"""

from decimal import Decimal

from geoalchemy2 import Geometry
from sqlalchemy import ARRAY, Date, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SuperfundSite(Base):
    """EPA Superfund / NPL site with PostGIS point geometry (SRID 4326)."""

    __tablename__ = "superfund_sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    # epa_id: EPA CERCLIS alphanumeric site ID (e.g. WAD009248671)
    epa_id: Mapped[str] = mapped_column(String(12), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    state_code: Mapped[str | None] = mapped_column(String(2))
    county: Mapped[str | None] = mapped_column(Text)
    zip_code: Mapped[str | None] = mapped_column(String(10))
    # status: 'NPL', 'CERCLIS', 'Deleted', etc.
    status: Mapped[str | None] = mapped_column(Text)
    # hrs_score: Hazard Ranking System score (0-100)
    hrs_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    npl_date: Mapped[object | None] = mapped_column(Date)
    epa_progress_url: Mapped[str | None] = mapped_column(Text)
    # contaminants: PostgreSQL text array of primary contaminant names
    contaminants: Mapped[object | None] = mapped_column(ARRAY(Text))
    location: Mapped[object] = mapped_column(Geometry("POINT", srid=4326), nullable=False)

    __table_args__ = (
        Index("idx_superfund_location", "location", postgresql_using="gist"),
        Index("idx_superfund_state", "state_code"),
    )
