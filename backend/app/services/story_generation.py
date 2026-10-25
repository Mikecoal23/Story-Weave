import json
from collections.abc import Sequence

import anthropic

from app.core.config import settings
from app.models.entities import PhonicsPattern
from app.schemas.stories import DraftStory

# A live call takes about 2 s (measured 2026-10-23). The SDK default is a 600 s read timeout
# plus 2 hidden retries; the pipeline already retries, so the SDK must not.
_REQUEST_TIMEOUT_SECONDS = 15.0


class LLMNotConfiguredError(RuntimeError):
    """ANTHROPIC_API_KEY is not set, so no draft can be requested."""


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
    feedback: str | None = None,
) -> str:
    pattern_lines = "\n".join(
        f"- {pattern.code} ({pattern.label}): e.g. {', '.join(pattern.example_words)}"
        for pattern in patterns
    )
    interests_line = ", ".join(interests) if interests else "no particular theme"
    vocab_line = ", ".join(sorted(vocab_constraints))
    prompt = (
        f"Target phonics patterns:\n{pattern_lines}\n\n"
        f"Child's interests: {interests_line}\n\n"
        f"Allowed vocabulary (use only these words): {vocab_line}"
    )
    if feedback:
        prompt += f"\n\nYour previous attempt was rejected. {feedback}"
    return prompt


def _extract_json_object(raw_text: str) -> str:
    """The JSON object inside a model reply.

    Haiku wraps its JSON in a ```json fence despite the prompt, so take everything from the
    first `{` to the last `}`. A reply with no braces is passed through unchanged and fails
    in `json.loads`, which the pipeline counts as a bad reply.
    """
    start, end = raw_text.find("{"), raw_text.rfind("}")
    if start == -1 or end < start:
        return raw_text
    return raw_text[start : end + 1]


def generate_story_draft(
    patterns: Sequence[PhonicsPattern],
    interests: tuple[str, ...],
    vocab_constraints: frozenset[str],
    feedback: str | None = None,
) -> DraftStory:
    """Ask the LLM for one story draft. Not validated against the vocabulary --
    that's the validator's job (see story_pipeline). `feedback` is why the previous
    draft was rejected, appended to the prompt on a retry."""
    if not settings.anthropic_api_key:
        # Without this the SDK raises a bare TypeError, which looks like a bad reply.
        raise LLMNotConfiguredError("ANTHROPIC_API_KEY is not set in backend/.env")
    client = anthropic.Anthropic(
        api_key=settings.anthropic_api_key,
        timeout=_REQUEST_TIMEOUT_SECONDS,
        max_retries=0,
    )
    message = client.messages.create(
        model=settings.anthropic_story_model,
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": _build_user_prompt(patterns, interests, vocab_constraints, feedback),
            }
        ],
    )
    raw_text = message.content[0].text
    data = json.loads(_extract_json_object(raw_text))
    return DraftStory(
        title=data["title"],
        theme=data["theme"],
        pattern_codes=tuple(pattern.code for pattern in patterns),
        lines=tuple(data["lines"]),
    )
