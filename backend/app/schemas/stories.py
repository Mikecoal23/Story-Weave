from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DraftStory(BaseModel):
    """A story before it is validated: what `generate_story_draft(...)` hands back.

    `pattern_codes` are the `phonics_pattern.code` values the story is meant to practice.
    The validator, the pipeline and `save_validated_story` treat an LLM draft and a
    fallback template identically, because a template is a `DraftStory` too.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    theme: str
    pattern_codes: tuple[str, ...]
    lines: tuple[str, ...]
    # One name from story_generation.CHARACTERS; the frontend shows its picture. Not stored.
    character: str = "default"


class FallbackStoryTemplate(DraftStory):
    """A pre-authored story (app/services/story_templates.py) that the pipeline serves
    when no LLM draft passes validation. Its `pattern_codes` are not checked against the
    DB here, so the fallback path works even if a lookup fails.
    """


class StoryResponse(BaseModel):
    """Response from GET /stories/{story_id}; the shape the frontend's `Story` type expects."""

    id: UUID
    title: str
    theme: str | None
    lines: list[str]


class GenerateStoryRequest(BaseModel):
    child_id: UUID


class GenerateStoryResponse(StoryResponse):
    """Response from POST /stories/generate: the saved story plus how it was produced.

    `source` is "fallback" when no LLM draft passed validation (it is also stored on the
    story row); `attempts` is how many LLM drafts were requested (returned here only).
    """

    source: Literal["llm", "fallback"]
    attempts: int
    character: str


class ValidatedStory(DraftStory):
    """A story that passed the controlled-vocabulary validator, ready to persist.

    `source` records whether the LLM wrote it or a pre-authored fallback template
    was used, so the app can flag fallback stories later. `attempts` is how many LLM
    drafts were requested before this story was settled on (== the attempt limit when
    the fallback fired).
    """

    source: Literal["llm", "fallback"]
    attempts: int
