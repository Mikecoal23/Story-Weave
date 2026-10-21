import pytest

from app.schemas.stories import DraftStory, FallbackStoryTemplate
from app.services.vocabulary_validator import tokenize, validate_story


def test_tokenize_lowercases_and_drops_punctuation() -> None:
    assert tokenize('"I wish to go," said the Frog.') == [
        "i",
        "wish",
        "to",
        "go",
        "said",
        "the",
        "frog",
    ]


def test_tokenize_keeps_inner_apostrophes() -> None:
    assert tokenize("I don't like it's") == ["i", "don't", "like", "it's"]


def test_tokenize_folds_curly_apostrophes() -> None:
    assert tokenize("don’t") == ["don't"]
    assert tokenize("don‘t") == ["don't"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("'hi'", ["hi"]),
        ("‘hi’", ["hi"]),
        ("the dogs' ball", ["the", "dogs", "ball"]),
        ("'", []),
        ("''hello''", ["hello"]),
    ],
)
def test_tokenize_ignores_edge_apostrophes(text: str, expected: list[str]) -> None:
    assert tokenize(text) == expected


def test_tokenize_keeps_digits_so_they_can_be_rejected() -> None:
    assert tokenize("I have 5 cats") == ["i", "have", "5", "cats"]
    assert tokenize("the 3rd pig") == ["the", "3rd", "pig"]


def test_tokenize_splits_hyphenated_words() -> None:
    assert tokenize("well-known") == ["well", "known"]


def test_tokenize_keeps_non_ascii_letters_instead_of_dropping_them() -> None:
    assert tokenize("café") == ["café"]


def test_tokenize_empty_and_punctuation_only() -> None:
    assert tokenize("") == []
    assert tokenize("... !? --") == []


# --- validate_story (pure, no database) ---

ALLOWED = frozenset({"a", "frog", "sat", "by", "the", "ship", "don't", "i"})


def make_story(*lines: str, title: str = "A Ship") -> DraftStory:
    return DraftStory(title=title, theme="t", pattern_codes=(), lines=lines)


def test_validate_story_accepts_a_story_made_only_of_allowed_words() -> None:
    result = validate_story(make_story("A frog sat by the ship.", "I don't."), ALLOWED)
    assert result.is_valid
    assert result.unknown_words == ()


def test_validate_story_reports_unknown_words_once_in_order() -> None:
    story = make_story("A dragon sat by the ship.", "The dragon flew.", "Zoom!")
    result = validate_story(story, ALLOWED)
    assert not result.is_valid
    assert result.unknown_words == ("dragon", "flew", "zoom")


def test_validate_story_checks_the_title() -> None:
    result = validate_story(make_story("A frog sat.", title="Dragon Day"), ALLOWED)
    assert result.unknown_words == ("dragon", "day")


def test_validate_story_rejects_digits() -> None:
    result = validate_story(make_story("A frog sat by 3 ships."), ALLOWED)
    assert result.unknown_words == ("3", "ships")


def test_validate_story_handles_case_punctuation_and_curly_apostrophes() -> None:
    story = make_story('"A FROG sat," said I.', "I don’t.")
    assert validate_story(story, ALLOWED).unknown_words == ("said",)


def test_validate_story_accepts_fallback_templates_too() -> None:
    template = FallbackStoryTemplate(
        title="A Ship", theme="t", pattern_codes=(), lines=("A frog sat.",)
    )
    assert validate_story(template, ALLOWED).is_valid
