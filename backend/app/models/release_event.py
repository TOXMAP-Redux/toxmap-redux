"""SQLAlchemy ORM model: release_events table.

Story 1.1.2 — release_events + indexes.

Column semantics (critical — read before modifying):
- total_release_lbs: TRI Field 65 (ON-SITE RELEASE TOTAL). Sum of the four medium
  breakdown columns. Does NOT include off-site transfers (Field 107).
- air_release_lbs: fugitive air (Field 51) + stack air (Field 52).
- water_release_lbs: Field 53 (single column).
- land_release_lbs: sum of Fields 57-64 (see LAND_RELEASE_FIELDS in tri_parser.py).
- underground_release_lbs: Class I wells (Field 55) + Class II-V wells (Field 56).
- off_site_lbs: Field 88 (OFF-SITE RELEASE TOTAL). Stored for completeness; not displayed.
- unit_of_measure: 'Pounds' for all chemicals; 'Grams' for dioxin/dioxin-like (N150).
  Source: TRI Field 50. The column names ending in _lbs are accurate only for 'Pounds' rows.
- form_type: 'R' = Form R (quantities present). 'A' = Form A Certification (all zeros
  are certification artifacts, not measured zero-release events).
"""

from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReleaseEvent(Base):
    """Annual TRI release event: one row per facility × chemical × year."""

    __tablename__ = "release_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"), nullable=False)
    chemical_id: Mapped[int] = mapped_column(ForeignKey("chemicals.id"), nullable=False)
    reporting_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # On-site release total (TRI Field 65). NULL = data absent; 0 = reported zero releases.
    total_release_lbs: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    # Medium breakdowns
    air_release_lbs: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    water_release_lbs: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    land_release_lbs: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    underground_release_lbs: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    # Off-site transfers (TRI Field 88) — stored, not displayed in current UI
    off_site_lbs: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    # 'Pounds' for all non-dioxin chemicals; 'Grams' for dioxin/dioxin-like (N150)
    unit_of_measure: Mapped[str] = mapped_column(String(6), nullable=False, default="Pounds")

    # 'R' = Form R (full quantities). 'A' = Form A Certification (all zeros; no data).
    form_type: Mapped[str] = mapped_column(String(1), nullable=False, default="R")

    facility: Mapped["Facility"] = relationship(back_populates="releases")  # noqa: F821
    chemical: Mapped["Chemical"] = relationship(back_populates="releases")  # noqa: F821

    __table_args__ = (
        Index("idx_releases_facility", "facility_id"),
        Index("idx_releases_year", "reporting_year"),
        Index("idx_releases_chemical", "chemical_id"),
    )
