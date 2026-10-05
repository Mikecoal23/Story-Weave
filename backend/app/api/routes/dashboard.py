from uuid import UUID

from fastapi import APIRouter, HTTPException

router = APIRouter()


# Path is singular (/caregiver/...), not /caregivers, to match what the team already
# wrote in planning.md. Possibly a typo, but kept for consistency; see the Decisions Log.
@router.get("/caregiver/{child_id}/dashboard")
def get_caregiver_dashboard(child_id: UUID) -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet (Stage 2)")
