import json

import pytest

from app.services.scoring import _parse_azure_assessment


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
