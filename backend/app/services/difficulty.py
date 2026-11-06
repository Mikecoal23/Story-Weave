from collections.abc import Mapping, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PhonicsMastery, PhonicsPattern
from app.schemas.difficulty import DifficultyTarget

# A pattern counts as mastered once the child has tried it at least MIN_ATTEMPTS times AND
# its confidence score (see `confidence`) is at least MASTERY_THRESHOLD. The dashboard
# imports both numbers.
MASTERY_THRESHOLD = 0.8
MIN_ATTEMPTS = 5
# At most this many patterns in each list, so a story asks for 4 patterns at most.
REINFORCE_COUNT = 2
STRETCH_COUNT = 2


def confidence(correct: int, attempts: int) -> float:
    """The share of words read right, pulled toward 0.5 when there are few attempts.

    It counts one extra right and one extra wrong read, so 5 out of 5 gives 6/7 (0.857),
    not 1.0: a short lucky run can't look like mastery. With many attempts it gets close
    to the plain share (17 out of 20 gives 18/22, 0.818).
    """
    return (correct + 1) / (attempts + 2)


def is_mastered(correct: int, attempts: int) -> bool:
    return attempts >= MIN_ATTEMPTS and confidence(correct, attempts) >= MASTERY_THRESHOLD


def pick_patterns(
    pattern_ids: Sequence[int], counts: Mapping[int, tuple[int, int]]
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Split pattern ids (given in `sequence_order` order) into (reinforce, stretch).

    `counts` maps a pattern id to the child's (correct, attempts); a pattern that isn't
    there has never been tried.
    - reinforce: the REINFORCE_COUNT mastered patterns with the LOWEST confidence, so the
      shakiest mastered ones get practised. A tie goes to the earlier pattern. Returned in
      `sequence_order` order.
    - stretch: the first STRETCH_COUNT patterns that aren't mastered, including ones the
      child has tried a few times and ones that dropped back below the threshold.
    """
    mastered = [p for p in pattern_ids if p in counts and is_mastered(*counts[p])]
    unmastered = [p for p in pattern_ids if p not in mastered]
    # sorted() is stable, so equal confidences stay in sequence order (earlier wins).
    weakest = sorted(mastered, key=lambda p: confidence(*counts[p]))[:REINFORCE_COUNT]
    reinforce = tuple(p for p in mastered if p in weakest)
    return reinforce, tuple(unmastered[:STRETCH_COUNT])


def select_difficulty_target(session: Session, child_id: UUID) -> DifficultyTarget:
    """Choose the phonics patterns a child's next story should use (rules in `pick_patterns`).

    A new child (no mastery rows) gets no reinforce patterns and the first two patterns
    in the sequence to stretch. Mastery uses `correct_count` and `attempts_count`, not the
    stored `mastery_score`, so few attempts count for less.

    The signature (session, child_id) is part of the frozen contract, so don't change it
    without a Decisions Log entry.
    """
    pattern_ids = session.scalars(
        select(PhonicsPattern.phonics_pattern_id).order_by(PhonicsPattern.sequence_order)
    ).all()
    counts = {
        row.phonics_pattern_id: (row.correct_count, row.attempts_count)
        for row in session.scalars(
            select(PhonicsMastery).where(PhonicsMastery.child_id == child_id)
        )
    }
    reinforce, stretch = pick_patterns(pattern_ids, counts)
    return DifficultyTarget(
        child_id=child_id,
        reinforce_pattern_ids=reinforce,
        stretch_pattern_ids=stretch,
    )
