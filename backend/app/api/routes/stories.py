from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Story, StoryLine
from app.schemas.stories import StoryResponse

router = APIRouter()


@router.get("/stories/{story_id}", response_model=StoryResponse)
def get_story(story_id: UUID, db: Session = Depends(get_db)) -> StoryResponse:
    story = db.get(Story, story_id)
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")
    lines = db.scalars(
        select(StoryLine.text)
        .where(StoryLine.story_id == story_id)
        .order_by(StoryLine.line_number)
    ).all()
    return StoryResponse(id=story.id, title=story.title, theme=story.theme, lines=list(lines))


@router.post("/stories/generate")
def generate_story() -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet (Stage 2)")
