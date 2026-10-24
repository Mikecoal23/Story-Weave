from unittest.mock import patch

import anthropic
import httpx
import pytest

from app.core.config import settings
from app.models.entities import PhonicsPattern
from app.schemas.stories import DraftStory
from app.services.story_generation import LLMNotConfiguredError
from app.services.story_pipeline import (
    MAX_THEME_LENGTH,
    MAX_TITLE_LENGTH,
    NoValidStoryError,
    generate_validated_story,
    rank_fallback_templates,
)
from app.services.story_templates import FALLBACK_TEMPLATES
from app.services.vocabulary_validator import tokenize

# Every word the three fallback templates use, so they always validate in these tests.
ALLOWED = frozenset(
    token
    for template in FALLBACK_TEMPLATES
    for text in (template.title, *template.lines)
    for token in tokenize(text)
)

GOOD = DraftStory(
    title="Ship Wish",
    theme="a frog",
    pattern_codes=("digraph_sh",),
    lines=("A frog sat by a ship.", "The frog had a wish."),
)
BAD = DraftStory(
    title="Ship Wish",
    theme="a frog",
    pattern_codes=("digraph_sh",),
    lines=("A dragon sat by a ship.", "The dragon had a wish."),
)


def make_patterns(*codes: str) -> list[PhonicsPattern]:
    return [
        PhonicsPattern(
            phonics_pattern_id=i,
            code=code,
            label=code,
            category="c",
            example_words=["x"],
            sequence_order=i * 10,
        )
        for i, code in enumerate(codes, start=1)
    ]


def run(drafts: list, patterns=None, allowed=ALLOWED, max_attempts=3):
    """Run the pipeline with generate_story_draft returning/raising `drafts` in order."""
    with patch("app.services.story_pipeline.generate_story_draft", side_effect=drafts) as mock:
        story = generate_validated_story(
            patterns or make_patterns("digraph_sh"), ("frogs",), allowed, max_attempts
        )
    return story, mock


def test_a_valid_first_draft_is_returned_without_retrying() -> None:
    story, mock = run([GOOD])
    assert story.source == "llm"
    assert story.attempts == 1
    assert story.lines == GOOD.lines
    assert mock.call_count == 1
    assert mock.call_args.args[3] is None  # no feedback on the first try


def test_a_rejected_draft_is_retried_with_the_offending_words_as_feedback() -> None:
    story, mock = run([BAD, GOOD])
    assert story.source == "llm"
    assert story.attempts == 2
    feedback = mock.call_args_list[1].args[3]
    assert "dragon" in feedback


def test_three_rejections_fall_back_to_a_template() -> None:
    story, mock = run([BAD, BAD, BAD])
    assert story.source == "fallback"
    assert story.attempts == 3
    assert mock.call_count == 3
    assert story.title in {t.title for t in FALLBACK_TEMPLATES}


def test_a_valid_third_draft_still_counts_as_llm() -> None:
    story, _ = run([BAD, BAD, GOOD])
    assert (story.source, story.attempts) == ("llm", 3)


def test_max_attempts_is_tunable() -> None:
    story, mock = run([BAD, BAD, BAD, BAD, BAD], max_attempts=5)
    assert mock.call_count == 5
    assert story.source == "fallback"
    story, mock = run([BAD], max_attempts=1)
    assert mock.call_count == 1
    assert story.source == "fallback"


def test_max_attempts_defaults_to_the_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "story_max_attempts", 2)
    with patch("app.services.story_pipeline.generate_story_draft", return_value=BAD) as mock:
        story = generate_validated_story(make_patterns("digraph_sh"), (), ALLOWED)
    assert mock.call_count == 2
    assert story.source == "fallback"
    assert story.attempts == 2


def test_an_unparseable_reply_uses_an_attempt_and_asks_for_json_only() -> None:
    story, mock = run([ValueError("bad json"), GOOD])
    assert story.attempts == 2
    assert "parsed" in mock.call_args_list[1].args[3]


def test_a_missing_key_in_the_reply_is_a_rejection_not_a_crash() -> None:
    story, _ = run([KeyError("title"), IndexError(), TypeError(), GOOD])
    assert story.source == "fallback"  # three bad replies exhaust the budget


def test_an_api_error_uses_an_attempt_and_the_loop_continues() -> None:
    error = anthropic.APIConnectionError(request=httpx.Request("POST", "https://example.test"))
    story, mock = run([error, GOOD])
    assert story.source == "llm"
    assert story.attempts == 2
    assert mock.call_args_list[1].args[3] is None  # nothing to tell the model


def test_every_attempt_failing_with_api_errors_still_returns_a_story() -> None:
    error = anthropic.APIConnectionError(request=httpx.Request("POST", "https://example.test"))
    story, _ = run([error, error, error])
    assert story.source == "fallback"


def test_a_missing_api_key_uses_every_attempt_then_falls_back() -> None:
    missing = LLMNotConfiguredError("no key")
    story, mock = run([missing, missing, missing])
    assert (story.source, story.attempts) == ("fallback", 3)
    assert mock.call_args_list[1].args[3] is None  # nothing to tell the model


@pytest.mark.parametrize(
    ("broken", "expected_feedback"),
    [
        (GOOD.model_copy(update={"lines": ()}), "no lines"),
        (GOOD.model_copy(update={"lines": ("A frog sat.", "  ")}), "empty"),
        (GOOD.model_copy(update={"title": " "}), "title"),
        (GOOD.model_copy(update={"title": "a " * MAX_TITLE_LENGTH}), "title"),
        (GOOD.model_copy(update={"theme": "x" * (MAX_THEME_LENGTH + 1)}), "theme"),
    ],
)
def test_a_draft_that_cannot_be_saved_is_rejected_with_feedback(
    broken: DraftStory, expected_feedback: str
) -> None:
    # Each of these passes the vocabulary check (no unknown words) but would save an empty
    # story or fail the INSERT.
    story, mock = run([broken, GOOD])
    assert (story.source, story.attempts) == ("llm", 2)
    assert expected_feedback in mock.call_args_list[1].args[3]


def test_fallback_prefers_the_template_sharing_the_most_patterns() -> None:
    story, _ = run([BAD] * 3, patterns=make_patterns("blend_bl", "blend_cl"))
    assert story.title == "Clap and Jump"
    story, _ = run([BAD] * 3, patterns=make_patterns("digraph_th", "silent_e_a"))
    assert story.title == "Cake in the Rain"


def test_fallback_ties_keep_authoring_order() -> None:
    ranked = rank_fallback_templates(["unrelated_code"])
    assert ranked == list(FALLBACK_TEMPLATES)


def test_fallback_skips_a_template_that_fails_validation() -> None:
    # "chip" is in Ship Wish only; dropping it makes the best match invalid.
    allowed = ALLOWED - {"chip"}
    story, _ = run([BAD] * 3, patterns=make_patterns("digraph_sh"), allowed=allowed)
    assert story.source == "fallback"
    assert story.title != "Ship Wish"


def test_raises_when_neither_the_llm_nor_any_template_validates() -> None:
    with pytest.raises(NoValidStoryError):
        run([BAD] * 3, allowed=frozenset({"a"}))
