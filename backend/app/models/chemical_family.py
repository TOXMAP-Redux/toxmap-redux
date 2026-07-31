"""SQLAlchemy ORM models: chemical_families and chemical_family_members tables.

ADR-007 — Chemical Families for Transparent Right-to-Know Search.

Groups related TRI chemicals (e.g., LEAD, LEAD COMPOUNDS, LEAD AND LEAD COMPOUNDS)
so citizen searches return complete release data.
"""

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ChemicalFamily(Base):
    """Parent element/compound group for TRI chemical expansion."""

    __tablename__ = "chemical_families"

    id: Mapped[int] = mapped_column(primary_key=True)
    family_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    nlm_url: Mapped[str | None] = mapped_column(String(500))
    epa_url: Mapped[str | None] = mapped_column(String(500))

    members: Mapped[list["ChemicalFamilyMember"]] = relationship(
        back_populates="family",
        cascade="all, delete-orphan",
    )


class ChemicalFamilyMember(Base):
    """Join table linking chemicals to their family."""

    __tablename__ = "chemical_family_members"

    chemical_id: Mapped[int] = mapped_column(
        ForeignKey("chemicals.id", ondelete="CASCADE"),
        primary_key=True,
    )
    family_id: Mapped[int] = mapped_column(
        ForeignKey("chemical_families.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_parent: Mapped[bool] = mapped_column(Boolean, default=False)

    family: Mapped["ChemicalFamily"] = relationship(back_populates="members")
    chemical: Mapped["Chemical"] = relationship()  # noqa: F821
