from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Caregiver, Child, ReadingSession
from app.schemas.children import ChildResponse, CreateChildRequest

router = APIRouter()


@router.post("/children", response_model=ChildResponse, status_code=201)
def create_child(body: CreateChildRequest, db: Session = Depends(get_db)) -> Child:
    if db.get(Caregiver, body.caregiver_id) is None:
        raise HTTPException(status_code=404, detail="Caregiver not found")
    child = Child(
        caregiver_id=body.caregiver_id,
        display_name=body.display_name,
        grade_level=body.grade_level,
        interests=body.interests,
    )
    db.add(child)
    db.commit()
    return child


@router.delete("/children/{child_id}", status_code=204)
def delete_child(child_id: UUID, db: Session = Depends(get_db)) -> None:
    child = db.get(Child, child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Child not found")
    # Sessions go first: reading_session.story_id is RESTRICT, so a story can't be deleted
    # while a session still points at it. The database's CASCADE rules remove the rest
    # (word attempts, stories and their lines, mastery, articulation flags).
    db.execute(delete(ReadingSession).where(ReadingSession.child_id == child_id))
    db.delete(child)
    db.commit()
