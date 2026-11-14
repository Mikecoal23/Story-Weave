"""`story.source`: save_validated_story stores whether the LLM or a fallback wrote the story.

Real (throwaway) schema, local Postgres only; skips, loudly, when none is running.
"""

from collections.abc import Generator

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from support import throwaway_schema

from app.models import (
    Caregiver,
    Child,
    PhonicsPattern,
    Story,
    StoryLine,
    StoryPattern,
    VocabularyWord,
    VocabularyWordPattern,
)
from app.schemas.stories import ValidatedStory
from app.services.story_store import save_validated_story

TABLES = [
    Caregiver.__table__,
    Child.__table__,
    PhonicsPattern.__table__,
    VocabularyWord.__table__,
    VocabularyWordPattern.__table__,
    Story.__table__,
    StoryPattern.__table__,
    StoryLine.__table__,
]


@pytest.fixture
def db() -> Generator[Session, None, None]:
    with throwaway_schema("story_source_test", TABLES, not_tested="story.source") as session:
        yield session


def make_child(db: Session) -> Child:
    caregiver = Caregiver(display_name="Test Caregiver")
    db.add(caregiver)
    db.flush()
    child = Child(caregiver_id=caregiver.id, display_name="Test Child", grade_level=1)
    db.add(child)
    db.flush()
    return child


def a_story(source: str) -> ValidatedStory:
    return ValidatedStory(
        title="T",
        theme="t",
        pattern_codes=(),
        lines=("It is fun.",),
        source=source,  # type: ignore[arg-type]
        attempts=1,
    )


def stored_source(db: Session, story_id) -> str | None:
    return db.scalar(select(Story.source).where(Story.id == story_id))


def test_a_saved_llm_story_remembers_it_came_from_the_llm(db: Session) -> None:
    child = make_child(db)

    story = save_validated_story(db, child.id, a_story("llm"))

    assert stored_source(db, story.id) == "llm"


def test_a_saved_fallback_story_remembers_it_was_a_fallback(db: Session) -> None:
    child = make_child(db)

    story = save_validated_story(db, child.id, a_story("fallback"))

    assert stored_source(db, story.id) == "fallback"


def test_a_story_saved_without_a_source_reads_back_as_none(db: Session) -> None:
    # What a row saved before the column existed looks like: no source, and no error.
    child = make_child(db)
    old = Story(child_id=child.id, title="Old", theme=None, status="validated")
    db.add(old)
    db.flush()

    assert stored_source(db, old.id) is None


def test_the_database_rejects_an_unknown_source(db: Session) -> None:
    child = make_child(db)

    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(Story(child_id=child.id, title="T", status="validated", source="human"))
        db.flush()
