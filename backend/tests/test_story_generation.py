import json
from unittest.mock import MagicMock, patch

from app.models.entities import PhonicsPattern
from app.services.story_generation import generate_story_draft


def make_pattern(code: str, label: str, example_words: list[str]) -> PhonicsPattern:
    return PhonicsPattern(
        phonics_pattern_id=1,
        code=code,
        label=label,
        category="consonant digraph",
        example_words=example_words,
        sequence_order=10,
    )


def fake_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.content = [MagicMock(text=json.dumps(payload))]
    return response


@patch("app.services.story_generation.anthropic.Anthropic")
def test_generate_story_draft_parses_the_llm_response(mock_anthropic_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = fake_response(
        {
            "title": "Ship Wish",
            "theme": "a frog and a ship",
            "lines": ["A frog sat by a ship.", "The frog had a wish."],
        }
    )
    mock_anthropic_cls.return_value = mock_client

    patterns = [make_pattern("digraph_sh", "SH", ["ship", "wish"])]
    draft = generate_story_draft(patterns, ("frogs",), frozenset({"a", "frog", "ship", "wish"}))

    assert draft.title == "Ship Wish"
    assert draft.theme == "a frog and a ship"
    assert draft.pattern_codes == ("digraph_sh",)
    assert draft.lines == ("A frog sat by a ship.", "The frog had a wish.")


@patch("app.services.story_generation.anthropic.Anthropic")
def test_generate_story_draft_sends_patterns_and_vocabulary_to_the_model(
    mock_anthropic_cls: MagicMock,
) -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = fake_response(
        {"title": "T", "theme": "t", "lines": ["One.", "Two."]}
    )
    mock_anthropic_cls.return_value = mock_client

    patterns = [make_pattern("digraph_sh", "SH", ["ship", "wish"])]
    generate_story_draft(patterns, ("dinosaurs",), frozenset({"ship", "wish"}))

    _, kwargs = mock_client.messages.create.call_args
    user_content = kwargs["messages"][0]["content"]
    assert "digraph_sh" in user_content
    assert "dinosaurs" in user_content
    assert "ship" in user_content
