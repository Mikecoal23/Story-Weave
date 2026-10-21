import re

from scripts.seed_data import normalize_word

# A token is a run of letters/digits, optionally joined by single inner apostrophes
# ("don't", "it's"). Edge apostrophes (quotes, trailing possessives) are not part of a
# word. Digits are kept as tokens on purpose: a "5" is never in the vocabulary, so the
# validator rejects it instead of silently ignoring it. `[^\W_]` is "letter or digit".
_TOKEN_RE = re.compile(r"[^\W_]+(?:'[^\W_]+)*")


def tokenize(text: str) -> list[str]:
    """Split text into normalised word tokens, in order.

    Runs `normalize_word` first (lowercase, curly apostrophes folded to a straight one),
    so tokens compare equal to `vocabulary_word.word`. Punctuation and whitespace are
    separators; hyphens split a word in two, so each half is checked on its own.
    """
    return _TOKEN_RE.findall(normalize_word(text))
