import pytest

from app.services.story_templates import FALLBACK_TEMPLATES
from app.services.vocabulary_validator import tokenize
from scripts import seed_data
from scripts.seed_data import PATTERNS, WordSeed, add_ending, build_words, normalize_word


def by_word() -> dict[str, WordSeed]:
    return {w.word: w for w in build_words()}


def test_normalize_word_trims_lowercases_and_straightens_apostrophes() -> None:
    assert normalize_word("  I ") == "i"
    assert normalize_word("Don’t") == "don't"
    assert normalize_word("don‘t") == "don't"


def test_every_word_is_unique_and_normalized() -> None:
    words = [w.word for w in build_words()]
    assert len(words) == len(set(words))
    assert all(w == normalize_word(w) and w for w in words)


def test_pattern_codes_and_sequence_orders_are_unique_and_gapped() -> None:
    assert len({p.code for p in PATTERNS}) == len(PATTERNS)
    orders = [p.sequence_order for p in PATTERNS]
    assert orders == list(range(10, 100, 10))


def test_no_sight_word_has_patterns() -> None:
    sight = [w for w in build_words() if w.is_sight_word]
    assert len(sight) > 150
    assert all(not w.pattern_codes for w in sight)


def test_every_pattern_word_is_tagged_and_not_sight() -> None:
    for word in build_words():
        if word.pattern_codes:
            assert not word.is_sight_word, word.word


def test_multi_pattern_words_have_every_expected_tag() -> None:
    words = by_word()
    assert words["shake"].pattern_codes == {"digraph_sh", "silent_e_a"}
    assert words["chase"].pattern_codes == {"digraph_ch", "silent_e_a"}
    assert words["fresh"].pattern_codes == {"digraph_sh", "blend_fr"}
    assert words["champ"].pattern_codes == {"digraph_ch", "final_blend_mp"}
    assert words["clay"].pattern_codes == {"blend_cl", "vowel_team_ai_ay"}


def test_dolch_overlap_words_are_pattern_words() -> None:
    words = by_word()
    overlap = (
        "this that then them with much wish black blue from make take say may play jump"
    ).split()
    assert all(words[w].pattern_codes and not words[w].is_sight_word for w in overlap)


def test_promoted_dolch_words_are_pattern_words() -> None:
    words = by_word()
    assert words["made"].pattern_codes == {"silent_e_a"}
    assert words["gave"].pattern_codes == {"silent_e_a"}
    assert words["came"].pattern_codes == {"silent_e_a"}
    assert words["ate"].pattern_codes == {"silent_e_a"}
    assert words["wash"].pattern_codes == {"digraph_sh"}
    assert words["which"].pattern_codes == {"digraph_ch"}
    assert words["away"].pattern_codes == {"vowel_team_ai_ay"}
    assert words["clean"].pattern_codes == {"blend_cl"}
    assert words["together"].pattern_codes == {"digraph_th"}


def test_irregular_th_words_stay_sight_words() -> None:
    words = by_word()
    for word in ("the", "they", "there", "their"):
        assert words[word].is_sight_word and not words[word].pattern_codes


def test_starter_sight_words_are_sight_words() -> None:
    # The sight words in sprint1_phonics_pattern_starter_set.md, Section 2.
    words = by_word()
    assert all(words[w].is_sight_word for w in ("said", "they", "of", "the", "was", "to", "you"))


def test_apostrophe_and_i_are_stored_normalized() -> None:
    words = by_word()
    assert words["don't"].is_sight_word
    assert words["i"].is_sight_word
    assert "I" not in words


def test_filler_and_nouns_are_unpatterned_non_sight_words() -> None:
    words = by_word()
    for word in (*seed_data.FILLER_WORDS, *seed_data.NOUN_WORDS):
        assert not words[word].is_sight_word and not words[word].pattern_codes, word


def test_all_dolch_words_are_present() -> None:
    assert len(seed_data.DOLCH_WORDS) == 220
    words = by_word()
    assert all(normalize_word(w) in words for w in seed_data.DOLCH_WORDS)


def test_fallback_templates_only_use_seeded_words() -> None:
    # Closes the "re-validate fallback templates against the seeded vocabulary" drift
    # risk from planning.md: every template word must exist in the seed data.
    words = by_word()
    for template in FALLBACK_TEMPLATES:
        used = {token for text in (template.title, *template.lines) for token in tokenize(text)}
        assert used <= set(words), f"{template.title}: {sorted(used - set(words))}"


def test_build_words_rejects_a_word_in_two_categories(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seed_data, "FILLER_WORDS", ("sat", "the"))
    with pytest.raises(ValueError, match="sight and filler"):
        build_words()


def test_build_words_rejects_unknown_pattern_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seed_data, "PATTERN_WORDS", {"nope": ("ship",)})
    with pytest.raises(ValueError, match="unknown pattern codes"):
        build_words()


@pytest.mark.parametrize(
    ("base", "ending", "expected"),
    [
        ("jump", "s", "jumps"),
        ("wish", "s", "wishes"),
        ("lunch", "s", "lunches"),
        ("box", "s", "boxes"),
        ("go", "s", "goes"),
        ("carry", "s", "carries"),
        ("play", "s", "plays"),
        ("jump", "ed", "jumped"),
        ("chase", "ed", "chased"),
        ("carry", "ed", "carried"),
        ("play", "ed", "played"),
        ("clap", "ed", "clapped"),
        ("open", "ed", "opened"),
        ("wait", "ed", "waited"),
        ("chase", "ing", "chasing"),
        ("see", "ing", "seeing"),
        ("run", "ing", "running"),
        ("try", "ing", "trying"),
        ("show", "ing", "showing"),
    ],
)
def test_add_ending_follows_the_spelling_rules(base: str, ending: str, expected: str) -> None:
    assert add_ending(base, ending) == expected


def test_an_ending_form_keeps_its_base_words_category_and_tags() -> None:
    words = by_word()
    assert words["jumped"].pattern_codes == {"final_blend_mp"}
    assert words["chasing"].pattern_codes == {"digraph_ch", "silent_e_a"}
    assert words["looked"].is_sight_word and not words["looked"].pattern_codes
    assert not words["dogs"].is_sight_word and not words["dogs"].pattern_codes


def test_irregular_verbs_get_no_ed_form() -> None:
    words = by_word()
    assert "running" in words and "makes" in words
    assert "runned" not in words and "maked" not in words


def test_an_already_seeded_form_keeps_its_own_row() -> None:
    # "does" and "goes" are Dolch sight words; "do" and "go" would generate them too.
    words = by_word()
    assert words["does"].is_sight_word
    assert words["goes"].is_sight_word


def test_build_words_rejects_an_ending_base_that_is_not_seeded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(seed_data, "PLURAL_NOUNS", ("dinosaur",))
    with pytest.raises(ValueError, match="ending base 'dinosaur'"):
        build_words()
