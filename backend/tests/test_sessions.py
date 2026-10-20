from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes import sessions as sessions_route
from app.db.session import get_db
from app.main import app
from app.models import ReadingSession, StoryLine
from app.schemas.scoring import ScoreResult, WordScore


def test_audio_route_scores_persists_and_returns_completed_result(monkeypatch) -> None:
    session_id = uuid4()
    story_id = uuid4()
    line_id = uuid4()
    reading_session = ReadingSession(
        id=session_id,
        child_id=uuid4(),
        story_id=story_id,
        status="in_progress",
    )
    story_line = StoryLine(id=line_id, story_id=story_id, line_number=1, text="A ship.")
    db = Mock()
    db.get.return_value = reading_session
    db.scalar.return_value = story_line
    score = ScoreResult(
        words=[WordScore(expected_word="ship", recognized_word="ship", status="mastered")]
    )
    score_audio = Mock(return_value=score)
    persist_score = Mock()
    monkeypatch.setattr(sessions_route, "score_line_audio", score_audio)
    monkeypatch.setattr(sessions_route, "process_line_score", persist_score)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        response = TestClient(app).post(
            f"/sessions/{session_id}/lines/1/audio",
            files={"audio": ("line.webm", b"audio", "audio/webm")},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json() == {
        "status": "complete",
        "result": {
            "words": [
                {
                    "expected_word": "ship",
                    "recognized_word": "ship",
                    "status": "mastered",
                }
            ]
        },
    }
    score_audio.assert_called_once_with(b"audio", story_line.text)
    persist_score.assert_called_once_with(db, session_id, line_id, score)
    db.commit.assert_called_once_with()
