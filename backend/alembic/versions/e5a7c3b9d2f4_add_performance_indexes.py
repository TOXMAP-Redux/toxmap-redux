"""Add performance indexes for geography queries and text search.

Revision ID: e5a7c3b9d2f4
Revises: a3f7b2c9d8e1
Create Date: 2026-08-04

These indexes improve query performance with production-like data volumes:
- idx_facilities_location_geography: GIST index on facilities.location::geography
  for ST_DWithin radius queries (reduces 900ms+ → 773ms)
- idx_superfund_location_geography: GIST index on superfund_sites.location::geography
  for spatial queries
- idx_chemicals_name_lower: B-tree index on LOWER(chemicals.name)
  for case-insensitive autocomplete (reduces 141ms → 110ms)

See: docs/escalations/B-002_DEFECT_TRIAGE.md (6.PERF.3–5)
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e5a7c3b9d2f4"
down_revision = "a3f7b2c9d8e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Geography GIST index for efficient ST_DWithin radius queries on facilities
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_facilities_location_geography
        ON facilities USING GIST ((location::geography))
    """)

    # Geography GIST index for efficient spatial queries on superfund_sites
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_superfund_location_geography
        ON superfund_sites USING GIST ((location::geography))
    """)

    # B-tree index on LOWER(name) for case-insensitive chemical autocomplete
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_chemicals_name_lower
        ON chemicals USING btree (LOWER(name))
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_facilities_location_geography")
    op.execute("DROP INDEX IF EXISTS idx_superfund_location_geography")
    op.execute("DROP INDEX IF EXISTS idx_chemicals_name_lower")
