"""Validator checks that need a real `vocabulary_word` table (local Postgres only).

These skip, loudly, when no local Postgres is running, so a skip here means the
fallback templates were NOT re-validated against the seeded vocabulary. The pure
validator tests in test_vocabulary_validator.py always run.
"""

from collections.abc import Generator

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models import PhonicsPattern, VocabularyWord, VocabularyWordPattern
from app.schemas.stories import DraftStory
from app.services.story_templates import FALLBACK_TEMPLATES
from app.services.vocabulary_validator import load_allowed_vocabulary, validate_story
from scripts.seed_data import build_words
from scripts.seed_vocabulary import LOCAL_HOSTS, seed

TABLES = [PhonicsPattern.__table__, VocabularyWord.__table__, VocabularyWordPattern.__table__]


@pytest.fixture
def seeded_session() -> Generator[Session, None, None]:
    """A throwaway schema, seeded with the real seed data, rolled back afterwards."""
    if make_url(str(engine.url)).host not in LOCAL_HOSTS:
        pytest.skip("vocabulary DB tests only run against a local database")
    try:
        connection = engine.connect()
    except OperationalError:
        pytest.skip(
            "local Postgres is not running (docker compose up -d db): "
            "fallback templates were NOT validated against the seeded vocabulary"
        )
    transaction = connection.begin()
    try:
        connection.execute(text("CREATE SCHEMA validator_test"))
        connection.execute(text("SET LOCAL search_path TO validator_test"))
        for table in TABLES:
            table.create(connection, checkfirst=False)
        with Session(bind=connection) as db:
            seed(db)
            yield db
    finally:
        transaction.rollback()
        connection.close()


def test_allowed_vocabulary_is_every_seeded_word(seeded_session: Session) -> None:
    allowed = load_allowed_vocabulary(seeded_session)
    assert allowed == {w.word for w in build_words()}


def test_every_fallback_template_passes_against_the_seeded_vocabulary(
    seeded_session: Session,
) -> None:
    allowed = load_allowed_vocabulary(seeded_session)
    for template in FALLBACK_TEMPLATES:
        result = validate_story(template, allowed)
        assert result.is_valid, f"{template.title}: {result.unknown_words}"


def test_an_out_of_vocabulary_word_is_rejected_against_the_seeded_vocabulary(
    seeded_session: Session,
) -> None:
    allowed = load_allowed_vocabulary(seeded_session)
    draft = DraftStory(
        title="Ship Wish",
        theme="t",
        pattern_codes=(),
        lines=("A frog sat by a ship.", "A dragon came."),
    )
    assert validate_story(draft, allowed).unknown_words == ("dragon",)
