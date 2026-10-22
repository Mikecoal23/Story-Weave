import logging
from collections.abc import Sequence

import anthropic

from app.core.config import settings
from app.models.entities import PhonicsPattern
from app.schemas.stories import DraftStory, FallbackStoryTemplate, ValidatedStory
from app.services.story_generation import generate_story_draft
from app.services.story_templates import FALLBACK_TEMPLATES
from app.services.vocabulary_validator import validate_story

logger = logging.getLogger(__name__)

# A malformed or incomplete LLM reply (bad JSON, missing keys, wrong types).
_BAD_REPLY_ERRORS = (ValueError, KeyError, IndexError, TypeError)

_BAD_REPLY_FEEDBACK = (
    "Your reply could not be parsed. Respond with ONLY the JSON object "
    '{"title": "...", "theme": "...", "lines": ["...", ...]} and nothing else.'
)


class NoValidStoryError(RuntimeError):
    """The LLM loop was exhausted and no fallback template passed validation either.

    Only reachable if the seeded vocabulary drifts away from every template (the DB
    test in test_vocabulary_validator_db.py guards against that).
    """


def _unknown_words_feedback(unknown_words: tuple[str, ...]) -> str:
    return (
        f"It used words that are not in the allowed vocabulary: {', '.join(unknown_words)}. "
        "Rewrite the whole story using ONLY words from the allowed vocabulary list."
    )


def rank_fallback_templates(pattern_codes: Sequence[str]) -> list[FallbackStoryTemplate]:
    """Fallback templates ordered by how many target pattern codes they share, most first.

    Ties keep authoring order (sorted() is stable), so the result is deterministic.
    """
    wanted = set(pattern_codes)
    return sorted(
        FALLBACK_TEMPLATES,
        key=lambda template: len(wanted & set(template.pattern_codes)),
        reverse=True,
    )


def generate_validated_story(
    patterns: Sequence[PhonicsPattern],
    interests: tuple[str, ...],
    allowed: frozenset[str],
    max_attempts: int | None = None,
) -> ValidatedStory:
    """Return a story whose every word is in `allowed`; a session never dead-ends.

    Asks the LLM for up to `max_attempts` drafts (default `settings.story_max_attempts`),
    feeding the rejected words back each time. A draft that fails validation, a reply
    that can't be parsed, and an Anthropic API error each use up one attempt. After the
    last rejection, the best-matching fallback template that validates is returned.
    """
    attempts = max_attempts if max_attempts is not None else settings.story_max_attempts
    feedback: str | None = None

    for attempt in range(1, attempts + 1):
        draft: DraftStory | None = None
        try:
            draft = generate_story_draft(patterns, interests, allowed, feedback)
        except anthropic.APIError:
            logger.warning("story attempt %d/%d: Anthropic API error", attempt, attempts)
        except _BAD_REPLY_ERRORS:
            logger.warning("story attempt %d/%d: unparseable LLM reply", attempt, attempts)
            feedback = _BAD_REPLY_FEEDBACK

        if draft is None:
            continue
        result = validate_story(draft, allowed)
        if result.is_valid:
            return ValidatedStory(**draft.model_dump(), source="llm", attempts=attempt)
        logger.warning(
            "story attempt %d/%d rejected, unknown words: %s",
            attempt,
            attempts,
            ", ".join(result.unknown_words),
        )
        feedback = _unknown_words_feedback(result.unknown_words)

    for template in rank_fallback_templates([pattern.code for pattern in patterns]):
        if validate_story(template, allowed).is_valid:
            logger.warning(
                "story fell back to template %r after %d attempts", template.title, attempts
            )
            return ValidatedStory(**template.model_dump(), source="fallback", attempts=attempts)
    raise NoValidStoryError("no LLM draft or fallback template passed vocabulary validation")
