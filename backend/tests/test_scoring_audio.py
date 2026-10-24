"""The audio half of scoring: FFmpeg conversion and the Azure call, with the SDK faked.

These exist because two bugs only showed up with real audio and the real SDK: a piped
WAV whose header claimed ~37 hours, and `result.properties` being a dict. FFmpeg tests
skip when FFmpeg is not installed.
"""

import json
import shutil
import sys
import wave
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.config import settings
from app.services import scoring

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg is not installed")


def make_wav(seconds: float, rate: int = 16000) -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(rate)
        wav_file.writeframes(b"\x00\x00" * int(seconds * rate))
    return buffer.getvalue()


def wav_seconds(wav_bytes: bytes) -> float:
    with wave.open(BytesIO(wav_bytes), "rb") as wav_file:
        return wav_file.getnframes() / wav_file.getframerate()


@needs_ffmpeg
def test_convert_to_wav_keeps_the_real_duration() -> None:
    converted = scoring._convert_to_wav(make_wav(1.5, rate=44100))

    assert wav_seconds(converted) == pytest.approx(1.5, abs=0.1)


@needs_ffmpeg
def test_convert_to_wav_rejects_audio_ffmpeg_cannot_decode() -> None:
    with pytest.raises(ValueError, match="decode"):
        scoring._convert_to_wav(b"this is not audio")


def fake_speech_sdk(result_json: str) -> MagicMock:
    sdk = MagicMock()
    sdk.ResultReason = SimpleNamespace(NoMatch="no-match", Canceled="canceled", Recognized="ok")
    sdk.ResultReason.RecognizedSpeech = "ok"
    result = SimpleNamespace(
        reason="ok",
        # A plain dict, exactly as the real Python SDK returns it.
        properties={sdk.PropertyId.SpeechServiceResponse_JsonResult: result_json},
    )
    sdk.SpeechRecognizer.return_value.recognize_once.return_value = result
    return sdk


@needs_ffmpeg
def test_score_line_audio_reads_the_azure_json_from_the_properties_dict(monkeypatch) -> None:
    azure_json = json.dumps(
        {
            "NBest": [
                {
                    "Words": [
                        {"Word": "ship", "PronunciationAssessment": {"ErrorType": "None"}},
                    ]
                }
            ]
        }
    )
    monkeypatch.setattr(settings, "azure_speech_key", "test-key")
    monkeypatch.setattr(settings, "azure_speech_region", "test-region")
    # `import azure.cognitiveservices.speech as x` walks attributes from `azure`, so the
    # parent packages are faked as well.
    sdk = fake_speech_sdk(azure_json)
    cognitiveservices = SimpleNamespace(speech=sdk)
    monkeypatch.setitem(sys.modules, "azure", SimpleNamespace(cognitiveservices=cognitiveservices))
    monkeypatch.setitem(sys.modules, "azure.cognitiveservices", cognitiveservices)
    monkeypatch.setitem(sys.modules, "azure.cognitiveservices.speech", sdk)

    result = scoring.score_line_audio(make_wav(1.0), "ship")

    assert [(w.expected_word, w.recognized_word, w.status) for w in result.words] == [
        ("ship", "ship", "mastered")
    ]


@needs_ffmpeg
def test_score_line_audio_accepts_a_short_recording_and_rejects_a_long_one(monkeypatch) -> None:
    monkeypatch.setattr(settings, "azure_speech_key", "test-key")
    monkeypatch.setattr(settings, "azure_speech_region", "test-region")

    with pytest.raises(ValueError, match="30 seconds"):
        scoring.score_line_audio(make_wav(31.0), "ship")
