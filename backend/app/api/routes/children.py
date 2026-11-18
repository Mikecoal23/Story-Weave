import hmac
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.api.auth import get_current_caregiver
from app.core.pins import decrypt_pin, encrypt_pin
from app.db.session import get_db
from app.models import Caregiver, Child, ReadingSession
from app.schemas.children import (
    ChildPinResponse,
    ChildResponse,
    CreateChildRequest,
    PinRequest,
    PinVerificationResponse,
)

router = APIRouter()


@router.post("/children", response_model=ChildResponse, status_code=201)
def create_child(
    body: CreateChildRequest,
    db: Session = Depends(get_db),
    current: Caregiver = Depends(get_current_caregiver),
) -> Child:
    if current.id != body.caregiver_id:
        raise HTTPException(status_code=403, detail="Cannot create a child for another caregiver")
    child = Child(
        caregiver_id=body.caregiver_id,
        display_name=body.display_name,
        grade_level=body.grade_level,
        interests=body.interests,
        pin_ciphertext=encrypt_pin(body.pin),
    )
    db.add(child)
    db.commit()
    return child


@router.delete("/children/{child_id}", status_code=204)
def delete_child(
    child_id: UUID,
    db: Session = Depends(get_db),
    current: Caregiver = Depends(get_current_caregiver),
) -> None:
    child = db.get(Child, child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Child not found")
    if child.caregiver_id != current.id:
        raise HTTPException(status_code=403, detail="Cannot remove another caregiver's child")
    # Sessions go first: reading_session.story_id is RESTRICT, so a story can't be deleted
    # while a session still points at it. The database's CASCADE rules remove the rest
    # (word attempts, stories and their lines, mastery, articulation flags).
    db.execute(delete(ReadingSession).where(ReadingSession.child_id == child_id))
    db.delete(child)
    db.commit()


@router.post("/children/{child_id}/verify-pin", response_model=PinVerificationResponse)
def verify_child_pin(
    child_id: UUID,
    body: PinRequest,
    db: Session = Depends(get_db),
    current: Caregiver = Depends(get_current_caregiver),
) -> PinVerificationResponse:
    child = db.get(Child, child_id)
    if child is None or child.caregiver_id != current.id:
        raise HTTPException(status_code=404, detail="Child not found")
    if child.pin_ciphertext is None:
        raise HTTPException(status_code=409, detail="Child PIN has not been set")
    return PinVerificationResponse(
        verified=hmac.compare_digest(body.pin, decrypt_pin(child.pin_ciphertext))
    )


@router.get("/children/{child_id}/pin", response_model=ChildPinResponse)
def get_child_pin(
    child_id: UUID,
    db: Session = Depends(get_db),
    current: Caregiver = Depends(get_current_caregiver),
) -> ChildPinResponse:
    child = db.get(Child, child_id)
    if child is None or child.caregiver_id != current.id:
        raise HTTPException(status_code=404, detail="Child not found")
    if child.pin_ciphertext is None:
        raise HTTPException(status_code=409, detail="Child PIN has not been set")
    return ChildPinResponse(pin=decrypt_pin(child.pin_ciphertext))


@router.put("/children/{child_id}/pin", status_code=204)
def set_child_pin(
    child_id: UUID,
    body: PinRequest,
    db: Session = Depends(get_db),
    current: Caregiver = Depends(get_current_caregiver),
) -> None:
    child = db.get(Child, child_id)
    if child is None or child.caregiver_id != current.id:
        raise HTTPException(status_code=404, detail="Child not found")
    child.pin_ciphertext = encrypt_pin(body.pin)
    db.commit()
