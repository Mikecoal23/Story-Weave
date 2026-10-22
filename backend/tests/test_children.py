from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models import Caregiver, Child


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
