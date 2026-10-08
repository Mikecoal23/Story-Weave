from app.services.story_templates import (
    ALLOWED_DRAFT_WORDS,
    FALLBACK_TEMPLATES,
    words_in,
)


def test_there_are_two_to_three_templates() -> None:
    assert 2 <= len(FALLBACK_TEMPLATES) <= 3


def test_templates_are_six_to_eight_lines() -> None:
    for template in FALLBACK_TEMPLATES:
        assert 6 <= len(template.lines) <= 8, template.title


def test_templates_have_a_title_theme_and_at_least_one_pattern() -> None:
    for template in FALLBACK_TEMPLATES:
        assert template.title
        assert template.theme
        assert len(template.pattern_codes) >= 1


def test_templates_only_use_the_documented_draft_vocabulary() -> None:
    # Guards against vocabulary drift while these are hand-authored and
    # unseeded (see module docstring in app.services.story_templates).
    for template in FALLBACK_TEMPLATES:
        used = set()
        for line in template.lines:
            used |= words_in(line)
        unexpected = used - ALLOWED_DRAFT_WORDS
        assert not unexpected, f"{template.title} uses undocumented words: {unexpected}"
