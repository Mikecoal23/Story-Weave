"""scripts.dev_fixtures: fixed ids, idempotence, safety rails (real schema, local Postgres only)."""

from collections.abc import Generator

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import engine
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
from app.services.story_templates import FALLBACK_TEMPLATES
from scripts import dev_fixtures
from scripts.dev_fixtures import (
    CAREGIVER_ID,
    LEO_ID,
    MIA_ID,
    STORY_ID,
    main,
    seed_fixtures,
)
from scripts.seed_vocabulary import LOCAL_HOSTS, seed

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


def _throwaway_schema(*, seeded: bool) -> Generator[Session, None, None]:
    if make_url(str(engine.url)).host not in LOCAL_HOSTS:
        pytest.skip("dev fixtures DB tests only run against a local database")
    try:
        connection = engine.connect()
    except OperationalError:
        pytest.skip(
            "local Postgres is not running (docker compose up -d db): "
            "scripts.dev_fixtures was NOT tested"
        )
    transaction = connection.begin()
    try:
        connection.execute(text("CREATE SCHEMA dev_fixtures_test"))
        connection.execute(text("SET LOCAL search_path TO dev_fixtures_test"))
        for table in TABLES:
            table.create(connection, checkfirst=False)
        with Session(bind=connection) as session:
            if seeded:
                seed(session)
            yield session
    finally:
        transaction.rollback()
        connection.close()


@pytest.fixture
def db() -> Generator[Session, None, None]:
    yield from _throwaway_schema(seeded=True)


@pytest.fixture
def empty_db() -> Generator[Session, None, None]:
    yield from _throwaway_schema(seeded=False)


def count(db: Session, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def test_creates_one_caregiver_two_children_and_the_first_template_story(db: Session) -> None:
    ids = seed_fixtures(db)

    assert ids == {
        "caregiver_id": str(CAREGIVER_ID),
        "mia_child_id": str(MIA_ID),
        "leo_child_id": str(LEO_ID),
        "story_id": str(STORY_ID),
    }
    assert count(db, Caregiver) == 1
    assert {child.display_name for child in db.scalars(select(Child))} == {"Mia", "Leo"}
    story = db.get(Story, STORY_ID)
    assert story is not None
    assert story.child_id == MIA_ID
    assert story.status == "validated"
    assert story.title == FALLBACK_TEMPLATES[0].title
    lines = list(
        db.scalars(
            select(StoryLine.text)
            .where(StoryLine.story_id == STORY_ID)
            .order_by(StoryLine.line_number)
        )
    )
    assert lines == list(FALLBACK_TEMPLATES[0].lines)
    linked = set(
        db.scalars(
            select(PhonicsPattern.code)
            .join(
                StoryPattern, StoryPattern.phonics_pattern_id == PhonicsPattern.phonics_pattern_id
            )
            .where(StoryPattern.story_id == STORY_ID)
        )
    )
    assert linked == set(FALLBACK_TEMPLATES[0].pattern_codes)


def test_running_twice_creates_nothing_new(db: Session) -> None:
    seed_fixtures(db)
    before = [count(db, model) for model in (Caregiver, Child, Story, StoryLine, StoryPattern)]

    seed_fixtures(db)

    assert [
        count(db, model) for model in (Caregiver, Child, Story, StoryLine, StoryPattern)
    ] == before


def test_existing_rows_are_never_modified(db: Session) -> None:
    seed_fixtures(db)
    mia = db.get(Child, MIA_ID)
    mia.display_name = "Renamed"  # type: ignore[union-attr]
    db.flush()

    seed_fixtures(db)

    assert db.get(Child, MIA_ID).display_name == "Renamed"  # type: ignore[union-attr]


def test_refuses_to_run_before_the_vocabulary_is_seeded(empty_db: Session) -> None:
    with pytest.raises(RuntimeError, match="seed_vocabulary"):
        seed_fixtures(empty_db)


def test_main_refuses_a_remote_database_without_allow_remote(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        settings, "database_url", "postgresql+psycopg://user:pw@ep-example.neon.tech/neondb"
    )
    monkeypatch.setattr(
        dev_fixtures, "seed_fixtures", lambda session: pytest.fail("must not touch the database")
    )

    assert main([]) == 2
    assert "Refusing" in capsys.readouterr().out
