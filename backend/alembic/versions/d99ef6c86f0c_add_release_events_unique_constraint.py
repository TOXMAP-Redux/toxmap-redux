"""add_release_events_unique_constraint

Revision ID: d99ef6c86f0c
Revises: 9fdbd155f1dd
Create Date: 2026-07-26 19:36:53.192639

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d99ef6c86f0c"
down_revision: str | None = "9fdbd155f1dd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Unique constraint: one row per facility × chemical × year.
    # Enables ON CONFLICT (facility_id, chemical_id, reporting_year) DO NOTHING
    # in tri_ingest.py so re-running ingestion is idempotent.
    op.create_unique_constraint(
        "uq_release_events_fac_chem_year",
        "release_events",
        ["facility_id", "chemical_id", "reporting_year"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_release_events_fac_chem_year",
        "release_events",
        type_="unique",
    )
