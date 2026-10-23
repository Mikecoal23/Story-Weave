"""POST /stories/generate and the GET /stories/{id} round trip.

The first group needs no database. The second group runs the real route against a throwaway
schema (local Postgres only) and skips, loudly, when none is running.
"""

from collections.abc import Generator
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.routes import stories as stories_route
from app.db.session import engine, get_db
from app.main import app
from app.models import (
    Caregiver,
    Child,
    PhonicsMastery,
    PhonicsPattern,
    Story,
    StoryLine,
    StoryPattern,
    VocabularyWord,
    VocabularyWordPattern,
)
from app.schemas.stories import ValidatedStory
from app.services import story_pipeline
from app.services.story_pipeline import NoValidStoryError
from app.services.story_templates import FALLBACK_TEMPLATES
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
]


def _post_generate(db, child_id: UUID):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        return TestClient(app).post("/stories/generate", json={"child_id": str(child_id)})
    finally:
        app.dependency_overrides.pop(get_db, None)


def _get_story(db, story_id: UUID):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        return TestClient(app).get(f"/stories/{story_id}")
    finally:
        app.dependency_overrides.pop(get_db, None)


# --- no database -----------------------------------------------------------------------


def test_generate_returns_404_for_an_unknown_child() -> None:
    db = Mock()
    db.get.return_value = None

    response = _post_generate(db, uuid4())

    assert response.status_code == 404
    db.commit.assert_not_called()


def test_generate_rejects_a_body_without_child_id() -> None:
    response = TestClient(app).post("/stories/generate", json={})

    assert response.status_code == 422


def test_generate_returns_503_when_no_valid_story_exists(monkeypatch) -> None:
    db = Mock()
    db.get.return_value = Child(
        id=uuid4(), caregiver_id=uuid4(), display_name="A", grade_level=1, interests=[]
    )
    db.scalars.return_value.all.return_value = []
    monkeypatch.setattr(stories_route, "load_allowed_vocabulary", Mock(return_value=frozenset()))
    monkeypatch.setattr(
        stories_route, "generate_validated_story", Mock(side_effect=NoValidStoryError("none"))
    )
    monkeypatch.setattr(
        stories_route,
        "select_difficulty_target",
        Mock(return_value=Mock(reinforce_pattern_ids=(), stretch_pattern_ids=())),
    )

    response = _post_generate(db, db.get.return_value.id)

    assert response.status_code == 503
    db.commit.assert_not_called()


# --- real schema -----------------------------------------------------------------------


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """A throwaway schema holding the real seed, rolled back afterwards."""
    if make_url(str(engine.url)).host not in LOCAL_HOSTS:
        pytest.skip("story route DB tests only run against a local database")
    try:
        connection = engine.connect()
    except OperationalError:
        pytest.skip(
            "local Postgres is not running (docker compose up -d db): "
            "POST /stories/generate persistence was NOT tested"
        )
    transaction = connection.begin()
    try:
        connection.execute(text("CREATE SCHEMA generate_story_test"))
        connection.execute(text("SET LOCAL search_path TO generate_story_test"))
        for table in TABLES:
            table.create(connection, checkfirst=False)
        with Session(bind=connection) as session:
            seed(session)
            yield session
    finally:
        transaction.rollback()
        connection.close()


def make_child(db: Session, interests: list[str] | None = None) -> Child:
    caregiver = Caregiver(display_name="Test Caregiver")
    db.add(caregiver)
    db.flush()
    child = Child(
        caregiver_id=caregiver.id,
        display_name="Test Child",
        grade_level=1,
        interests=interests or [],
    )
    db.add(child)
    db.flush()
    return child


def first_two_pattern_ids(db: Session) -> list[int]:
    return list(
        db.scalars(
            select(PhonicsPattern.phonics_pattern_id)
            .order_by(PhonicsPattern.sequence_order)
            .limit(2)
        )
    )


def test_generate_saves_an_llm_story_and_get_returns_it(db: Session, monkeypatch) -> None:
    child = make_child(db, interests=["dogs"])
    stretch_ids = first_two_pattern_ids(db)
    codes = tuple(
        db.scalars(
            select(PhonicsPattern.code).where(PhonicsPattern.phonics_pattern_id.in_(stretch_ids))
        )
    )
    draft = ValidatedStory(
        title="The Big Dog",
        theme="dogs",
        pattern_codes=codes,
        lines=("The big dog ran.", "It is fun."),
        source="llm",
        attempts=2,
    )
    generator = Mock(return_value=draft)
    monkeypatch.setattr(stories_route, "generate_validated_story", generator)

    response = _post_generate(db, child.id)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "The Big Dog"
    assert body["theme"] == "dogs"
    assert body["lines"] == ["The big dog ran.", "It is fun."]
    assert body["source"] == "llm"
    assert body["attempts"] == 2

    # The generator got the child's two stretch patterns (in order), the interests and the
    # vocabulary that was loaded once for this request.
    patterns, interests, allowed = generator.call_args.args
    assert [p.phonics_pattern_id for p in patterns] == stretch_ids
    assert interests == ("dogs",)
    assert "dog" in allowed

    story = db.get(Story, UUID(body["id"]))
    assert story is not None
    assert story.status == "validated"
    assert story.child_id == child.id
    linked = set(
        db.scalars(select(StoryPattern.phonics_pattern_id).where(StoryPattern.story_id == story.id))
    )
    assert linked == set(stretch_ids)

    round_trip = _get_story(db, story.id)
    assert round_trip.status_code == 200
    assert round_trip.json() == {
        "id": body["id"],
        "title": "The Big Dog",
        "theme": "dogs",
        "lines": ["The big dog ran.", "It is fun."],
    }


def test_generate_falls_back_to_a_template_when_the_llm_fails(db: Session, monkeypatch) -> None:
    # The same path a missing API key takes: every LLM call errors, so after all attempts the
    # pipeline serves a validated fallback template. Runs the real validator on the real seed.
    child = make_child(db)
    monkeypatch.setattr(
        story_pipeline, "generate_story_draft", Mock(side_effect=ValueError("bad reply"))
    )

    response = _post_generate(db, child.id)

    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "fallback"
    assert body["attempts"] == 3
    assert body["title"] in {template.title for template in FALLBACK_TEMPLATES}
    saved_lines = list(
        db.scalars(
            select(StoryLine.text)
            .where(StoryLine.story_id == UUID(body["id"]))
            .order_by(StoryLine.line_number)
        )
    )
    assert saved_lines == body["lines"]
    assert db.get(Story, UUID(body["id"])).status == "validated"  # type: ignore[union-attr]
