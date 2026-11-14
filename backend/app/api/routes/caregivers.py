import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Caregiver, CaregiverSession, Child
from app.schemas.caregivers import CaregiverSessionResponse, CreateCaregiverRequest, LoginRequest
from app.schemas.children import ChildResponse

router = APIRouter()

# Login model (planning.md, Open Question 12, 2026-11-04): email lookup with no password.
# Stored but not checked anywhere yet (planning.md, 2026-09-30).
SESSION_LIFETIME = timedelta(days=30)


def _normalize(email: str) -> str:
    return email.strip().lower()


def _mint_session(db: Session, caregiver: Caregiver) -> CaregiverSessionResponse:
    # The raw token goes to the client once; the database keeps only its SHA-256 hash
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + SESSION_LIFETIME
    db.add(
        CaregiverSession(
            caregiver_id=caregiver.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=expires_at,
        )
    )
    db.commit()
    return CaregiverSessionResponse(
        caregiver_id=caregiver.id,
        display_name=caregiver.display_name,
        token=token,
        expires_at=expires_at,
    )


@router.post("/caregivers", response_model=CaregiverSessionResponse, status_code=201)
def create_caregiver(
    body: CreateCaregiverRequest, db: Session = Depends(get_db)
) -> CaregiverSessionResponse:
    email = _normalize(body.email)
    if db.scalar(select(Caregiver).where(Caregiver.email == email)) is not None:
        raise HTTPException(status_code=409, detail="Email already in use")
    caregiver = Caregiver(display_name=body.display_name, email=email)
    db.add(caregiver)
    try:
        db.flush()  # assigns caregiver.id, needed by the session row
    except IntegrityError:
        # Two sign-ups with one email at the same moment: both pass the check above,
        # and the database's unique constraint stops the second one here.
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already in use") from None
    return _mint_session(db, caregiver)


@router.post("/caregivers/session", response_model=CaregiverSessionResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> CaregiverSessionResponse:
    caregiver = db.scalar(select(Caregiver).where(Caregiver.email == _normalize(body.email)))
    if caregiver is None:
        raise HTTPException(status_code=404, detail="No caregiver with that email")
    return _mint_session(db, caregiver)


@router.get("/caregivers/{caregiver_id}/children", response_model=list[ChildResponse])
def list_children(caregiver_id: UUID, db: Session = Depends(get_db)) -> list[Child]:
    if db.get(Caregiver, caregiver_id) is None:
        raise HTTPException(status_code=404, detail="Caregiver not found")
    return list(
        db.scalars(
            select(Child).where(Child.caregiver_id == caregiver_id).order_by(Child.created_at)
        )
    )
