import pytest

from app.services.vocabulary_validator import tokenize


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
