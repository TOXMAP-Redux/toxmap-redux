"""SQLAlchemy ORM model: chemicals table.

Story 1.1.2 — chemicals table + partial unique index on non-null CAS numbers.

cas_number is nullable: TRI compound categories (e.g. LEAD COMPOUNDS = N420,
COPPER COMPOUNDS = N100) do not have CAS numbers assigned by CAS. A partial
unique index prevents duplicate non-null CAS values while allowing multiple
NULL rows (one per compound category).
"""

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Chemical(Base):
    """TRI chemical or compound category."""

    __tablename__ = "chemicals"

    id: Mapped[int] = mapped_column(primary_key=True)
    # cas_number is NULL for TRI compound categories (N-prefix IDs)
    cas_number: Mapped[str | None] = mapped_column(String(12))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(Text)
    atsdr_url: Mapped[str | None] = mapped_column(Text)
    pubchem_url: Mapped[str | None] = mapped_column(Text)

    releases: Mapped[list["ReleaseEvent"]] = relationship(  # noqa: F821
        back_populates="chemical"
    )

    __table_args__ = (
        # Partial unique index: unique on cas_number only where it is NOT NULL.
        # This allows multiple compound-category rows with cas_number = NULL.
        Index(
            "idx_chemicals_cas_number",
            "cas_number",
            unique=True,
            postgresql_where="cas_number IS NOT NULL",
        ),
    )
