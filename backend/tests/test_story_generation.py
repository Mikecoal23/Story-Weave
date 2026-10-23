import json
from unittest.mock import MagicMock, patch

import pytest

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
def test_generate_story_draft_accepts_json_wrapped_in_a_code_fence(
    mock_anthropic_cls: MagicMock,
) -> None:
    # What the real model returns: the JSON inside a ```json fence (seen 2026-10-22).
    payload = {"title": "Ship Wish", "theme": "a ship", "lines": ["A frog sat by a ship."]}
    response = MagicMock()
    response.content = [MagicMock(text=f"```json\n{json.dumps(payload, indent=2)}\n```")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = response
    mock_anthropic_cls.return_value = mock_client

    draft = generate_story_draft(
        [make_pattern("digraph_sh", "SH", ["ship"])], (), frozenset({"a", "frog", "ship"})
    )

    assert draft.title == "Ship Wish"
    assert draft.lines == ("A frog sat by a ship.",)


@patch("app.services.story_generation.anthropic.Anthropic")
def test_generate_story_draft_still_rejects_a_reply_with_no_json(
    mock_anthropic_cls: MagicMock,
) -> None:
    response = MagicMock()
    response.content = [MagicMock(text="Sorry, I cannot write that.")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = response
    mock_anthropic_cls.return_value = mock_client

    with pytest.raises(ValueError):
        generate_story_draft([make_pattern("digraph_sh", "SH", ["ship"])], (), frozenset({"a"}))


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
    assert "rejected" not in user_content  # no feedback on a first attempt


@patch("app.services.story_generation.anthropic.Anthropic")
def test_generate_story_draft_includes_retry_feedback_in_the_prompt(
    mock_anthropic_cls: MagicMock,
) -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = fake_response(
        {"title": "T", "theme": "t", "lines": ["One.", "Two."]}
    )
    mock_anthropic_cls.return_value = mock_client

    patterns = [make_pattern("digraph_sh", "SH", ["ship", "wish"])]
    generate_story_draft(
        patterns, (), frozenset({"ship"}), feedback="It used words not allowed: dragon."
    )

    _, kwargs = mock_client.messages.create.call_args
    user_content = kwargs["messages"][0]["content"]
    assert "previous attempt was rejected" in user_content
    assert "dragon" in user_content
