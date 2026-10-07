from uuid import UUID

from fastapi import APIRouter, HTTPException

router = APIRouter()


# Plural, to match every other caregiver-rooted route. The planning.md draft had this
# singular (/caregiver/...); renamed after team review. See the Decisions Log.
@router.get("/caregivers/{child_id}/dashboard")
def get_caregiver_dashboard(child_id: UUID) -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet (Stage 2)")
