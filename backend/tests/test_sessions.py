from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes import sessions as sessions_route
from app.db.session import get_db
from app.main import app
from app.models import ReadingSession, Story, StoryLine
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


def _post_start_session(db: Mock, child_id, story_id):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        return TestClient(app).post(
            "/sessions", json={"child_id": str(child_id), "story_id": str(story_id)}
        )
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_start_session_creates_in_progress_session() -> None:
    child_id = uuid4()
    story_id = uuid4()
    session_id = uuid4()
    db = Mock()
    db.get.return_value = Story(id=story_id, child_id=child_id, title="A ship", status="approved")
    db.add.side_effect = lambda row: setattr(row, "id", session_id)

    response = _post_start_session(db, child_id, story_id)

    assert response.status_code == 201
    assert response.json() == {"id": str(session_id)}
    db.commit.assert_called_once()


def test_start_session_rejects_story_of_another_child() -> None:
    story_id = uuid4()
    db = Mock()
    db.get.return_value = Story(id=story_id, child_id=uuid4(), title="A ship", status="approved")

    response = _post_start_session(db, uuid4(), story_id)

    assert response.status_code == 404
    db.add.assert_not_called()


def test_start_session_returns_404_for_missing_story() -> None:
    db = Mock()
    db.get.return_value = None

    response = _post_start_session(db, uuid4(), uuid4())

    assert response.status_code == 404
