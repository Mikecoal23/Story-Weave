"""The seams between components: scoring -> difficulty engine, and generation -> scoring.

Each unit is tested on its own elsewhere; these check that the output of one is something the
next one handles. No Azure or Anthropic call is made. The database tests run on a throwaway
schema (local Postgres only) and skip, loudly, when none is running.
"""

from collections.abc import Generator
from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from support import throwaway_schema

from app.core.words import normalize_scored_word
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
from app.schemas.stories import DraftStory
from app.services.difficulty import select_difficulty_target
from app.services.scoring import process_line_score
from app.services.story_pipeline import generate_validated_story
from app.services.story_templates import FALLBACK_TEMPLATES
from app.services.vocabulary_validator import tokenize

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
    with throwaway_schema("seams_test", TABLES, not_tested="the scoring/generation seams") as s:
        yield s


def make_child(db: Session) -> Child:
    caregiver = Caregiver(display_name="Test Caregiver")
    db.add(caregiver)
    db.flush()
    child = Child(caregiver_id=caregiver.id, display_name="Test Child", grade_level=1)
    db.add(child)
    db.flush()
    return child


def read_lines(db: Session, child: Child, lines: list[str], status: str) -> None:
    """The child reads each line once, in one reading session; every word gets `status`.

    The lines are different StoryLine rows, so this stays true if a re-read of one line is
    ever counted differently from a first read.
    """
    story = Story(child_id=child.id, title="Test", status="validated")
    db.add(story)
    db.flush()
    reading = ReadingSession(child_id=child.id, story_id=story.id)
    story_lines = [
        StoryLine(story_id=story.id, line_number=number, text=text)
        for number, text in enumerate(lines, start=1)
    ]
    db.add_all([reading, *story_lines])
    db.flush()
    for story_line in story_lines:
        score = ScoreResult(
            words=[WordScore(expected_word=w, status=status) for w in story_line.text.split()]
        )
        process_line_score(db, reading.id, story_line.id, score)


def codes(db: Session, pattern_ids: tuple[int, ...]) -> list[str]:
    rows = db.execute(
        select(PhonicsPattern.code)
        .where(PhonicsPattern.phonics_pattern_id.in_(pattern_ids))
        .order_by(PhonicsPattern.sequence_order)
    )
    return [code for (code,) in rows]


# --- scoring -> difficulty engine ------------------------------------------------------------


def test_scored_lines_move_mastery_and_change_the_next_difficulty_target(db: Session) -> None:
    child = make_child(db)
    before = select_difficulty_target(db, child.id)
    assert codes(db, before.reinforce_pattern_ids) == []
    assert codes(db, before.stretch_pattern_ids) == ["digraph_sh", "digraph_ch"]

    # "ship wish" is two SH words per line: three lines read well = 6 of 6 = mastered.
    read_lines(db, child, ["ship wish"] * 3, "mastered")
    after = select_difficulty_target(db, child.id)

    assert codes(db, after.reinforce_pattern_ids) == ["digraph_sh"]
    assert codes(db, after.stretch_pattern_ids) == ["digraph_ch", "digraph_th"]


def test_misread_lines_pull_a_mastered_pattern_back_to_stretch(db: Session) -> None:
    child = make_child(db)
    read_lines(db, child, ["ship wish"] * 3, "mastered")  # SH: 6 of 6
    assert codes(db, select_difficulty_target(db, child.id).reinforce_pattern_ids) == ["digraph_sh"]

    read_lines(db, child, ["ship wish"] * 4, "missed")  # SH: 6 of 14, confidence 7/16

    after = select_difficulty_target(db, child.id)
    assert codes(db, after.reinforce_pattern_ids) == []
    assert codes(db, after.stretch_pattern_ids) == ["digraph_sh", "digraph_ch"]


# --- generation -> scoring -------------------------------------------------------------------


def assert_line_is_scorable(line: str) -> None:
    # Single spaces, so the reader screen's split(' ') and the scorer's split() agree.
    assert line == " ".join(line.split()), line
    for word in line.split():
        # The validator saw exactly one word, and it is the form the scorer looks up.
        assert tokenize(word) == [normalize_scored_word(word)], word


def test_every_fallback_template_line_is_scorable() -> None:
    # Fallback templates skip clean_draft and shape_problem, so this test is their guard.
    for template in FALLBACK_TEMPLATES:
        for line in template.lines:
            assert_line_is_scorable(line)


def test_a_cleaned_llm_draft_is_scorable() -> None:
    allowed = frozenset(
        token
        for template in FALLBACK_TEMPLATES
        for text in (template.title, *template.lines)
        for token in tokenize(text)
    )
    messy = DraftStory(
        title="Ship  Wish",
        theme="a frog",
        pattern_codes=("digraph_sh",),
        lines=(
            "A  frog sat by a ship. ",
            ' "I wish to go,"   said\tthe frog.',
            "The frog had a wish.",
        ),
    )
    with patch("app.services.story_pipeline.generate_story_draft", return_value=messy):
        story = generate_validated_story([], (), allowed, max_attempts=1)

    assert (story.source, story.attempts) == ("llm", 1)
    assert story.title == "Ship Wish"
    for line in story.lines:
        assert_line_is_scorable(line)


def test_every_word_of_a_validated_story_finds_its_vocabulary_row(db: Session) -> None:
    # The whole point of the validator/scorer agreement: no word of a saved line is
    # "not in the vocabulary" to the scorer, so every word is credited.
    child = make_child(db)
    for template in FALLBACK_TEMPLATES:
        read_lines(db, child, list(template.lines), "mastered")

    unmatched = list(
        db.scalars(
            select(ReadingAttempt.expected_word).where(ReadingAttempt.vocabulary_word_id.is_(None))
        )
    )
    assert unmatched == []
