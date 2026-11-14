from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PhonicsMastery, PhonicsPattern
from app.schemas.difficulty import DifficultyTarget

# A pattern counts as mastered once the child has tried it at least MIN_ATTEMPTS times AND
# its confidence score (see `confidence`) is at least MASTERY_THRESHOLD.
MASTERY_THRESHOLD = 0.8
MIN_ATTEMPTS = 5
# At most this many patterns in each list, so a story asks for 4 patterns at most.
REINFORCE_COUNT = 2
STRETCH_COUNT = 2
# Stands in for "never practised": earlier than any real time, so such a pattern sorts first.
NEVER_PRACTISED = datetime(1970, 1, 1, tzinfo=UTC)


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
    pattern_ids: Sequence[int],
    counts: Mapping[int, tuple[int, int]],
    last_practised: Mapping[int, datetime] | None = None,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Split pattern ids (given in `sequence_order` order) into (reinforce, stretch).

    `counts` maps a pattern id to the child's (correct, attempts); a pattern that isn't
    there has never been tried. `last_practised` maps a pattern id to when the child last
    read it; a pattern that isn't there (or no mapping at all) counts as never practised.
    Pure: the caller reads the database and the clock is never called here.
    - reinforce: the REINFORCE_COUNT mastered patterns practised LONGEST AGO, never-practised
      ones first. Equal times go to the lowest confidence, then to the earlier pattern.
      Returned in `sequence_order` order.
    - stretch: the first STRETCH_COUNT patterns that aren't mastered, including ones the
      child has tried a few times and ones that dropped back below the threshold.
    """
    last = last_practised or {}
    mastered = [p for p in pattern_ids if p in counts and is_mastered(*counts[p])]
    unmastered = [p for p in pattern_ids if p not in mastered]
    # sorted() is stable, so a full tie stays in sequence order (earlier wins).
    longest_ago = sorted(
        mastered, key=lambda p: (last.get(p, NEVER_PRACTISED), confidence(*counts[p]))
    )[:REINFORCE_COUNT]
    reinforce = tuple(p for p in mastered if p in longest_ago)
    return reinforce, tuple(unmastered[:STRETCH_COUNT])


def select_difficulty_target(session: Session, child_id: UUID) -> DifficultyTarget:
    """Choose the phonics patterns a child's next story should use (rules in `pick_patterns`).

    A new child (no mastery rows) gets no reinforce patterns and the first two patterns
    in the sequence to stretch. Mastery uses `correct_count` and `attempts_count`, not the
    stored `mastery_score`, so few attempts count for less. `last_practised_at` decides which
    mastered patterns are reinforced; a row that was never stamped counts as never practised.

    The signature (session, child_id) is part of the frozen contract, so don't change it
    without a Decisions Log entry.
    """
    pattern_ids = session.scalars(
        select(PhonicsPattern.phonics_pattern_id).order_by(PhonicsPattern.sequence_order)
    ).all()
    rows = session.scalars(select(PhonicsMastery).where(PhonicsMastery.child_id == child_id)).all()
    counts = {row.phonics_pattern_id: (row.correct_count, row.attempts_count) for row in rows}
    last_practised = {
        row.phonics_pattern_id: row.last_practised_at
        for row in rows
        if row.last_practised_at is not None
    }
    reinforce, stretch = pick_patterns(pattern_ids, counts, last_practised)
    return DifficultyTarget(
        child_id=child_id,
        reinforce_pattern_ids=reinforce,
        stretch_pattern_ids=stretch,
    )
