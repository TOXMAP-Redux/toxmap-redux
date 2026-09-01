"""Add trigram and GIN indexes for Superfund site search (ADR-010, Algorithms Handbook).

Revision ID: g2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-08-20

Algorithms Handbook §10 High-Priority Recommendations:
1. idx_superfund_name_trgm: GIN trigram index for ILIKE name search (Phase 1)
2. idx_superfund_contaminants_gin: GIN index for array containment queries (Phase 3)

These indexes benefit dev mode (FastAPI + PostgreSQL) and API fallback users (~5%).
Production mode (DuckDB WASM) does not use PostgreSQL.

See: docs/onboarding/ALGORITHMS_HANDBOOK.md §10
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "g2b3c4d5e6f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Phase 1: GIN trigram index for fast ILIKE %query% on site name
    # pg_trgm extension already enabled by f1a2b3c4d5e6
    # Enables < 100ms autocomplete on ~1,700 Superfund sites
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_superfund_name_trgm
        ON superfund_sites USING GIN (name gin_trgm_ops)
    """)

    # Phase 3: GIN index for contaminants array containment queries
    # Enables indexed @> (array contains) and ANY() queries
    # Replaces slow array_to_string().ilike() pattern
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_superfund_contaminants_gin
        ON superfund_sites USING GIN (contaminants)
    """)

    # Pattern ops index for prefix searches on EPA ID (e.g., "VAD07%")
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_superfund_epa_id_pattern
        ON superfund_sites (epa_id varchar_pattern_ops)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_superfund_epa_id_pattern")
    op.execute("DROP INDEX IF EXISTS idx_superfund_contaminants_gin")
    op.execute("DROP INDEX IF EXISTS idx_superfund_name_trgm")
