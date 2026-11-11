"""GET /children/{child_id}/dashboard: the 404 always runs; the rest need local Postgres."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from support import throwaway_schema

from app.db.session import get_db
from app.main import app
from app.models import (
    Caregiver,
    Child,
    PhonicsMastery,
    PhonicsPattern,
    ReadingAttempt,
    ReadingSession,
    Story,
    StoryLine,
    VocabularyWord,
    VocabularyWordPattern,
)

# The seed also writes vocabulary rows, so those tables are created too.
TABLES = [
    Caregiver.__table__,
    Child.__table__,
    PhonicsPattern.__table__,
    PhonicsMastery.__table__,
    VocabularyWord.__table__,
    VocabularyWordPattern.__table__,
    Story.__table__,
    StoryLine.__table__,
    ReadingSession.__table__,
    ReadingAttempt.__table__,
]


def _get_dashboard(db, child_id: UUID):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        return TestClient(app).get(f"/children/{child_id}/dashboard")
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_dashboard_returns_404_for_unknown_child() -> None:
    db = Mock()
    db.get.return_value = None

    response = _get_dashboard(db, uuid4())

    assert response.status_code == 404


# --- real schema -----------------------------------------------------------------------


@pytest.fixture
def db() -> Generator[Session, None, None]:
    with throwaway_schema("dashboard_test", TABLES, not_tested="the dashboard queries") as session:
        yield session


def make_child(db: Session) -> Child:
    caregiver = Caregiver(display_name="Test Caregiver")
    db.add(caregiver)
    db.flush()
    child = Child(caregiver_id=caregiver.id, display_name="Test Child", grade_level=1)
    db.add(child)
    db.flush()
    return child


def patterns(db: Session) -> list[PhonicsPattern]:
    return list(db.scalars(select(PhonicsPattern).order_by(PhonicsPattern.sequence_order)))


def make_session(
    db: Session, child: Child, title: str, started_at: datetime
) -> tuple[ReadingSession, StoryLine]:
    story = Story(child_id=child.id, title=title, status="validated")
    db.add(story)
    db.flush()
    line = StoryLine(story_id=story.id, line_number=1, text="A ship.")
    reading = ReadingSession(child_id=child.id, story_id=story.id, started_at=started_at)
    db.add_all([line, reading])
    db.flush()
    return reading, line


def add_attempt(
    db: Session,
    reading: ReadingSession,
    line: StoryLine,
    word: str,
    status: str,
    created_at: datetime,
    index: int = 1,
) -> None:
    db.add(
        ReadingAttempt(
            reading_session_id=reading.id,
            story_line_id=line.id,
            word_index=index,
            expected_word=word,
            result_status=status,
            created_at=created_at,
        )
    )
    db.flush()


def test_child_with_no_data_gets_empty_dashboard(db: Session) -> None:
    child = make_child(db)
    first_two = patterns(db)[:2]

    response = _get_dashboard(db, child.id)

    assert response.status_code == 200
    body = response.json()
    assert body["sessions"] == 0
    assert body["last_story"] is None
    assert body["strongest"] is None
    assert body["patterns"] == []
    # A new child is working on the first two patterns, and practises their example words.
    assert body["working_on"] == [p.label for p in first_two]
    assert 0 < len(body["try_at_home"]) <= 5
    assert set(body["try_at_home"]) <= {w for p in first_two for w in p.example_words}


def test_child_with_sessions_and_mastery(db: Session) -> None:
    child = make_child(db)
    now = datetime.now(UTC)
    p1, p2, p3 = patterns(db)[:3]

    # Counts: this week, has scored words.
    recent, line = make_session(db, child, "New Story", now - timedelta(hours=1))
    add_attempt(db, recent, line, "the", "mastered", now - timedelta(minutes=30), 1)
    add_attempt(db, recent, line, "ship.", "shaky", now - timedelta(minutes=20), 2)
    add_attempt(db, recent, line, "Chop,", "missed", now - timedelta(minutes=10), 3)
    add_attempt(db, recent, line, "ship", "missed", now - timedelta(minutes=5), 4)
    # Doesn't count: this week but nothing was scored.
    make_session(db, child, "Unread Story", now - timedelta(hours=3))
    # Doesn't count: scored, but older than 7 days.
    old, old_line = make_session(db, child, "Old Story", now - timedelta(days=10))
    add_attempt(db, old, old_line, "old", "missed", now - timedelta(days=10))

    db.add_all(
        [
            PhonicsMastery(
                child_id=child.id,
                phonics_pattern_id=p1.phonics_pattern_id,
                mastery_score=0.9,
                attempts_count=10,
                correct_count=9,
            ),
            PhonicsMastery(
                child_id=child.id,
                phonics_pattern_id=p2.phonics_pattern_id,
                mastery_score=0.5,
                attempts_count=4,
                correct_count=2,
            ),
        ]
    )
    db.flush()

    response = _get_dashboard(db, child.id)

    assert response.status_code == 200
    assert response.json() == {
        "sessions": 1,
        "last_story": "New Story",
        "working_on": [p2.label, p3.label],  # p1 is mastered, so the next two unmastered
        "strongest": p1.label,
        "patterns": [{"label": p1.label, "fill": 90}, {"label": p2.label, "fill": 50}],
        # Newest first, punctuation stripped, no repeats; "the" was mastered so it is left out.
        "try_at_home": ["ship", "chop", "old"],
    }
