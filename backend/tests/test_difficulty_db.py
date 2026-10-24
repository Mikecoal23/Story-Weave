"""select_difficulty_target against a real (throwaway) schema, local Postgres only.

These skip, loudly, when no local Postgres is running. The frozen-contract tests in
test_difficulty.py always run.
"""

from collections.abc import Generator

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from support import throwaway_schema

from app.models import (
    Caregiver,
    Child,
    PhonicsMastery,
    PhonicsPattern,
    VocabularyWord,
    VocabularyWordPattern,
)
from app.services.difficulty import select_difficulty_target

# The seed also writes vocabulary rows, so those tables are created too.
TABLES = [
    Caregiver.__table__,
    Child.__table__,
    PhonicsPattern.__table__,
    PhonicsMastery.__table__,
    VocabularyWord.__table__,
    VocabularyWordPattern.__table__,
]


@pytest.fixture
def db() -> Generator[Session, None, None]:
    with throwaway_schema(
        "difficulty_test", TABLES, not_tested="select_difficulty_target"
    ) as session:
        yield session


def make_child(db: Session) -> Child:
    caregiver = Caregiver(display_name="Test Caregiver")
    db.add(caregiver)
    db.flush()
    child = Child(caregiver_id=caregiver.id, display_name="Test Child", grade_level=1)
    db.add(child)
    db.flush()
    return child


def pattern_ids(db: Session) -> list[int]:
    """Seeded pattern ids in sequence_order order."""
    return list(
        db.scalars(
            select(PhonicsPattern.phonics_pattern_id).order_by(PhonicsPattern.sequence_order)
        )
    )


def set_mastery(db: Session, child: Child, pattern_id: int, score: float, attempts: int) -> None:
    db.add(
        PhonicsMastery(
            child_id=child.id,
            phonics_pattern_id=pattern_id,
            mastery_score=score,
            attempts_count=attempts,
            correct_count=round(score * attempts),
        )
    )
    db.flush()


def test_a_child_with_no_data_gets_the_first_two_patterns(db: Session) -> None:
    child = make_child(db)
    ids = pattern_ids(db)

    target = select_difficulty_target(db, child.id)

    assert target.child_id == child.id
    assert target.reinforce_pattern_ids == ()
    assert target.stretch_pattern_ids == tuple(ids[:2])


def test_mastered_patterns_are_reinforced_and_stretch_moves_on(db: Session) -> None:
    child = make_child(db)
    ids = pattern_ids(db)
    set_mastery(db, child, ids[0], score=0.9, attempts=10)

    target = select_difficulty_target(db, child.id)

    assert target.reinforce_pattern_ids == (ids[0],)
    assert target.stretch_pattern_ids == (ids[1], ids[2])


def test_threshold_is_inclusive_at_80_percent_and_5_attempts(db: Session) -> None:
    child = make_child(db)
    ids = pattern_ids(db)
    set_mastery(db, child, ids[0], score=0.8, attempts=5)

    assert select_difficulty_target(db, child.id).reinforce_pattern_ids == (ids[0],)


def test_a_high_score_with_too_few_attempts_is_not_mastered(db: Session) -> None:
    child = make_child(db)
    ids = pattern_ids(db)
    set_mastery(db, child, ids[0], score=1.0, attempts=4)

    target = select_difficulty_target(db, child.id)

    assert target.reinforce_pattern_ids == ()
    assert target.stretch_pattern_ids == tuple(ids[:2])


def test_enough_attempts_with_a_low_score_is_not_mastered(db: Session) -> None:
    child = make_child(db)
    ids = pattern_ids(db)
    set_mastery(db, child, ids[0], score=0.79, attempts=20)

    assert select_difficulty_target(db, child.id).reinforce_pattern_ids == ()


def test_a_gap_in_the_sequence_stays_in_stretch(db: Session) -> None:
    # Pattern 2 is mastered but pattern 1 is not: stretch still starts at the lowest
    # unmastered pattern, and reinforce lists only what was actually mastered.
    child = make_child(db)
    ids = pattern_ids(db)
    set_mastery(db, child, ids[1], score=0.95, attempts=8)

    target = select_difficulty_target(db, child.id)

    assert target.reinforce_pattern_ids == (ids[1],)
    assert target.stretch_pattern_ids == (ids[0], ids[2])


def test_reinforce_is_in_sequence_order(db: Session) -> None:
    child = make_child(db)
    ids = pattern_ids(db)
    set_mastery(db, child, ids[2], score=0.9, attempts=6)
    set_mastery(db, child, ids[0], score=0.9, attempts=6)

    assert select_difficulty_target(db, child.id).reinforce_pattern_ids == (ids[0], ids[2])


def test_another_childs_mastery_is_ignored(db: Session) -> None:
    child = make_child(db)
    other = make_child(db)
    ids = pattern_ids(db)
    set_mastery(db, other, ids[0], score=1.0, attempts=50)

    target = select_difficulty_target(db, child.id)

    assert target.reinforce_pattern_ids == ()
    assert target.stretch_pattern_ids == tuple(ids[:2])


def test_when_everything_is_mastered_stretch_is_empty(db: Session) -> None:
    child = make_child(db)
    ids = pattern_ids(db)
    for pattern_id in ids:
        set_mastery(db, child, pattern_id, score=0.9, attempts=10)

    target = select_difficulty_target(db, child.id)

    assert target.reinforce_pattern_ids == tuple(ids)
    assert target.stretch_pattern_ids == ()
