from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Caregiver, Child
from app.schemas.children import ChildResponse

router = APIRouter()

# Route stubs for the team's REST contract (planning.md, Stage 1). Every route returns
# 501 until its Stage 2 implementation lands. Request/response bodies are NOT specified
# yet except where planning.md says so, so they are deliberately left off these stubs.


@router.post("/caregivers")
def create_caregiver() -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet (Stage 2)")


@router.post("/caregivers/{caregiver_id}/session")
def mint_caregiver_session(caregiver_id: UUID) -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet (Stage 2)")


@router.get("/caregivers/{caregiver_id}/children", response_model=list[ChildResponse])
def list_children(caregiver_id: UUID, db: Session = Depends(get_db)) -> list[Child]:
    if db.get(Caregiver, caregiver_id) is None:
        raise HTTPException(status_code=404, detail="Caregiver not found")
    return list(
        db.scalars(
            select(Child).where(Child.caregiver_id == caregiver_id).order_by(Child.created_at)
        )
    )
