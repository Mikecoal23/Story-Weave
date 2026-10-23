from app.services.story_templates import FALLBACK_TEMPLATES


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
