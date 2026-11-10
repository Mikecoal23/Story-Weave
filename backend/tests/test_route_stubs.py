import pytest

from app.main import app
from app.schemas.scoring import ScoreResult, WordScore
from app.schemas.sessions import LineAudioResponse

# The team's planned REST contract (planning.md, Stage 1), as (method, path) pairs.
PLANNED_ROUTES = [
    ("POST", "/caregivers"),
    ("POST", "/caregivers/session"),
    ("POST", "/children"),
    ("GET", "/caregivers/{caregiver_id}/children"),
    ("POST", "/sessions"),
    ("POST", "/sessions/{session_id}/lines/{line_number}/audio"),
    ("GET", "/stories/{story_id}"),
    ("POST", "/stories/generate"),
    ("GET", "/children/{child_id}/dashboard"),
]


def test_all_planned_routes_are_in_openapi_schema() -> None:
    # Checked against the OpenAPI schema, not app.routes: included routers are
    # wrapped, so app.routes doesn't list them flat. The schema is what teammates read.
    paths = app.openapi()["paths"]

    for method, path in PLANNED_ROUTES:
        assert method.lower() in paths.get(path, {}), f"missing {method} {path}"


def test_line_audio_response_always_includes_status() -> None:
    result = ScoreResult(
        words=[
            WordScore(
                expected_word="read",
                recognized_word="read",
                status="mastered",
            )
        ]
    )
    response = LineAudioResponse(status="complete", result=result)

    assert response.model_dump() == {
        "status": "complete",
        "result": {
            "words": [
                {
                    "expected_word": "read",
                    "recognized_word": "read",
                    "status": "mastered",
                    "error_classification": None,
                }
            ]
        },
    }


def test_line_audio_response_rejects_unknown_status() -> None:
    with pytest.raises(ValueError):
        LineAudioResponse(status="pending")  # type: ignore[arg-type]
