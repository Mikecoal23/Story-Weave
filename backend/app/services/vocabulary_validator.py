import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.words import normalize_word
from app.models import VocabularyWord
from app.schemas.stories import DraftStory

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


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of checking one story against the controlled vocabulary."""

    # Words not in the vocabulary, in first-seen order, no duplicates.
    unknown_words: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.unknown_words


def load_allowed_vocabulary(db: Session) -> frozenset[str]:
    """Every word a story may use: all `vocabulary_word` rows.

    Sight, pattern, filler and noun words are all allowed;
    "sight" only changes how a word is scored, not whether a story may contain it.
    """
    return frozenset(db.scalars(select(VocabularyWord.word)))


def validate_story(story: DraftStory, allowed: frozenset[str]) -> ValidationResult:
    """Reject any story whose title or lines contain a word outside `allowed`.

    The title is checked too, since the child may read it. Pure function: the caller
    loads the vocabulary once (`load_allowed_vocabulary`) and reuses it across retries.
    """
    unknown: dict[str, None] = {}  # dict keeps first-seen order
    for text in (story.title, *story.lines):
        for token in tokenize(text):
            if token not in allowed:
                unknown[token] = None
    return ValidationResult(unknown_words=tuple(unknown))
