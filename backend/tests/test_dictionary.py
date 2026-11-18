import io
import json

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_dictionary_lookup_returns_definition_phonetic_and_audio(monkeypatch) -> None:
    payload = [
        {
            "hwi": {
                "hw": "ship",
                "prs": [{"mw": "ˈship", "sound": {"audio": "ship0001"}}],
            },
            "shortdef": ["a large seagoing vessel"],
        }
    ]
    monkeypatch.setattr(settings, "merriam_webster_api_key", "test-key")
    monkeypatch.setattr(
        "app.services.dictionary.urlopen",
        lambda url, timeout: io.BytesIO(json.dumps(payload).encode()),
    )

    response = client.get("/dictionary/ship")

    assert response.status_code == 200
    assert response.json() == {
        "word": "ship",
        "phonetic": "ˈship",
        "definition": "a large seagoing vessel",
        "audio_url": ("https://media.merriam-webster.com/audio/prons/en/us/mp3/s/ship0001.mp3"),
    }


def test_dictionary_lookup_rejects_invalid_words(monkeypatch) -> None:
    monkeypatch.setattr(settings, "merriam_webster_api_key", "test-key")
    monkeypatch.setattr(
        "app.services.dictionary.urlopen",
        lambda url, timeout: (_ for _ in ()).throw(AssertionError("unexpected request")),
    )

    assert client.get("/dictionary/word%20with%20spaces").status_code == 422


def test_dictionary_lookup_handles_words_without_entries(monkeypatch) -> None:
    monkeypatch.setattr(settings, "merriam_webster_api_key", "test-key")
    monkeypatch.setattr(
        "app.services.dictionary.urlopen",
        lambda url, timeout: io.BytesIO(json.dumps(["shipper", "ships"]).encode()),
    )

    response = client.get("/dictionary/unknown")

    assert response.status_code == 404


def test_dictionary_lookup_requires_server_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "merriam_webster_api_key", None)
    monkeypatch.setattr(
        "app.services.dictionary.urlopen",
        lambda url, timeout: (_ for _ in ()).throw(AssertionError("unexpected request")),
    )

    assert client.get("/dictionary/ship").status_code == 502


def test_merriam_webster_api_key_is_not_returned_to_the_client(monkeypatch) -> None:
    payload = [{"hwi": {"hw": "ship"}, "shortdef": ["a vessel"]}]
    monkeypatch.setattr(settings, "merriam_webster_api_key", "secret-test-key")
    requested_urls: list[str] = []

    def fake_urlopen(url, timeout):
        requested_urls.append(url)
        return io.BytesIO(json.dumps(payload).encode())

    monkeypatch.setattr("app.services.dictionary.urlopen", fake_urlopen)

    response = client.get("/dictionary/ship")

    assert response.status_code == 200
    assert "secret-test-key" not in response.text
    assert "secret-test-key" in requested_urls[0]
