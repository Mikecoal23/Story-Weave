from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.sessions import LineAudioResponse

router = APIRouter()


@router.post("/sessions")
def start_session() -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet (Stage 2)")


@router.post(
    "/sessions/{session_id}/lines/{line_number}/audio",
    response_model=LineAudioResponse,
)
def upload_line_audio(
    session_id: UUID,
    line_number: int,
    audio: UploadFile = File(...),
) -> LineAudioResponse:
    raise HTTPException(status_code=501, detail="Not implemented yet (Stage 2)")
