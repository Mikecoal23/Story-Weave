"""Add caregiver PIN hashes and encrypted child PINs.

Revision ID: 4f2a9c1d8b63
Revises: daca9dcb1e3e
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "4f2a9c1d8b63"
down_revision: str | None = "daca9dcb1e3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("caregiver", sa.Column("pin_hash", sa.String(length=128), nullable=True))
    op.add_column(
        "caregiver",
        sa.Column("pin_failed_attempts", sa.SmallInteger(), server_default="0", nullable=False),
    )
    op.add_column(
        "caregiver", sa.Column("pin_locked_until", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("child", sa.Column("pin_ciphertext", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("child", "pin_ciphertext")
    op.drop_column("caregiver", "pin_locked_until")
    op.drop_column("caregiver", "pin_failed_attempts")
    op.drop_column("caregiver", "pin_hash")
