import pytest

from app.core.words import normalize_scored_word


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Ship,", "ship"),
        ('"I', "i"),
        ('go,"', "go"),
        ("Don’t", "don't"),  # a curly apostrophe is folded, not trimmed
        ("don't.", "don't"),
        ("fun!?", "fun"),
    ],
)
def test_normalize_scored_word_trims_ascii_punctuation_and_keeps_apostrophes(
    raw: str, expected: str
) -> None:
    assert normalize_scored_word(raw) == expected


@pytest.mark.parametrize("raw", ["“hi,”", "ran—fast"])
def test_normalize_scored_word_leaves_curly_quotes_and_dashes_alone(raw: str) -> None:
    # Why the story pipeline must reject such words: scoring would look up this odd form.
    assert normalize_scored_word(raw) == raw.lower()
