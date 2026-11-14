"""`last_practised_at`: scoring stamps it, the difficulty engine reads it.

Real (throwaway) schema, local Postgres only; skips, loudly, when none is running.
"""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from support import throwaway_schema

from app.models import (
    Caregiver,
    Child,
    PhonicsMastery,
    PhonicsPattern,
    ReadingAttempt,
    ReadingSession,
    Story,
    StoryLine,
    StoryPattern,
    VocabularyWord,
    VocabularyWordPattern,
)
from app.schemas.scoring import ScoreResult, WordScore
from app.services.difficulty import select_difficulty_target
from app.services.scoring import process_line_score

TABLES = [
    Caregiver.__table__,
    Child.__table__,
    PhonicsPattern.__table__,
    PhonicsMastery.__table__,
    VocabularyWord.__table__,
    VocabularyWordPattern.__table__,
    Story.__table__,
    StoryPattern.__table__,
    StoryLine.__table__,
    ReadingSession.__table__,
    ReadingAttempt.__table__,
]


@pytest.fixture
def db() -> Generator[Session, None, None]:
    with throwaway_schema(
        "spaced_repetition_test", TABLES, not_tested="last_practised_at"
    ) as session:
        yield session


def start_reading(db: Session, line_text: str) -> tuple[ReadingSession, StoryLine]:
    caregiver = Caregiver(display_name="Test Caregiver")
    db.add(caregiver)
    db.flush()
    child = Child(caregiver_id=caregiver.id, display_name="Test Child", grade_level=1)
    db.add(child)
    db.flush()
    story = Story(child_id=child.id, title="Test", status="validated")
    db.add(story)
    db.flush()
    line = StoryLine(story_id=story.id, line_number=1, text=line_text)
    reading = ReadingSession(child_id=child.id, story_id=story.id)
    db.add_all([line, reading])
    db.flush()
    return reading, line


def read(db: Session, reading: ReadingSession, line: StoryLine, status: str = "mastered") -> None:
    score = ScoreResult(
        words=[WordScore(expected_word=w, status=status) for w in line.text.split()]
    )
    process_line_score(db, reading.id, line.id, score)


def stamps_by_code(db: Session, child_id) -> dict[str, datetime | None]:
    rows = db.execute(
        select(PhonicsPattern.code, PhonicsMastery.last_practised_at)
        .join(PhonicsPattern)
        .where(PhonicsMastery.child_id == child_id)
    )
    return dict(rows.all())


def add_mastery(db: Session, child_id, code: str, correct: int, attempts: int) -> None:
    pattern_id = db.scalar(
        select(PhonicsPattern.phonics_pattern_id).where(PhonicsPattern.code == code)
    )
    db.add(
        PhonicsMastery(
            child_id=child_id,
            phonics_pattern_id=pattern_id,
            mastery_score=correct / attempts,
            attempts_count=attempts,
            correct_count=correct,
        )
    )
    db.flush()


def reinforce_codes(db: Session, child_id) -> list[str]:
    target = select_difficulty_target(db, child_id)
    rows = db.execute(
        select(PhonicsPattern.code)
        .where(PhonicsPattern.phonics_pattern_id.in_(target.reinforce_pattern_ids))
        .order_by(PhonicsPattern.sequence_order)
    )
    return [code for (code,) in rows]


def test_scoring_a_pattern_word_stamps_last_practised_at(db: Session) -> None:
    reading, line = start_reading(db, "The blue lamp and black clock had fun.")
    before = datetime.now(UTC)

    read(db, reading, line)

    after = datetime.now(UTC)
    stamps = stamps_by_code(db, reading.child_id)
    assert set(stamps) == {"blend_bl", "blend_cl", "final_blend_mp"}
    assert all(before <= stamp <= after for stamp in stamps.values())
    assert len(set(stamps.values())) == 1  # one time for the whole line


def test_a_line_with_only_sight_words_stamps_nothing(db: Session) -> None:
    reading, line = start_reading(db, "The and had.")

    read(db, reading, line)

    assert stamps_by_code(db, reading.child_id) == {}


def test_a_re_read_stamps_the_pattern_again(db: Session) -> None:
    reading, line = start_reading(db, "blue")
    read(db, reading, line)
    long_ago = datetime.now(UTC) - timedelta(days=30)
    row = db.scalars(
        select(PhonicsMastery).where(PhonicsMastery.child_id == reading.child_id)
    ).one()
    row.last_practised_at = long_ago
    db.flush()

    read(db, reading, line)  # same line, same session: the latest read replaces the first

    assert stamps_by_code(db, reading.child_id)["blend_bl"] > long_ago
    assert (row.correct_count, row.attempts_count) == (1, 1)


def test_the_engine_reinforces_the_mastered_patterns_practised_longest_ago(db: Session) -> None:
    reading, _ = start_reading(db, "ship")
    child_id = reading.child_id
    # All three are mastered. By confidence alone the two weakest are SH and CH.
    add_mastery(db, child_id, "digraph_sh", 9, 10)  # 0.833
    add_mastery(db, child_id, "digraph_ch", 10, 10)  # 0.917
    add_mastery(db, child_id, "digraph_th", 20, 20)  # 0.955
    assert reinforce_codes(db, child_id) == ["digraph_sh", "digraph_ch"]  # no timestamps yet

    now = datetime.now(UTC)
    for code, days_ago in [("digraph_sh", 1), ("digraph_ch", 2), ("digraph_th", 30)]:
        row = db.scalars(
            select(PhonicsMastery)
            .join(PhonicsPattern)
            .where(PhonicsMastery.child_id == child_id, PhonicsPattern.code == code)
        ).one()
        row.last_practised_at = now - timedelta(days=days_ago)
    db.flush()

    assert reinforce_codes(db, child_id) == ["digraph_ch", "digraph_th"]  # SH was read yesterday


def test_reading_a_reinforced_pattern_moves_it_to_the_back_of_the_queue(db: Session) -> None:
    # The seam: scoring stamps the pattern, and the very next target reinforces the others.
    reading, line = start_reading(db, "ship wish")  # two SH words
    child_id = reading.child_id
    add_mastery(db, child_id, "digraph_sh", 9, 10)
    add_mastery(db, child_id, "digraph_ch", 10, 10)
    add_mastery(db, child_id, "digraph_th", 20, 20)
    assert reinforce_codes(db, child_id) == ["digraph_sh", "digraph_ch"]

    read(db, reading, line)  # SH is now 11 of 12 and stamped; CH and TH were never stamped

    assert reinforce_codes(db, child_id) == ["digraph_ch", "digraph_th"]
