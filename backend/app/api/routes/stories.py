from uuid import UUID

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/stories/{story_id}")
def get_story(story_id: UUID) -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet (Stage 2)")


@router.post("/stories/generate")
def generate_story() -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet (Stage 2)")
