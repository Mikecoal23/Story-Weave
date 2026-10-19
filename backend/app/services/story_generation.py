import json
from collections.abc import Sequence

import anthropic

from app.core.config import settings
from app.models.entities import PhonicsPattern
from app.schemas.stories import DraftStory

_SYSTEM_PROMPT = """You write short decodable stories for children in grades 1-3 learning to read.

Rules:
- Use ONLY words from the allowed vocabulary list. Never use a word that is not in that list.
- The story must be 6-8 lines, one short sentence per line.
- Work in as many of the target phonics patterns as you naturally can.
- Respond with ONLY a JSON object, no other text, shaped exactly like:
  {"title": "...", "theme": "...", "lines": ["...", "...", ...]}
"""


def _build_user_prompt(
    patterns: Sequence[PhonicsPattern],
    interests: tuple[str, ...],
    vocab_constraints: frozenset[str],
) -> str:
    pattern_lines = "\n".join(
        f"- {pattern.code} ({pattern.label}): e.g. {', '.join(pattern.example_words)}"
        for pattern in patterns
    )
    interests_line = ", ".join(interests) if interests else "no particular theme"
    vocab_line = ", ".join(sorted(vocab_constraints))
    return (
        f"Target phonics patterns:\n{pattern_lines}\n\n"
        f"Child's interests: {interests_line}\n\n"
        f"Allowed vocabulary (use only these words): {vocab_line}"
    )


def generate_story_draft(
    patterns: Sequence[PhonicsPattern],
    interests: tuple[str, ...],
    vocab_constraints: frozenset[str],
) -> DraftStory:
    """Ask the LLM for one story draft. Not validated against the vocabulary yet --
    that's the controlled-vocabulary validator's job, not this function's."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=settings.anthropic_story_model,
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": _build_user_prompt(patterns, interests, vocab_constraints),
            }
        ],
    )
    raw_text = message.content[0].text
    data = json.loads(raw_text)
    return DraftStory(
        title=data["title"],
        theme=data["theme"],
        pattern_codes=tuple(pattern.code for pattern in patterns),
        lines=tuple(data["lines"]),
    )
