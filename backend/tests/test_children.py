from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from support import throwaway_schema

from app.db.session import get_db
from app.main import app
from app.models import (
    Caregiver,
    Child,
    PhonicsPattern,
    ReadingAttempt,
    ReadingSession,
    Story,
    StoryLine,
    StoryPattern,
    VocabularyWord,
)


def _call(db: Mock, method: str, path: str, **kwargs):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        return getattr(TestClient(app), method)(path, **kwargs)
    finally:
        app.dependency_overrides.pop(get_db, None)


def _create_body(caregiver_id, **overrides) -> dict:
    body = {
        "caregiver_id": str(caregiver_id),
        "display_name": "Mia",
        "grade_level": 1,
        "interests": ["dinosaurs"],
    }
    return body | overrides


def test_create_child_inserts_and_returns_child() -> None:
    caregiver_id = uuid4()
    child_id = uuid4()
    db = Mock()
    db.get.return_value = Caregiver(id=caregiver_id, display_name="Dev")
    db.add.side_effect = lambda row: setattr(row, "id", child_id)

    response = _call(db, "post", "/children", json=_create_body(caregiver_id))

    assert response.status_code == 201
    assert response.json() == {
        "id": str(child_id),
        "display_name": "Mia",
        "grade_level": 1,
        "interests": ["dinosaurs"],
    }
    db.commit.assert_called_once()


def test_create_child_returns_404_for_unknown_caregiver() -> None:
    db = Mock()
    db.get.return_value = None

    response = _call(db, "post", "/children", json=_create_body(uuid4()))

    assert response.status_code == 404
    db.add.assert_not_called()


def test_create_child_rejects_grade_outside_one_to_three() -> None:
    db = Mock()

    response = _call(db, "post", "/children", json=_create_body(uuid4(), grade_level=4))

    assert response.status_code == 422
    db.add.assert_not_called()


def test_list_children_returns_the_caregivers_children() -> None:
    caregiver_id = uuid4()
    child = Child(
        id=uuid4(),
        caregiver_id=caregiver_id,
        display_name="Mia",
        grade_level=2,
        interests=["space"],
    )
    db = Mock()
    db.get.return_value = Caregiver(id=caregiver_id, display_name="Dev")
    db.scalars.return_value = [child]

    response = _call(db, "get", f"/caregivers/{caregiver_id}/children")

    assert response.status_code == 200
    assert response.json() == [
        {"id": str(child.id), "display_name": "Mia", "grade_level": 2, "interests": ["space"]}
    ]


def test_list_children_returns_404_for_unknown_caregiver() -> None:
    db = Mock()
    db.get.return_value = None

    response = _call(db, "get", f"/caregivers/{uuid4()}/children")

    assert response.status_code == 404


def test_delete_child_removes_child_and_commits() -> None:
    child = Child(id=uuid4(), caregiver_id=uuid4(), display_name="Mia", grade_level=1)
    db = Mock()
    db.get.return_value = child

    response = _call(db, "delete", f"/children/{child.id}")

    assert response.status_code == 204
    db.execute.assert_called_once()  # the child's reading sessions
    db.delete.assert_called_once_with(child)
    db.commit.assert_called_once()


def test_delete_child_returns_404_for_unknown_child() -> None:
    db = Mock()
    db.get.return_value = None

    response = _call(db, "delete", f"/children/{uuid4()}")

    assert response.status_code == 404
    db.delete.assert_not_called()


def test_delete_child_with_reading_history_leaves_nothing_behind() -> None:
    # Real Postgres, because the mocks above can't see the CASCADE and RESTRICT rules
    tables = [
        Caregiver.__table__,
        Child.__table__,
        PhonicsPattern.__table__,
        VocabularyWord.__table__,
        Story.__table__,
        StoryPattern.__table__,
        StoryLine.__table__,
        ReadingSession.__table__,
        ReadingAttempt.__table__,
    ]
    with throwaway_schema(
        "delete_child_test", tables, not_tested="deleting a child with history", seeded=False
    ) as db:
        caregiver = Caregiver(display_name="Test Caregiver")
        db.add(caregiver)
        db.flush()
        child = Child(caregiver_id=caregiver.id, display_name="Test Child", grade_level=1)
        db.add(child)
        db.flush()
        story = Story(child_id=child.id, title="Test", status="validated")
        db.add(story)
        db.flush()
        line = StoryLine(story_id=story.id, line_number=1, text="A fish.")
        reading = ReadingSession(child_id=child.id, story_id=story.id)
        db.add_all([line, reading])
        db.flush()
        db.add(
            ReadingAttempt(
                reading_session_id=reading.id,
                story_line_id=line.id,
                word_index=1,
                expected_word="a",
                result_status="mastered",
            )
        )
        db.flush()

        response = _call(db, "delete", f"/children/{child.id}")

        assert response.status_code == 204
        for model in (Child, Story, StoryLine, ReadingSession, ReadingAttempt):
            assert db.scalar(select(func.count()).select_from(model)) == 0
        assert db.get(Caregiver, caregiver.id) is not None
