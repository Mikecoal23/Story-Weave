from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Caregiver, Child
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
