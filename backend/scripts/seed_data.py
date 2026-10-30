"""Seed data for phonics_pattern, vocabulary_word and vocabulary_word_pattern.

Pure data and validation -- no database access -- so it can be unit-tested offline.
This module is the single source of truth: scripts.seed_vocabulary makes the database
match it, so changing a word's category here and re-running is how a word is promoted
or demoted between "sight word" and "pattern word".

Sources: sprint1_phonics_pattern_starter_set.md (pattern metadata, sequence_order) and
the ratified word table (planning.md Decisions Log, seeding entry). Sight words are the
Dolch list (220 words) minus every Dolch word that is a pattern word. Word endings
(-s/-es, -ed, -ing) are generated from the base-word lists below (2026-10-30).
"""

import re
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

# Word endings (2026-10-30, Open Question 17): without them the LLM writes "the frog thank
# the fish". Each form is seeded as its own row with its base word's category and pattern
# tags, so scoring finds "jumped" and a miss on it counts against -MP, like "jump".
# Takes -s/-es, -ed and -ing.
REGULAR_VERBS: tuple[str, ...] = (
    # pattern words
    "ship shop wish rush mash wash fish show chop chat chase thank blink clap clip clean "
    "name wait rain play stay jump bump pump dump camp mail tape "
    # sight words
    "look help like want ask walk stop open live call work pull use start pick carry laugh try"
).split()
# Takes -s/-es and -ing only: the past tense is irregular (ran, made, said), so it is seeded
# as its own word or not at all.
IRREGULAR_VERBS: tuple[str, ...] = (
    "make take shake think say pay shut "  # pattern words
    "run find come go do see eat ride get sit sing read tell sleep keep bring drink hold cut "
    "fly give draw grow buy write know put fall hurt"  # sight words
).split()
# Takes -s/-es only.
PLURAL_NOUNS: tuple[str, ...] = (
    "shell dish chip moth path bath cake game gate lake tail day way lamp clock frog clam "
    "club "  # pattern words
    "ball bed bird box boy car cow dog door duck egg farm girl hand hill home house nest pig "
    "toy tree"  # nouns
).split()

_VOWELS = "aeiou"


def _doubles_final_consonant(base: str) -> bool:
    """A one-vowel word ending consonant-vowel-consonant doubles its last letter: clapped."""
    return (
        len(re.findall(f"[{_VOWELS}]+", base)) == 1
        and len(base) >= 3
        and base[-1] not in _VOWELS + "wxy"
        and base[-2] in _VOWELS
        and base[-3] not in _VOWELS
    )


def add_ending(base: str, ending: str) -> str:
    """Spell `base` + `ending` ("s", "ed" or "ing") with the regular spelling rules.

    wish -> wishes, carry -> carries, chase -> chased, carry -> carried, chase -> chasing,
    clap -> clapped / clapping.
    """
    consonant_y = base.endswith("y") and base[-2] not in _VOWELS
    if ending == "s":
        if base.endswith(("s", "sh", "ch", "x", "z", "o")):
            return base + "es"
        return base[:-1] + "ies" if consonant_y else base + "s"
    if ending == "ed":
        if base.endswith("e"):
            return base + "d"
        if consonant_y:
            return base[:-1] + "ied"
    elif base.endswith("e") and not base.endswith("ee"):
        return base[:-1] + "ing"
    if _doubles_final_consonant(base):
        base += base[-1]
    return base + ending


def inflected_words(base_words: dict[str, WordSeed]) -> list[WordSeed]:
    """The ending forms of the three lists above, each with its base word's category and tags.

    A form that is already seeded (does, goes) is skipped, so its own row wins.
    """
    forms: dict[str, WordSeed] = {}
    for bases, endings in (
        (REGULAR_VERBS, ("s", "ed", "ing")),
        (IRREGULAR_VERBS, ("s", "ing")),
        (PLURAL_NOUNS, ("s",)),
    ):
        for base in bases:
            seed = base_words.get(base)
            if seed is None:
                raise ValueError(f"ending base {base!r} is not a seeded word")
            for ending in endings:
                form = add_ending(base, ending)
                if form not in base_words:
                    forms[form] = WordSeed(form, seed.is_sight_word, seed.pattern_codes)
    return list(forms.values())


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
    words += inflected_words({seed.word: seed for seed in words})
    for seed in words:
        if not seed.word or seed.word != normalize_word(seed.word):
            raise ValueError(f"word {seed.word!r} is not normalized")
    return sorted(words, key=lambda s: s.word)
