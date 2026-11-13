"""Reading the same line again in the same reading session: the latest read replaces the first.

The mic stays on after a line is scored, so a child can record a line several times. Without
this rule every upload adds to `phonics_mastery`. Real (throwaway) schema, local Postgres only;
skips, loudly, when none is running.
"""

from collections.abc import Generator

import pytest
from sqlalchemy import func, select
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
from app.services.dashboard import build_dashboard
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

# blend_bl twice (blue, black), blend_cl once (clock), final_blend_mp once (lamp); "The",
# "and" and "had" are sight words and "fun" has no pattern.
LINE = "The blue lamp and black clock had fun."


@pytest.fixture
def db() -> Generator[Session, None, None]:
    with throwaway_schema(
        "rescoring_test", TABLES, not_tested="re-reading a line in one session"
    ) as session:
        yield session


def start_reading(db: Session, *line_texts: str) -> tuple[ReadingSession, list[StoryLine]]:
    caregiver = Caregiver(display_name="Test Caregiver")
    db.add(caregiver)
    db.flush()
    child = Child(caregiver_id=caregiver.id, display_name="Test Child", grade_level=1)
    db.add(child)
    db.flush()
    story = Story(child_id=child.id, title="Test", status="validated")
    db.add(story)
    db.flush()
    lines = [
        StoryLine(story_id=story.id, line_number=number, text=text)
        for number, text in enumerate(line_texts, start=1)
    ]
    reading = ReadingSession(child_id=child.id, story_id=story.id)
    db.add_all([*lines, reading])
    db.flush()
    return reading, lines


def score(words: str, status: str) -> ScoreResult:
    return ScoreResult(words=[WordScore(expected_word=w, status=status) for w in words.split()])


def mastery_by_code(db: Session, reading: ReadingSession) -> dict[str, tuple[int, int, float]]:
    rows = db.execute(
        select(
            PhonicsPattern.code,
            PhonicsMastery.correct_count,
            PhonicsMastery.attempts_count,
            PhonicsMastery.mastery_score,
        )
        .join(PhonicsPattern)
        .where(PhonicsMastery.child_id == reading.child_id)
    )
    return {code: (correct, attempts, float(ratio)) for code, correct, attempts, ratio in rows}


def attempt_count(db: Session, reading: ReadingSession) -> int:
    return db.scalar(
        select(func.count())
        .select_from(ReadingAttempt)
        .where(ReadingAttempt.reading_session_id == reading.id)
    )


def test_reading_a_line_again_in_the_same_session_replaces_the_first_read(db: Session) -> None:
    reading, (line,) = start_reading(db, LINE)

    for _ in range(5):  # one line recorded five times
        process_line_score(db, reading.id, line.id, score(LINE, "mastered"))

    assert mastery_by_code(db, reading)["blend_bl"] == (2, 2, 1.0)  # one read, not five
    assert mastery_by_code(db, reading)["blend_cl"] == (1, 1, 1.0)
    assert attempt_count(db, reading) == len(LINE.split())  # one read's attempts, not five


def test_a_worse_second_read_replaces_a_better_first_read(db: Session) -> None:
    reading, (line,) = start_reading(db, LINE)

    process_line_score(db, reading.id, line.id, score(LINE, "mastered"))
    process_line_score(db, reading.id, line.id, score(LINE, "missed"))

    assert mastery_by_code(db, reading)["blend_bl"] == (0, 2, 0.0)


def test_a_good_second_read_replaces_a_failed_first_take(db: Session) -> None:
    # A silent first take is scored as all "missed" (Azure NoMatch); the retry is the real read.
    reading, (line,) = start_reading(db, LINE)

    process_line_score(db, reading.id, line.id, score(LINE, "missed"))
    process_line_score(db, reading.id, line.id, score(LINE, "mastered"))

    assert mastery_by_code(db, reading)["blend_bl"] == (2, 2, 1.0)


def test_taking_back_a_mastered_read_takes_back_its_correct_counts(db: Session) -> None:
    # Line 1 keeps the pattern's attempts above 0, so the correct count has to be taken back
    # for real.
    reading, (first, second) = start_reading(db, "The blue lamp.", "The blue lamp.")

    process_line_score(db, reading.id, first.id, score("The blue lamp.", "missed"))
    process_line_score(db, reading.id, second.id, score("The blue lamp.", "mastered"))
    assert mastery_by_code(db, reading)["blend_bl"] == (1, 2, 0.5)

    process_line_score(db, reading.id, second.id, score("The blue lamp.", "missed"))

    assert mastery_by_code(db, reading)["blend_bl"] == (0, 2, 0.0)


def test_a_different_line_in_the_same_session_is_not_replaced(db: Session) -> None:
    reading, (first, second) = start_reading(db, LINE, "The blue lamp.")

    process_line_score(db, reading.id, first.id, score(LINE, "mastered"))
    process_line_score(db, reading.id, second.id, score("The blue lamp.", "mastered"))

    assert mastery_by_code(db, reading)["blend_bl"] == (3, 3, 1.0)


def test_a_row_that_falls_back_to_zero_attempts_keeps_the_table_constraints(db: Session) -> None:
    # The second read has no SH word at all, so SH goes 1 -> 0 attempts: score 0, no
    # division by zero, and correct <= attempts still holds.
    reading, (line,) = start_reading(db, "ship")

    process_line_score(db, reading.id, line.id, score("ship", "mastered"))
    process_line_score(db, reading.id, line.id, score("the", "mastered"))  # a sight word

    assert mastery_by_code(db, reading)["digraph_sh"] == (0, 0, 0.0)
    assert attempt_count(db, reading) == 1  # only the sight-word attempt remains


def test_a_pattern_link_added_after_the_first_read_cannot_push_counts_below_zero(
    db: Session,
) -> None:
    # "ship" was read when it had only SH. Then it gets a CH link too (a re-seed). Taking
    # the first read back must not decrement a CH row that never counted it.
    reading, (line,) = start_reading(db, "ship")
    process_line_score(db, reading.id, line.id, score("ship", "missed"))
    ship_id = db.scalar(
        select(VocabularyWord.vocabulary_word_id).where(VocabularyWord.word == "ship")
    )
    ch_id = db.scalar(
        select(PhonicsPattern.phonics_pattern_id).where(PhonicsPattern.code == "digraph_ch")
    )
    db.add(VocabularyWordPattern(vocabulary_word_id=ship_id, phonics_pattern_id=ch_id))
    db.add(
        PhonicsMastery(
            child_id=reading.child_id,
            phonics_pattern_id=ch_id,
            mastery_score=0,
            attempts_count=0,
            correct_count=0,
        )
    )
    db.flush()

    process_line_score(db, reading.id, line.id, score("ship", "mastered"))  # no CheckViolation

    counts = mastery_by_code(db, reading)
    assert counts["digraph_sh"] == (1, 1, 1.0)
    assert counts["digraph_ch"] == (1, 1, 1.0)  # clamped at 0, then the new read counted


def test_a_word_missed_and_then_read_right_is_no_longer_a_practice_word(db: Session) -> None:
    reading, (line,) = start_reading(db, "clock")

    process_line_score(db, reading.id, line.id, score("clock", "missed"))
    assert "clock" in build_dashboard(db, reading.child_id).try_at_home

    process_line_score(db, reading.id, line.id, score("clock", "mastered"))
    assert "clock" not in build_dashboard(db, reading.child_id).try_at_home
