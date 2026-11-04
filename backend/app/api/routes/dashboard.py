from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Child
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import build_dashboard

router = APIRouter()


# Child-rooted, since it returns one child's data (renamed from /caregivers/{child_id}/dashboard
# on 2026-11-01, Open Question 11; see the Decisions Log).
@router.get("/children/{child_id}/dashboard", response_model=DashboardResponse)
def get_child_dashboard(child_id: UUID, db: Session = Depends(get_db)) -> DashboardResponse:
    if db.get(Child, child_id) is None:
        raise HTTPException(status_code=404, detail="Child not found")
    return build_dashboard(db, child_id)
