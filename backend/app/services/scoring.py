from uuid import UUID

from sqlalchemy.orm import Session

from app.schemas.scoring import ScoreResult


def score_line_audio(audio_bytes: bytes, expected_line: str) -> ScoreResult:
    """Score one line of audio against its expected text."""
    raise NotImplementedError("score_line_audio is a Stage 2 task")


def process_line_score(
    session: Session,
    reading_session_id: UUID,
    story_line_id: UUID,
    score_result: ScoreResult,
) -> None:
    """Persist a line's score and update the child's phonics mastery."""
    raise NotImplementedError("process_line_score is a Stage 2 task")
