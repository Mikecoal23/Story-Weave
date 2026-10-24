import json
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models import PhonicsMastery, ReadingAttempt, ReadingSession, StoryLine, VocabularyWord
from app.schemas.scoring import ScoreResult, WordScore
from app.services.scoring import _parse_azure_assessment, process_line_score


def test_parse_azure_assessment_maps_word_error_types() -> None:
    result = _parse_azure_assessment(
        json.dumps(
            {
                "NBest": [
                    {
                        "Words": [
                            {
                                "Word": "the",
                                "PronunciationAssessment": {"ErrorType": "None"},
                            },
                            {
                                "Word": "cat",
                                "PronunciationAssessment": {
                                    "ErrorType": "Mispronunciation"
                                },
                            },
                            {
                                "Word": "sat",
                                "PronunciationAssessment": {"ErrorType": "Omission"},
                            },
                            {
                                "Word": "extra",
                                "PronunciationAssessment": {"ErrorType": "Insertion"},
                            },
                        ]
                    }
                ]
            }
        ),
        "the cat sat",
    )

    assert [word.status for word in result.words] == ["mastered", "shaky", "missed"]
    assert [word.expected_word for word in result.words] == ["the", "cat", "sat"]
    assert result.words[1].recognized_word == "cat"
    assert result.words[2].recognized_word is None


def test_parse_azure_assessment_rejects_unknown_error_type() -> None:
    with pytest.raises(ValueError, match="Unsupported Azure Speech error type"):
        _parse_azure_assessment(
            json.dumps(
                {
                    "NBest": [
                        {
                            "Words": [
                                {
                                    "Word": "word",
                                    "PronunciationAssessment": {"ErrorType": "Unknown"},
                                }
                            ]
                        }
                    ]
                }
            ),
            "word",
        )


def test_process_line_score_persists_words_and_updates_non_sight_patterns() -> None:
    session_id = uuid4()
    story_id = uuid4()
    line_id = uuid4()
    child_id = uuid4()
    reading_session = ReadingSession(
        id=session_id,
        child_id=child_id,
        story_id=story_id,
        status="in_progress",
    )
    story_line = StoryLine(id=line_id, story_id=story_id, line_number=1, text="ship, the")
    ship = VocabularyWord(vocabulary_word_id=1, word="ship", is_sight_word=False)
    the = VocabularyWord(vocabulary_word_id=2, word="the", is_sight_word=True)
    existing_mastery = PhonicsMastery(
        child_id=child_id,
        phonics_pattern_id=10,
        mastery_score=0.5,
        attempts_count=2,
        correct_count=1,
    )
    session = Mock(spec=Session)
    session.execute.return_value.all.return_value = [(ship, 10), (ship, 20), (the, 30)]
    added: list[object] = []
    session.add.side_effect = added.append

    def get(model: type, identity: object) -> object | None:
        if model is ReadingSession:
            return reading_session
        if model is StoryLine:
            return story_line
        if model is PhonicsMastery and identity == (child_id, 10):
            return existing_mastery
        return None

    session.get.side_effect = get
    process_line_score(
        session,
        session_id,
        line_id,
        ScoreResult(
            words=[
                WordScore(expected_word="Ship,", recognized_word="ship", status="mastered"),
                WordScore(expected_word="the", recognized_word=None, status="missed"),
            ]
        ),
    )

    attempts = [item for item in added if isinstance(item, ReadingAttempt)]
    new_mastery = [item for item in added if isinstance(item, PhonicsMastery)]
    assert [(attempt.word_index, attempt.vocabulary_word_id) for attempt in attempts] == [
        (1, 1),
        (2, 2),
    ]
    assert existing_mastery.attempts_count == 3
    assert existing_mastery.correct_count == 2
    assert existing_mastery.mastery_score == pytest.approx(2 / 3)
    assert len(new_mastery) == 1
    assert new_mastery[0].phonics_pattern_id == 20
    assert new_mastery[0].attempts_count == 1
    assert new_mastery[0].correct_count == 1
    session.flush.assert_called_once_with()


def test_process_line_score_rejects_a_line_outside_the_session() -> None:
    session_id = uuid4()
    session = Mock(spec=Session)
    session.get.side_effect = [
        ReadingSession(id=session_id, child_id=uuid4(), story_id=uuid4(), status="in_progress"),
        StoryLine(id=uuid4(), story_id=uuid4(), line_number=1, text="ship"),
    ]

    with pytest.raises(ValueError, match="does not belong"):
        process_line_score(
            session,
            session_id,
            uuid4(),
            ScoreResult(words=[WordScore(expected_word="ship", status="mastered")]),
        )

    session.execute.assert_not_called()
