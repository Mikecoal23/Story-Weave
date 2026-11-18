"""Add phonics_mastery.last_practised_at and story.source.

last_practised_at: when the child last read a word of the pattern, so the difficulty engine
can prefer patterns not practised recently.
source: whether a saved story came from the LLM or from a fallback template.
Both are nullable and have no backfill: existing rows stay NULL (never stamped / unknown).

Revision ID: daca9dcb1e3e
Revises: 9cde937f7a48
Create Date: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "daca9dcb1e3e"
down_revision: str | None = "4d8ac9f62e11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "phonics_mastery",
        sa.Column("last_practised_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("story", sa.Column("source", sa.String(length=20), nullable=True))
    op.create_check_constraint(
        "ck_story_source",
        "story",
        "source IS NULL OR source IN ('llm', 'fallback')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_story_source", "story", type_="check")
    op.drop_column("story", "source")
    op.drop_column("phonics_mastery", "last_practised_at")
