from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PhonicsMastery, PhonicsPattern
from app.schemas.difficulty import DifficultyTarget

# A pattern counts as mastered once the child has tried it enough times for the score to
# mean something AND is right at least this often. Component 2 replaces both numbers in Sprint 3.
MASTERY_THRESHOLD = 0.8
MIN_ATTEMPTS = 5
STRETCH_COUNT = 2


def select_difficulty_target(session: Session, child_id: UUID) -> DifficultyTarget:
    """Choose the phonics patterns a child's next story should use.

    Naive first pass (Component 2 replaces this body in Sprint 3):
    - reinforce: every mastered pattern (score >= 0.8 with at least 5 attempts), in
      `sequence_order` order.
    - stretch: the 2 lowest-`sequence_order` patterns that are not mastered yet. A child
      with no mastery rows therefore gets the first two patterns in the sequence.

    The signature (session, child_id) is part of the frozen contract, so don't change it
    without a Decisions Log entry.
    """
    patterns = session.scalars(select(PhonicsPattern).order_by(PhonicsPattern.sequence_order)).all()
    mastery = {
        row.phonics_pattern_id: row
        for row in session.scalars(
            select(PhonicsMastery).where(PhonicsMastery.child_id == child_id)
        )
    }

    def is_mastered(pattern_id: int) -> bool:
        row = mastery.get(pattern_id)
        return (
            row is not None
            and row.attempts_count >= MIN_ATTEMPTS
            and float(row.mastery_score) >= MASTERY_THRESHOLD
        )

    reinforce = [p.phonics_pattern_id for p in patterns if is_mastered(p.phonics_pattern_id)]
    stretch = [p.phonics_pattern_id for p in patterns if not is_mastered(p.phonics_pattern_id)]
    return DifficultyTarget(
        child_id=child_id,
        reinforce_pattern_ids=tuple(reinforce),
        stretch_pattern_ids=tuple(stretch[:STRETCH_COUNT]),
    )
