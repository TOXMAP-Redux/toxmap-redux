"""Add trigram indexes for facility search autocomplete (ADR-010).

Revision ID: f1a2b3c4d5e6
Revises: e5a7c3b9d2f4
Create Date: 2026-08-07

ADR-010: Facility Search Autocomplete (ID and Name)
- pg_trgm extension for fast ILIKE %query% pattern matching
- GIN index on facilities.name for name search (< 100ms SLA)
- B-tree pattern_ops index on tri_facility_id for prefix search

See: docs/adr/ADR-010-facility-search-autocomplete.md
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "e5a7c3b9d2f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pg_trgm extension for trigram-based text search
    # This extension is included in standard PostGIS images
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # GIN index for fast ILIKE %query% on facility name
    # Enables < 100ms autocomplete on ~22K facilities
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_facilities_name_trgm
        ON facilities USING GIN (name gin_trgm_ops)
    """)

    # Pattern ops index for prefix searches on TRI ID (e.g., "89319%")
    # Uses varchar_pattern_ops for efficient LIKE 'prefix%' queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_facilities_tri_id_pattern
        ON facilities (tri_facility_id varchar_pattern_ops)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_facilities_tri_id_pattern")
    op.execute("DROP INDEX IF EXISTS idx_facilities_name_trgm")
    # Note: pg_trgm extension is left in place (may be used elsewhere)
