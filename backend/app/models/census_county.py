"""SQLAlchemy ORM model: census_county table.

Story 1.1.3 — census_county + PostGIS MULTIPOLYGON boundary + indexes.
NLM 2006-2013 enhancement: US Census demographic overlays.

Health/mortality columns (T-09 scenario):
- cancer_mortality_female_per_100k: female cancer mortality rate
- cancer_mortality_male_per_100k: male cancer mortality rate
- heart_disease_mortality_per_100k: heart disease mortality rate

The co-occurrence disclaimer in the UI appears on the mortality tab only
(UX invariant 10) — not on income or population tabs.
"""

from decimal import Decimal

from geoalchemy2 import Geometry
from sqlalchemy import Index, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CensusCounty(Base):
    """US Census county with demographic data and MULTIPOLYGON boundary."""

    __tablename__ = "census_county"

    id: Mapped[int] = mapped_column(primary_key=True)
    # fips_code: 5-digit state+county FIPS (e.g. '51187' = Warren County VA)
    fips_code: Mapped[str] = mapped_column(String(5), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    state_code: Mapped[str | None] = mapped_column(String(2))
    census_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # Population demographics
    total_pop: Mapped[int | None] = mapped_column(Integer)
    median_income: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    pct_under_18: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    pct_over_65: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    pct_nonwhite: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    # Health/mortality overlays (T-09; co-occurrence disclaimer on mortality tab only)
    cancer_mortality_female_per_100k: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    cancer_mortality_male_per_100k: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    heart_disease_mortality_per_100k: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))

    # County boundary polygon for choropleth overlay
    boundary: Mapped[object | None] = mapped_column(Geometry("MULTIPOLYGON", srid=4326))

    __table_args__ = (Index("idx_county_boundary", "boundary", postgresql_using="gist"),)
