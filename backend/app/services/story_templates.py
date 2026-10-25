from app.schemas.stories import FallbackStoryTemplate

# Pre-authored stories the pipeline serves when no LLM draft passes validation
# (app.services.story_pipeline). Every word must be in the seeded vocabulary:
# tests/test_seed_data.py checks them against the seed data and
# tests/test_vocabulary_validator_db.py runs the real validator on the seeded tables.
# `pattern_codes` are what each story practices; the pipeline picks the template sharing
# the most codes with the child's target patterns.
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
