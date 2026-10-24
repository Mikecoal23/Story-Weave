from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models import Story


def _get_story(db: Mock, story_id):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        return TestClient(app).get(f"/stories/{story_id}")
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_story_returns_title_theme_and_ordered_lines() -> None:
    story_id = uuid4()
    db = Mock()
    db.get.return_value = Story(
        id=story_id, child_id=uuid4(), title="The Big Dog", theme="dogs", status="approved"
    )
    db.scalars.return_value.all.return_value = ["The big dog ran.", "It is fun."]

    response = _get_story(db, story_id)

    assert response.status_code == 200
    assert response.json() == {
        "id": str(story_id),
        "title": "The Big Dog",
        "theme": "dogs",
        "lines": ["The big dog ran.", "It is fun."],
    }


def test_get_story_returns_404_for_missing_story() -> None:
    db = Mock()
    db.get.return_value = None

    response = _get_story(db, uuid4())

    assert response.status_code == 404
