"""process_line_score against a real (throwaway) schema with the app's session settings.

The mock-session tests in test_scoring.py cannot see flush behavior. The app's sessions have
autoflush off (app.db.session.SessionLocal), so these tests do too. Skips, loudly, when no
local Postgres is running.
"""

from collections.abc import Generator

import pytest
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.session import engine
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
from app.services.scoring import process_line_score
from scripts.seed_vocabulary import LOCAL_HOSTS, seed

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
    """A throwaway schema holding the real seed, rolled back afterwards."""
    if make_url(str(engine.url)).host not in LOCAL_HOSTS:
        pytest.skip("scoring DB tests only run against a local database")
    try:
        connection = engine.connect()
    except OperationalError:
        pytest.skip(
            "local Postgres is not running (docker compose up -d db): "
            "process_line_score persistence was NOT tested"
        )
    transaction = connection.begin()
    try:
        connection.execute(text("CREATE SCHEMA scoring_test"))
        connection.execute(text("SET LOCAL search_path TO scoring_test"))
        for table in TABLES:
            table.create(connection, checkfirst=False)
        with Session(bind=connection, autoflush=False, expire_on_commit=False) as session:
            seed(session)
            yield session
    finally:
        transaction.rollback()
        connection.close()


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


def mastery_by_code(db: Session, reading: ReadingSession) -> dict[str, tuple[int, int]]:
    rows = db.execute(
        select(PhonicsPattern.code, PhonicsMastery.correct_count, PhonicsMastery.attempts_count)
        .join(PhonicsPattern)
        .where(PhonicsMastery.child_id == reading.child_id)
    )
    return {code: (correct, attempts) for code, correct, attempts in rows}


def test_two_words_sharing_a_new_pattern_update_one_mastery_row(db: Session) -> None:
    # "blue" and "black" are both blend_bl, and the child has no blend_bl row yet.
    line_text = "The blue lamp and black clock had fun."
    reading, line = start_reading(db, line_text)
    statuses = {"blue": "mastered", "black": "missed"}
    score = ScoreResult(
        words=[
            WordScore(expected_word=word, status=statuses.get(word, "mastered"))
            for word in line_text.split()
        ]
    )

    process_line_score(db, reading.id, line.id, score)

    mastery = mastery_by_code(db, reading)
    assert mastery["blend_bl"] == (1, 2)  # one row, both words counted
    assert mastery["blend_cl"] == (1, 1)
    assert mastery["final_blend_mp"] == (1, 1)


def test_a_second_line_adds_to_the_existing_mastery_row(db: Session) -> None:
    reading, line = start_reading(db, "The blue lamp and black clock had fun.")
    all_mastered = ScoreResult(
        words=[WordScore(expected_word=w, status="mastered") for w in line.text.split()]
    )

    process_line_score(db, reading.id, line.id, all_mastered)
    process_line_score(db, reading.id, line.id, all_mastered)

    assert mastery_by_code(db, reading)["blend_bl"] == (4, 4)
