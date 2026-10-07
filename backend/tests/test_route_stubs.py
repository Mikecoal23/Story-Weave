from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.sessions import LineAudioResponse

client = TestClient(app)

# The team's planned REST contract (planning.md, Stage 1), as (method, path) pairs.
PLANNED_ROUTES = [
    ("POST", "/caregivers"),
    ("POST", "/caregivers/{caregiver_id}/session"),
    ("POST", "/children"),
    ("POST", "/sessions"),
    ("POST", "/sessions/{session_id}/lines/{line_number}/audio"),
    ("GET", "/stories/{story_id}"),
    ("POST", "/stories/generate"),
    ("GET", "/caregivers/{child_id}/dashboard"),
]


def test_all_planned_routes_are_in_openapi_schema() -> None:
    # Checked against the OpenAPI schema, not app.routes: included routers are
    # wrapped, so app.routes doesn't list them flat. The schema is what teammates read.
    paths = app.openapi()["paths"]

    for method, path in PLANNED_ROUTES:
        assert method.lower() in paths.get(path, {}), f"missing {method} {path}"


def test_stub_routes_return_501() -> None:
    session_id = uuid4()
    requests = [
        ("post", "/caregivers", {}),
        ("post", f"/caregivers/{uuid4()}/session", {}),
        ("post", "/children", {}),
        ("post", "/sessions", {}),
        (
            "post",
            f"/sessions/{session_id}/lines/1/audio",
            {"files": {"audio": ("line.webm", b"x", "audio/webm")}},
        ),
        ("get", f"/stories/{uuid4()}", {}),
        ("post", "/stories/generate", {}),
        ("get", f"/caregivers/{uuid4()}/dashboard", {}),
    ]

    for method, path, kwargs in requests:
        response = getattr(client, method)(path, **kwargs)
        assert response.status_code == 501, (
            f"{method.upper()} {path} returned {response.status_code}"
        )


def test_line_audio_response_always_includes_status() -> None:
    response = LineAudioResponse(status="complete", result={"words": []})

    assert response.model_dump() == {"status": "complete", "result": {"words": []}}


def test_line_audio_response_rejects_unknown_status() -> None:
    with pytest.raises(ValueError):
        LineAudioResponse(status="pending")  # type: ignore[arg-type]
