from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DraftStory(BaseModel):
    """What `generate_story_draft(...)` hands back, before validation.

    Same shape as `FallbackStoryTemplate` on purpose: the controlled-vocabulary
    validator and the eventual `Story`/`StoryLine` persistence both consume
    either one identically, so the regenerate/fallback paths don't need to
    branch on which kind of story they're holding.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    theme: str
    pattern_codes: tuple[str, ...]
    lines: tuple[str, ...]


class FallbackStoryTemplate(BaseModel):
    """A pre-authored, guaranteed-valid story used when the LLM + validator
    loop in `generate_story_draft(...)` rejects N drafts in a row.

    `pattern_codes` are `phonics_pattern.code` values the story is meant to
    reinforce — not validated against the DB here, since the fallback path
    must work even if a lookup fails.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    theme: str
    pattern_codes: tuple[str, ...]
    lines: tuple[str, ...]


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

    `source` is "fallback" when no LLM draft passed validation (Open Question 16: returned
    here only, not stored); `attempts` is how many LLM drafts were requested.
    """

    source: Literal["llm", "fallback"]
    attempts: int


class ValidatedStory(DraftStory):
    """A story that passed the controlled-vocabulary validator, ready to persist.

    `source` records whether the LLM wrote it or a pre-authored fallback template
    was used, so the app can flag fallback stories later. `attempts` is how many LLM
    drafts were requested before this story was settled on (== the attempt limit when
    the fallback fired).
    """

    source: Literal["llm", "fallback"]
    attempts: int
