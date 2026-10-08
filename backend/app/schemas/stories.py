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
