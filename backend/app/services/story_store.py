from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PhonicsPattern, Story, StoryLine, StoryPattern
from app.schemas.stories import ValidatedStory


def save_validated_story(
    db: Session, child_id: UUID, story: ValidatedStory, story_id: UUID | None = None
) -> Story:
    """Write a validated story and its lines and pattern links. Flushes, never commits.

    Status is 'validated' for LLM and fallback stories alike. The pattern links come from
    the story's own `pattern_codes` (the targets for an LLM draft, the template's codes for
    a fallback), so a fallback is linked to what it actually practices. `story_id` is only
    for the dev fixtures script, which needs a fixed id; leave it out otherwise.
    """
    row = Story(child_id=child_id, title=story.title, theme=story.theme, status="validated")
    if story_id is not None:
        row.id = story_id
    db.add(row)
    db.flush()
    db.add_all(
        StoryLine(story_id=row.id, line_number=number, text=text)
        for number, text in enumerate(story.lines, start=1)
    )
    pattern_ids = db.scalars(
        select(PhonicsPattern.phonics_pattern_id).where(
            PhonicsPattern.code.in_(story.pattern_codes)
        )
    )
    db.add_all(
        StoryPattern(story_id=row.id, phonics_pattern_id=pattern_id) for pattern_id in pattern_ids
    )
    db.flush()
    return row
