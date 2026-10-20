from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import ReadingSession, StoryLine
from app.schemas.sessions import LineAudioResponse
from app.services.scoring import process_line_score, score_line_audio

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
    line_number: int = Path(ge=1),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> LineAudioResponse:
    reading_session = db.get(ReadingSession, session_id)
    if reading_session is None:
        raise HTTPException(status_code=404, detail="Reading session not found")
    if reading_session.status != "in_progress":
        raise HTTPException(status_code=409, detail="Reading session is not in progress")

    story_line = db.scalar(
        select(StoryLine).where(
            StoryLine.story_id == reading_session.story_id,
            StoryLine.line_number == line_number,
        )
    )
    if story_line is None:
        raise HTTPException(status_code=404, detail="Story line not found")

    try:
        score_result = score_line_audio(audio.file.read(), story_line.text)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except TimeoutError as error:
        raise HTTPException(status_code=504, detail="Audio assessment timed out") from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail="Azure Speech assessment failed") from error

    process_line_score(db, session_id, story_line.id, score_result)
    db.commit()
    return LineAudioResponse(status="complete", result=score_result)
