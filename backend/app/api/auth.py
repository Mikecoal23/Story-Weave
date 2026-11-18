import hashlib
from datetime import UTC, datetime

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Caregiver, CaregiverSession


def get_current_caregiver(
    authorization: str | None = Header(default=None), db: Session = Depends(get_db)
) -> Caregiver:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Caregiver session required")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Caregiver session required")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = db.scalar(
        select(CaregiverSession).where(
            CaregiverSession.token_hash == token_hash,
            CaregiverSession.expires_at > datetime.now(UTC),
        )
    )
    if session is None:
        raise HTTPException(status_code=401, detail="Caregiver session expired or invalid")
    caregiver = db.get(Caregiver, session.caregiver_id)
    if caregiver is None:
        raise HTTPException(status_code=401, detail="Caregiver session expired or invalid")
    return caregiver
