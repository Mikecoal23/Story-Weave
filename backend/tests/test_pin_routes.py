import hashlib
from unittest.mock import Mock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.auth import get_current_caregiver
from app.core.config import settings
from app.core.pins import encrypt_pin, hash_pin
from app.db.session import get_db
from app.main import app
from app.models import Caregiver, CaregiverSession, Child


def _call(db: Mock, method: str, path: str, current: Caregiver, **kwargs):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_caregiver] = lambda: current
    try:
        return getattr(TestClient(app), method)(path, **kwargs)
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_caregiver, None)


def test_caregiver_session_auth_uses_the_stored_token_hash() -> None:
    caregiver = Caregiver(id=uuid4(), display_name="Parent")
    token = "session-token"
    session = CaregiverSession(
        caregiver_id=caregiver.id, token_hash=hashlib.sha256(token.encode()).hexdigest()
    )
    db = Mock()
    db.scalar.return_value = session
    db.get.return_value = caregiver

    assert get_current_caregiver(f"Bearer {token}", db) is caregiver
    db.get.assert_called_once_with(Caregiver, caregiver.id)


def test_caregiver_session_auth_rejects_missing_or_invalid_tokens() -> None:
    with pytest.raises(HTTPException) as missing:
        get_current_caregiver(None, Mock())
    assert missing.value.status_code == 401

    db = Mock()
    db.scalar.return_value = None
    with pytest.raises(HTTPException) as invalid:
        get_current_caregiver("Bearer bad-token", db)
    assert invalid.value.status_code == 401


def test_child_pin_can_be_verified_recovered_and_changed(monkeypatch) -> None:
    monkeypatch.setattr(settings, "pin_encryption_key", Fernet.generate_key().decode())
    caregiver = Caregiver(id=uuid4(), display_name="Parent")
    child = Child(
        id=uuid4(),
        caregiver_id=caregiver.id,
        display_name="Mia",
        grade_level=1,
        pin_ciphertext=encrypt_pin("0420"),
    )
    db = Mock()
    db.get.return_value = child

    assert child.pin_ciphertext != "0420"
    assert _call(
        db, "post", f"/children/{child.id}/verify-pin", caregiver, json={"pin": "0420"}
    ).json() == {"verified": True}
    assert _call(
        db, "post", f"/children/{child.id}/verify-pin", caregiver, json={"pin": "1234"}
    ).json() == {"verified": False}
    assert _call(db, "get", f"/children/{child.id}/pin", caregiver).json() == {"pin": "0420"}

    response = _call(db, "put", f"/children/{child.id}/pin", caregiver, json={"pin": "5678"})

    assert response.status_code == 204
    assert child.pin_ciphertext != "5678"
    assert db.commit.call_count == 1


def test_child_pin_is_not_available_to_another_caregiver(monkeypatch) -> None:
    monkeypatch.setattr(settings, "pin_encryption_key", Fernet.generate_key().decode())
    caregiver = Caregiver(id=uuid4(), display_name="Parent")
    child = Child(
        id=uuid4(),
        caregiver_id=uuid4(),
        display_name="Mia",
        grade_level=1,
        pin_ciphertext=encrypt_pin("0420"),
    )
    db = Mock()
    db.get.return_value = child

    response = _call(db, "get", f"/children/{child.id}/pin", caregiver)

    assert response.status_code == 404


def test_parent_pin_verification_resets_failures_and_locks_after_five_attempts() -> None:
    caregiver = Caregiver(
        id=uuid4(),
        display_name="Parent",
        pin_hash=hash_pin("0420"),
        pin_failed_attempts=0,
    )
    db = Mock()

    for _ in range(4):
        response = _call(
            db,
            "post",
            f"/caregivers/{caregiver.id}/verify-pin",
            caregiver,
            json={"pin": "1234"},
        )
        assert response.json() == {"verified": False}

    assert _call(
        db,
        "post",
        f"/caregivers/{caregiver.id}/verify-pin",
        caregiver,
        json={"pin": "0420"},
    ).json() == {"verified": True}
    assert caregiver.pin_failed_attempts == 0
    assert caregiver.pin_locked_until is None

    for _ in range(5):
        response = _call(
            db,
            "post",
            f"/caregivers/{caregiver.id}/verify-pin",
            caregiver,
            json={"pin": "1234"},
        )
        assert response.json() == {"verified": False}

    assert caregiver.pin_locked_until is not None
    assert (
        _call(
            db,
            "post",
            f"/caregivers/{caregiver.id}/verify-pin",
            caregiver,
            json={"pin": "0420"},
        ).status_code
        == 429
    )
