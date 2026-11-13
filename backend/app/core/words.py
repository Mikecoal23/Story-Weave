from string import punctuation


def normalize_word(raw: str) -> str:
    """Canonical form for a vocabulary word: trimmed, lowercase, straight apostrophe.

    vocabulary_word has CHECK constraints for lowercase and trimmed. Curly apostrophes
    are folded to ASCII so "don’t" from a transcript matches "don't" in the table, and
    "I" is stored as "i". Anything that looks words up (e.g. scoring) must call this
    first. Lives in app/ so the services don't import from scripts/; scripts.seed_data
    imports it from here.
    """
    return raw.replace("’", "'").replace("‘", "'").strip().lower()


def normalize_scored_word(raw: str) -> str:
    """The form of one word of a line as scoring and the dashboard look it up.

    `normalize_word`, then ASCII punctuation trimmed from both ends, apostrophes kept
    ("Ship," -> "ship", "don't" stays). Curly double quotes and dashes are NOT trimmed, so
    a word like "“hi,”" stays as it is and finds no vocabulary row. The story pipeline
    rejects such words (see `unscorable_word`) so a saved line always matches.
    """
    return normalize_word(raw).strip(punctuation.replace("'", ""))
