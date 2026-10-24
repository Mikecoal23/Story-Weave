from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Child, PhonicsPattern, Story, StoryLine
from app.schemas.stories import GenerateStoryRequest, GenerateStoryResponse, StoryResponse
from app.services.difficulty import select_difficulty_target
from app.services.story_pipeline import NoValidStoryError, generate_validated_story
from app.services.story_store import save_validated_story
from app.services.vocabulary_validator import load_allowed_vocabulary

router = APIRouter()


@router.get("/stories/{story_id}", response_model=StoryResponse)
def get_story(story_id: UUID, db: Session = Depends(get_db)) -> StoryResponse:
    story = db.get(Story, story_id)
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")
    lines = db.scalars(
        select(StoryLine.text).where(StoryLine.story_id == story_id).order_by(StoryLine.line_number)
    ).all()
    return StoryResponse(id=story.id, title=story.title, theme=story.theme, lines=list(lines))


@router.post("/stories/generate", response_model=GenerateStoryResponse, status_code=201)
def generate_story(
    body: GenerateStoryRequest, db: Session = Depends(get_db)
) -> GenerateStoryResponse:
    child = db.get(Child, body.child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Child not found")

    target = select_difficulty_target(db, child.id)
    pattern_ids = [*target.reinforce_pattern_ids, *target.stretch_pattern_ids]
    patterns = db.scalars(
        select(PhonicsPattern)
        .where(PhonicsPattern.phonics_pattern_id.in_(pattern_ids))
        .order_by(PhonicsPattern.sequence_order)
    ).all()
    allowed = load_allowed_vocabulary(db)

    try:
        validated = generate_validated_story(patterns, tuple(child.interests), allowed)
    except NoValidStoryError as error:
        raise HTTPException(status_code=503, detail="No valid story could be produced") from error

    story = save_validated_story(db, child.id, validated)
    db.commit()
    return GenerateStoryResponse(
        id=story.id,
        title=story.title,
        theme=story.theme,
        lines=list(validated.lines),
        source=validated.source,
        attempts=validated.attempts,
    )
