import hashlib
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.main import app
from app.models import Caregiver, CaregiverSession


def _call(db: Mock, method: str, path: str, **kwargs):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        return getattr(TestClient(app), method)(path, **kwargs)
    finally:
        app.dependency_overrides.pop(get_db, None)


def _added_session(db: Mock) -> CaregiverSession:
    rows = [c.args[0] for c in db.add.call_args_list]
    return next(r for r in rows if isinstance(r, CaregiverSession))


def test_create_caregiver_returns_token_and_stores_only_its_hash() -> None:
    caregiver_id = uuid4()
    db = Mock()
    db.scalar.return_value = None  # email not taken
    db.flush.side_effect = lambda: setattr(db.add.call_args_list[0].args[0], "id", caregiver_id)

    response = _call(
        db, "post", "/caregivers", json={"display_name": "Sam", "email": " Sam@Example.com "}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["caregiver_id"] == str(caregiver_id)
    assert body["display_name"] == "Sam"
    assert db.add.call_args_list[0].args[0].email == "sam@example.com"
    session = _added_session(db)
    assert session.caregiver_id == caregiver_id
    assert session.token_hash == hashlib.sha256(body["token"].encode()).hexdigest()
    assert session.token_hash != body["token"]
    db.commit.assert_called_once()


def test_create_caregiver_returns_409_for_taken_email() -> None:
    db = Mock()
    db.scalar.return_value = Caregiver(id=uuid4(), display_name="Sam", email="sam@example.com")

    response = _call(
        db, "post", "/caregivers", json={"display_name": "Sam", "email": "sam@example.com"}
    )

    assert response.status_code == 409
    db.add.assert_not_called()


def test_create_caregiver_returns_409_when_a_sign_up_races_on_the_email() -> None:
    db = Mock()
    db.scalar.return_value = None  # the email looked free when checked
    db.flush.side_effect = IntegrityError("INSERT", {}, Exception("duplicate email"))

    response = _call(
        db, "post", "/caregivers", json={"display_name": "Sam", "email": "sam@example.com"}
    )

    assert response.status_code == 409
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_login_finds_caregiver_and_mints_a_new_token_each_time() -> None:
    caregiver = Caregiver(id=uuid4(), display_name="Sam", email="sam@example.com")
    db = Mock()
    db.scalar.return_value = caregiver

    first = _call(db, "post", "/caregivers/session", json={"email": "SAM@example.com"})
    second = _call(db, "post", "/caregivers/session", json={"email": "sam@example.com"})

    assert first.status_code == 200
    assert first.json()["caregiver_id"] == str(caregiver.id)
    assert first.json()["token"] != second.json()["token"]
    assert db.commit.call_count == 2


def test_login_returns_404_for_unknown_email() -> None:
    db = Mock()
    db.scalar.return_value = None

    response = _call(db, "post", "/caregivers/session", json={"email": "nobody@example.com"})

    assert response.status_code == 404
    db.add.assert_not_called()
