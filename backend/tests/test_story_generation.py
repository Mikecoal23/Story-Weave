import json
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.models import PhonicsPattern
from app.services.story_generation import LLMNotConfiguredError, generate_story_draft


@pytest.fixture(autouse=True)
def api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    # The SDK is mocked; a key only has to be present, whatever backend/.env holds.
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")


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
def test_generate_story_draft_keeps_a_character_from_the_list(
    mock_anthropic_cls: MagicMock,
) -> None:
    mock_anthropic_cls.return_value.messages.create.return_value = fake_response(
        {"title": "T", "theme": "t", "character": "frog", "lines": ["One."]}
    )

    draft = generate_story_draft([make_pattern("digraph_sh", "SH", ["ship"])], (), frozenset())

    assert draft.character == "frog"


@pytest.mark.parametrize("payload_extra", [{"character": "zzz"}, {"character": None}, {}])
@patch("app.services.story_generation.anthropic.Anthropic")
def test_generate_story_draft_uses_default_for_an_unknown_or_missing_character(
    mock_anthropic_cls: MagicMock, payload_extra: dict
) -> None:
    mock_anthropic_cls.return_value.messages.create.return_value = fake_response(
        {"title": "T", "theme": "t", "lines": ["One."], **payload_extra}
    )

    draft = generate_story_draft([make_pattern("digraph_sh", "SH", ["ship"])], (), frozenset())

    assert draft.character == "default"


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


@patch("app.services.story_generation.anthropic.Anthropic")
def test_the_client_has_a_short_timeout_and_no_sdk_retries(mock_anthropic_cls: MagicMock) -> None:
    mock_anthropic_cls.return_value.messages.create.return_value = fake_response(
        {"title": "T", "theme": "t", "lines": ["One."]}
    )

    generate_story_draft([make_pattern("digraph_sh", "SH", ["ship"])], (), frozenset({"one"}))

    _, kwargs = mock_anthropic_cls.call_args
    assert kwargs["timeout"] <= 30
    assert kwargs["max_retries"] == 0  # the pipeline does the retrying


@patch("app.services.story_generation.anthropic.Anthropic")
def test_a_missing_api_key_raises_before_any_call(
    mock_anthropic_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "anthropic_api_key", None)

    with pytest.raises(LLMNotConfiguredError):
        generate_story_draft([make_pattern("digraph_sh", "SH", ["ship"])], (), frozenset({"a"}))
    mock_anthropic_cls.assert_not_called()


def text_block(raw_text: str) -> MagicMock:
    return MagicMock(text=raw_text)


# A first block that is not text (a tool-use block has no `.text`).
NON_TEXT_BLOCK = MagicMock(spec=["type", "id", "name", "input"])

NOT_A_STORY = [
    pytest.param([], id="empty content"),
    pytest.param([NON_TEXT_BLOCK], id="first block is not text"),
    pytest.param([text_block("[1, 2]")], id="json list"),
    pytest.param([text_block('"just a string"')], id="json string"),
    pytest.param([text_block("null")], id="json null"),
    pytest.param(
        [text_block('{"title": "T", "theme": "t", "lines": "A frog sat."}')], id="lines is a string"
    ),
    pytest.param(
        [text_block('{"title": "T", "theme": "t", "lines": {"a": "b"}}')], id="lines is a dict"
    ),
    pytest.param(
        [text_block('{"title": "T", "theme": "t", "lines": ["One.", 2]}')], id="a line is a number"
    ),
    pytest.param(
        [text_block('{"title": 5, "theme": "t", "lines": ["One."]}')], id="title is a number"
    ),
    pytest.param(
        [text_block('{"title": "T", "theme": null, "lines": ["One."]}')], id="theme is null"
    ),
]


@pytest.mark.parametrize("content", NOT_A_STORY)
@patch("app.services.story_generation.anthropic.Anthropic")
def test_a_reply_that_is_not_a_story_raises_value_error(
    mock_anthropic_cls: MagicMock, content: list
) -> None:
    # ValueError is what the pipeline counts as a bad reply (one used attempt, then a retry),
    # so none of these may escape as AttributeError or TypeError (a 500 from the route).
    response = MagicMock()
    response.content = content
    mock_anthropic_cls.return_value.messages.create.return_value = response

    with pytest.raises(ValueError):
        generate_story_draft([make_pattern("digraph_sh", "SH", ["ship"])], (), frozenset({"a"}))
