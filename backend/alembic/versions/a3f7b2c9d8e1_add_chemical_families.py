"""add_chemical_families

Revision ID: a3f7b2c9d8e1
Revises: d99ef6c86f0c
Create Date: 2026-07-31 19:00:00.000000

ADR-007: Chemical Families for Transparent Right-to-Know Search

Adds tables for grouping related TRI chemicals (e.g., LEAD, LEAD COMPOUNDS,
LEAD AND LEAD COMPOUNDS) so citizen searches return complete release data.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3f7b2c9d8e1"
down_revision: str | None = "d99ef6c86f0c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Chemical families table (parent element/compound groups)
    op.create_table(
        "chemical_families",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("nlm_url", sa.String(500), nullable=True),
        sa.Column("epa_url", sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_name", name="uq_chemical_families_name"),
    )
    op.create_index(
        "idx_chemical_families_name",
        "chemical_families",
        ["family_name"],
        unique=False,
    )

    # Join table linking chemicals to their family
    op.create_table(
        "chemical_family_members",
        sa.Column("chemical_id", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("is_parent", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["chemical_id"], ["chemicals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["family_id"], ["chemical_families.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chemical_id", "family_id"),
    )
    op.create_index(
        "idx_chemical_family_members_family",
        "chemical_family_members",
        ["family_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_chemical_family_members_family", table_name="chemical_family_members")
    op.drop_table("chemical_family_members")
    op.drop_index("idx_chemical_families_name", table_name="chemical_families")
    op.drop_table("chemical_families")
