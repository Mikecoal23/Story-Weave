"""Persist articulation-vs-unclassified scoring outcomes.

Revision ID: 4d8ac9f62e11
Revises: 9cde937f7a48
Create Date: 2026-11-02
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "4d8ac9f62e11"
down_revision: str | None = "9cde937f7a48"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "reading_attempt",
        sa.Column("error_classification", sa.String(length=20), nullable=True),
    )
    op.create_check_constraint(
        "ck_reading_attempt_error_classification",
        "reading_attempt",
        "error_classification IS NULL OR "
        "error_classification IN ('articulation', 'unclassified')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_reading_attempt_error_classification",
        "reading_attempt",
        type_="check",
    )
    op.drop_column("reading_attempt", "error_classification")
