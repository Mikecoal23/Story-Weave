import re

from app.schemas.stories import FallbackStoryTemplate

# The seeded `vocabulary_word` table doesn't exist yet (blocked on the team's
# phonics-pattern ratification session), so these templates are drafted against
# the starter set documented in sprint1_phonics_pattern_starter_set.md instead.
# They are NOT yet validated against the real controlled vocabulary -- re-check
# every word below once vocabulary_word is seeded (planning.md Decisions Log,
# 2026-10-07).

# sprint1_phonics_pattern_starter_set.md Section 1, "Example words" column.
STARTER_PATTERN_WORDS = frozenset(
    {
        "ship",
        "wish",  # digraph_sh
        "chip",
        "much",  # digraph_ch
        "this",
        "bath",  # digraph_th
        "blue",
        "black",  # blend_bl
        "clap",
        "clock",  # blend_cl
        "frog",
        "from",  # blend_fr
        "cake",
        "name",  # silent_e_a
        "rain",
        "play",  # vowel_team_ai_ay
        "jump",
        "lamp",  # final_blend_mp
    }
)

# sprint1_phonics_pattern_starter_set.md Section 2.
STARTER_SIGHT_WORDS = frozenset({"said", "they", "of", "the", "was", "to", "you"})

# Basic function/verb words needed to make grammatical sentences out of the
# starter set above. None of these are in sprint1_phonics_pattern_starter_set.md
# yet -- flagged in planning.md as an additional ask for the ratification
# session, not assumed on the team's behalf.
DRAFT_GLUE_WORDS = frozenset(
    {
        "a",
        "after",
        "and",
        "ate",
        "by",
        "can",
        "fell",
        "fun",
        "go",
        "had",
        "has",
        "i",
        "in",
        "is",
        "like",
        "sat",
    }
)

ALLOWED_DRAFT_WORDS = STARTER_PATTERN_WORDS | STARTER_SIGHT_WORDS | DRAFT_GLUE_WORDS

_WORD_RE = re.compile(r"[a-z']+")


def words_in(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


FALLBACK_TEMPLATES: tuple[FallbackStoryTemplate, ...] = (
    FallbackStoryTemplate(
        title="Ship Wish",
        theme="a frog and a ship",
        pattern_codes=("digraph_sh", "blend_fr"),
        lines=(
            "A frog sat by a ship.",
            "The frog had a wish.",
            '"I wish to go," said the frog.',
            "A chip fell from the ship.",
            "The frog ate the chip.",
            '"I like the ship," said the frog.',
        ),
    ),
    FallbackStoryTemplate(
        title="Clap and Jump",
        theme="a lamp and a clock",
        pattern_codes=("blend_bl", "blend_cl", "final_blend_mp"),
        lines=(
            "The clock was black.",
            "A blue lamp sat by the clock.",
            '"Clap, clap," said the clock.',
            "The lamp can jump.",
            '"I like to jump," said the lamp.',
            "The blue lamp and black clock had fun.",
        ),
    ),
    FallbackStoryTemplate(
        title="Cake in the Rain",
        theme="playing in the rain",
        pattern_codes=("digraph_th", "silent_e_a", "vowel_team_ai_ay"),
        lines=(
            "This is a cake.",
            "The cake has a name.",
            "They like to play in the rain.",
            '"This rain is fun," they said.',
            '"I like this cake," they said.',
            "They had a bath after the rain.",
        ),
    ),
)
