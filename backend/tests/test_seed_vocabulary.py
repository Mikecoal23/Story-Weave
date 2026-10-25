from collections.abc import Generator

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from support import throwaway_schema

from app.models import PhonicsPattern, VocabularyWord, VocabularyWordPattern
from scripts import seed_data, seed_vocabulary
from scripts.seed_data import PATTERNS, build_words
from scripts.seed_vocabulary import seed

TABLES = [PhonicsPattern.__table__, VocabularyWord.__table__, VocabularyWordPattern.__table__]


@pytest.fixture
def session() -> Generator[Session, None, None]:
    """Empty seed tables in a throwaway schema, so each test runs the seed itself."""
    with throwaway_schema(
        "seed_test", TABLES, not_tested="scripts.seed_vocabulary", seeded=False
    ) as db:
        yield db


def count(session: Session, model) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def tags(session: Session) -> dict[str, set[str]]:
    rows = session.execute(
        select(VocabularyWord.word, PhonicsPattern.code)
        .join(
            VocabularyWordPattern,
            VocabularyWordPattern.vocabulary_word_id == VocabularyWord.vocabulary_word_id,
        )
        .join(
            PhonicsPattern,
            PhonicsPattern.phonics_pattern_id == VocabularyWordPattern.phonics_pattern_id,
        )
    ).all()
    result: dict[str, set[str]] = {}
    for word, code in rows:
        result.setdefault(word, set()).add(code)
    return result


def test_seed_inserts_everything(session: Session) -> None:
    report = seed(session)
    words = build_words()
    assert count(session, PhonicsPattern) == len(PATTERNS) == report.patterns
    assert count(session, VocabularyWord) == len(words) == report.words
    expected_junction = sum(len(w.pattern_codes) for w in words)
    assert count(session, VocabularyWordPattern) == expected_junction == report.junction_rows
    assert report.junction_added == expected_junction
    assert report.junction_removed == 0
    assert report.unmanaged_words == 0


def test_seed_twice_changes_nothing(session: Session) -> None:
    first = seed(session)
    second = seed(session)
    assert (second.patterns, second.words, second.junction_rows) == (
        first.patterns,
        first.words,
        first.junction_rows,
    )
    assert second.junction_added == 0
    assert second.junction_removed == 0


def test_no_sight_word_has_pattern_rows(session: Session) -> None:
    seed(session)
    sight_with_rows = session.scalar(
        select(func.count())
        .select_from(VocabularyWordPattern)
        .join(
            VocabularyWord,
            VocabularyWord.vocabulary_word_id == VocabularyWordPattern.vocabulary_word_id,
        )
        .where(VocabularyWord.is_sight_word.is_(True))
    )
    assert sight_with_rows == 0


def test_multi_pattern_words_have_every_junction_row(session: Session) -> None:
    seed(session)
    found = tags(session)
    assert found["shake"] == {"digraph_sh", "silent_e_a"}
    assert found["fresh"] == {"digraph_sh", "blend_fr"}
    assert found["champ"] == {"digraph_ch", "final_blend_mp"}
    assert found["clay"] == {"blend_cl", "vowel_team_ai_ay"}
    assert found["chase"] == {"digraph_ch", "silent_e_a"}


def test_pattern_metadata_is_stored(session: Session) -> None:
    seed(session)
    rows = {p.code: p for p in session.scalars(select(PhonicsPattern))}
    assert rows["digraph_sh"].sequence_order == 10
    assert rows["final_blend_mp"].sequence_order == 90
    assert rows["silent_e_a"].example_words == ["cake", "name"]


def test_pattern_word_demoted_to_sight_loses_its_junction_rows(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed(session)
    assert "ship" in tags(session)

    monkeypatch.setattr(
        seed_data,
        "PATTERN_WORDS",
        {c: tuple(w for w in ws if w != "ship") for c, ws in seed_data.PATTERN_WORDS.items()},
    )
    monkeypatch.setattr(seed_data, "FILLER_WORDS", (*seed_data.FILLER_WORDS, "ship"))
    # Same word, now a plain non-pattern word: junction row must go.
    report = seed(session)
    assert "ship" not in tags(session)
    assert report.junction_removed == 1

    monkeypatch.setattr(seed_data, "FILLER_WORDS", seed_data.FILLER_WORDS[:-1])
    monkeypatch.setattr(seed_data, "DOLCH_WORDS", (*seed_data.DOLCH_WORDS, "ship"))
    seed(session)
    ship = session.scalar(select(VocabularyWord).where(VocabularyWord.word == "ship"))
    assert ship is not None and ship.is_sight_word
    assert "ship" not in tags(session)


def test_sight_word_promoted_to_pattern_gets_flag_cleared_and_rows_added(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed(session)
    wash = session.scalar(select(VocabularyWord).where(VocabularyWord.word == "wash"))
    assert wash is not None and not wash.is_sight_word  # promoted pattern word

    # Demote wash to a sight word, seed, then promote it back.
    monkeypatch.setattr(
        seed_data,
        "PATTERN_WORDS",
        {c: tuple(w for w in ws if w != "wash") for c, ws in seed_data.PATTERN_WORDS.items()},
    )
    seed(session)
    session.refresh(wash)
    assert wash.is_sight_word and "wash" not in tags(session)

    monkeypatch.undo()
    seed(session)
    session.refresh(wash)
    assert not wash.is_sight_word
    assert tags(session)["wash"] == {"digraph_sh"}


def test_words_outside_the_seed_are_left_alone(session: Session) -> None:
    session.add(VocabularyWord(word="zebra", is_sight_word=False))
    session.flush()
    report = seed(session)
    assert report.unmanaged_words == 1
    assert session.scalar(select(VocabularyWord).where(VocabularyWord.word == "zebra"))


def test_bad_data_aborts_before_any_write(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(seed_data, "FILLER_WORDS", ("sat", "the"))
    with pytest.raises(ValueError):
        seed(session)
    assert count(session, PhonicsPattern) == 0
    assert count(session, VocabularyWord) == 0


def test_cli_refuses_remote_hosts_without_the_flag(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from app.core.config import settings

    monkeypatch.setattr(
        settings, "database_url", "postgresql+psycopg://u:secret@ep-example.neon.tech/db"
    )
    assert seed_vocabulary.main([]) == 2
    out = capsys.readouterr().out
    assert "Refusing" in out and "secret" not in out
