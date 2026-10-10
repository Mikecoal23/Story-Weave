from uuid import UUID

from fastapi import APIRouter, HTTPException

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
