"""Seed data for phonics_pattern, vocabulary_word and vocabulary_word_pattern.

Pure data and validation -- no database access -- so it can be unit-tested offline.
This module is the single source of truth: scripts.seed_vocabulary makes the database
match it, so changing a word's category here and re-running is how a word is promoted
or demoted between "sight word" and "pattern word".

Sources: sprint1_phonics_pattern_starter_set.md (pattern metadata, sequence_order) and
the ratified word table (planning.md Decisions Log, seeding entry). Sight words are the
Dolch list (220 words) minus every Dolch word that is a pattern word.
"""

from dataclasses import dataclass

from app.core.words import normalize_word


@dataclass(frozen=True)
class PatternSeed:
    code: str
    label: str
    category: str
    example_words: tuple[str, ...]
    sequence_order: int


@dataclass(frozen=True)
class WordSeed:
    word: str
    is_sight_word: bool
    pattern_codes: frozenset[str]


# Gapped by 10 so a CVC pattern can later be inserted at 1-9 without renumbering.
PATTERNS: tuple[PatternSeed, ...] = (
    PatternSeed("digraph_sh", "SH", "consonant digraph", ("ship", "wish"), 10),
    PatternSeed("digraph_ch", "CH", "consonant digraph", ("chip", "much"), 20),
    PatternSeed("digraph_th", "TH", "consonant digraph", ("this", "bath"), 30),
    PatternSeed("blend_bl", "BL", "initial L-blend", ("blue", "black"), 40),
    PatternSeed("blend_cl", "CL", "initial L-blend", ("clap", "clock"), 50),
    PatternSeed("blend_fr", "FR", "initial R-blend", ("frog", "from"), 60),
    PatternSeed("silent_e_a", "a_e (silent-e)", "VCe long vowel", ("cake", "name"), 70),
    PatternSeed("vowel_team_ai_ay", "ai / ay", "long-a vowel team", ("rain", "play"), 80),
    PatternSeed("final_blend_mp", "-MP", "final blend", ("jump", "lamp"), 90),
)

# Words per pattern. A word listed under two patterns is tagged with both (decision E),
# so a miss on "shake" counts against SH and a_e.
# Dagger words (black, blue, blink, clock, play, stay) also contain a pattern that is
# not taught yet; they are tagged only with their intended pattern (decision B).
PATTERN_WORDS: dict[str, tuple[str, ...]] = {
    "digraph_sh": (
        "ship shop shell shed shut fish wish dish rush mash fresh shake "
        "wash show shall"  # promoted from Dolch
    ).split(),
    "digraph_ch": (
        "chip chop chin chat much such rich lunch chase champ which"  # promoted from Dolch
    ).split(),
    "digraph_th": (
        "this that then them thin with bath math path moth "
        "these those think thank three both together"  # promoted from Dolch
    ).split(),
    "blend_bl": "blob blot bled blip blab black blue blink".split(),
    "blend_cl": (
        "clap clip clam clan club clog clot clad clay clock clean"  # promoted from Dolch
    ).split(),
    "blend_fr": "frog from fret fresh frill".split(),
    "silent_e_a": (
        "cake name make take game gate late lake same tape shake chase "
        "made gave came ate"  # promoted from Dolch
    ).split(),
    "vowel_team_ai_ay": (
        "rain day say may way pay tail mail wait clay play stay away always"  # promoted from Dolch
    ).split(),
    "final_blend_mp": "jump lamp camp damp bump pump lump dump limp ramp champ".split(),
}

# Dolch sight words by grade (220). Whether each becomes a sight word or a pattern word
# is decided by PATTERN_WORDS above: a Dolch word in the pattern table stays a pattern
# word. Still sight words despite containing a pattern's letters: the, they, there, their
# (irregular).
DOLCH_WORDS: tuple[str, ...] = tuple(
    (
        # pre-primer (40)
        "the to and a I you it in said for up look is go we little down can see not one my "
        "me big come blue red where jump away here help make yellow two play run find three "
        "funny "
        # primer (52)
        "he was that she on they but at with all there out be have am do did what so get "
        "like this will yes went are now no came ride into good want too pretty four saw "
        "well ran brown eat who new must black white soon our ate say under please "
        # first grade (41)
        "of his had him her some as then could when were them ask an over just from any how "
        "know put take every old by after think let going walk again may stop fly round give "
        "once open has live thank "
        # second grade (46)
        "would very your its around don't right green their call sleep five wash or before "
        "been off cold tell work first does goes write always made gave us buy those use fast "
        "pull both sit which read why found because best upon these sing wish many "
        # third grade (41)
        "if long about got six never seven eight today myself much keep try start ten bring "
        "drink only better hold warm full done light pick hurt cut kind fall carry small own "
        "show hot far draw clean grow together shall laugh"
    ).split()
)

# Decodable words with no pattern and not sight words (decision C): the fallback story
# templates need them, and they keep their slot open for a future CVC pattern.
FILLER_WORDS: tuple[str, ...] = ("sat", "fell", "fun")

# A small subset of the Dolch noun list (not in the repo), chosen to avoid patterns that
# are not taught yet, so stories can have subjects and objects.
NOUN_WORDS: tuple[str, ...] = (
    "ball bed bird box boy car cow dog door duck egg farm girl hand hill home house man "
    "milk nest pig sun toy tree"
).split()


def build_words() -> list[WordSeed]:
    """Combine the lists above into validated WordSeed rows, sorted by word."""
    pattern_codes = {p.code for p in PATTERNS}
    unknown = set(PATTERN_WORDS) - pattern_codes
    if unknown:
        raise ValueError(f"PATTERN_WORDS uses unknown pattern codes: {sorted(unknown)}")

    tags: dict[str, set[str]] = {}
    for code, words in PATTERN_WORDS.items():
        for raw in words:
            word = normalize_word(raw)
            if raw != word:
                raise ValueError(f"pattern word {raw!r} is not normalized")
            tags.setdefault(word, set()).add(code)

    sight = {normalize_word(w) for w in DOLCH_WORDS} - set(tags)
    filler = {normalize_word(w) for w in FILLER_WORDS}
    nouns = {normalize_word(w) for w in NOUN_WORDS}

    for name_a, set_a, name_b, set_b in (
        ("sight", sight, "filler", filler),
        ("sight", sight, "noun", nouns),
        ("filler", filler, "noun", nouns),
        ("pattern", set(tags), "filler", filler),
        ("pattern", set(tags), "noun", nouns),
    ):
        both = set_a & set_b
        if both:
            raise ValueError(f"words in both {name_a} and {name_b}: {sorted(both)}")

    words = [WordSeed(w, False, frozenset(codes)) for w, codes in tags.items()]
    words += [WordSeed(w, True, frozenset()) for w in sight]
    words += [WordSeed(w, False, frozenset()) for w in filler | nouns]
    for seed in words:
        if not seed.word or seed.word != normalize_word(seed.word):
            raise ValueError(f"word {seed.word!r} is not normalized")
    return sorted(words, key=lambda s: s.word)
