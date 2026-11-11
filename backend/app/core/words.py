def normalize_word(raw: str) -> str:
    """Canonical form for a vocabulary word: trimmed, lowercase, straight apostrophe.

    vocabulary_word has CHECK constraints for lowercase and trimmed. Curly apostrophes
    are folded to ASCII so "don’t" from a transcript matches "don't" in the table, and
    "I" is stored as "i". Anything that looks words up (e.g. scoring) must call this
    first. Lives in app/ so the services don't import from scripts/; scripts.seed_data
    imports it from here.
    """
    return raw.replace("’", "'").replace("‘", "'").strip().lower()
