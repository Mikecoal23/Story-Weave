from pydantic import BaseModel, ConfigDict


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
