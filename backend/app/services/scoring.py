import json
import shutil
import subprocess
import tempfile
import wave
from io import BytesIO
from pathlib import Path
from string import punctuation
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (
    PhonicsMastery,
    ReadingAttempt,
    ReadingSession,
    StoryLine,
    VocabularyWord,
    VocabularyWordPattern,
)
from app.schemas.scoring import ScoreResult, WordScore
from scripts.seed_data import normalize_word


def _normalize_scored_word(word: str) -> str:
    return normalize_word(word).strip(punctuation.replace("'", ""))


def score_line_audio(audio_bytes: bytes, expected_line: str) -> ScoreResult:
    """Assess a browser recording against its expected line with Azure Speech."""
    if not settings.azure_speech_key or not settings.azure_speech_region:
        raise RuntimeError("Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in backend/.env")
    if not audio_bytes:
        raise ValueError("Audio upload is empty")
    if not expected_line.strip():
        raise ValueError("Expected line must not be empty")

    wav_bytes = _convert_to_wav(audio_bytes)
    with wave.open(BytesIO(wav_bytes), "rb") as wav_file:
        duration_seconds = wav_file.getnframes() / wav_file.getframerate()
    if duration_seconds > 30:
        raise ValueError("A single line recording must not exceed 30 seconds")

    import azure.cognitiveservices.speech as speechsdk

    with tempfile.TemporaryDirectory() as temp_dir:
        wav_path = Path(temp_dir) / "audio.wav"
        wav_path.write_bytes(wav_bytes)
        audio_config = speechsdk.audio.AudioConfig(filename=str(wav_path))
        speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_speech_key,
            region=settings.azure_speech_region,
        )
        speech_config.output_format = speechsdk.OutputFormat.Detailed
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            language="en-US",
            audio_config=audio_config,
        )
        assessment_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=expected_line,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Word,
            enable_miscue=True,
        )
        assessment_config.apply_to(recognizer)
        result = recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.NoMatch:
            return ScoreResult(
                words=[
                    WordScore(expected_word=word, status="missed")
                    for word in expected_line.split()
                ]
            )
        if result.reason == speechsdk.ResultReason.Canceled:
            details = speechsdk.CancellationDetails.from_result(result)
            raise RuntimeError(f"Azure Speech assessment failed: {details.error_details}")
        if result.reason != speechsdk.ResultReason.RecognizedSpeech:
            raise RuntimeError(f"Unexpected Azure Speech result: {result.reason}")

        # `result.properties` is a plain dict in the Python SDK (not a PropertyCollection).
        result_json = result.properties[speechsdk.PropertyId.SpeechServiceResponse_JsonResult]
        return _parse_azure_assessment(result_json, expected_line)


def _convert_to_wav(audio_bytes: bytes) -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("FFmpeg is required to convert uploaded audio for Azure Speech")

    # FFmpeg writes the WAV to a file, not to a pipe: a pipe can't be seeked, so the header
    # would claim an unknown (2**31 - 1 frame) length and the duration check would reject
    # every recording.
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = Path(temp_dir) / "input"
        wav_path = Path(temp_dir) / "output.wav"
        source_path.write_bytes(audio_bytes)
        try:
            result = subprocess.run(
                [
                    ffmpeg,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    str(source_path),
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-c:a",
                    "pcm_s16le",
                    str(wav_path),
                ],
                capture_output=True,
                timeout=30,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise TimeoutError("Audio conversion exceeded 30 seconds") from error
        if result.returncode != 0:
            raise ValueError("Could not decode uploaded audio")
        return wav_path.read_bytes()


def _parse_azure_assessment(result_json: str, expected_line: str) -> ScoreResult:
    try:
        result: dict[str, Any] = json.loads(result_json)
        best_result = result["NBest"][0]
        assessed_words = []
        for item in best_result["Words"]:
            error_type = item["PronunciationAssessment"]["ErrorType"]
            if error_type == "Insertion":
                continue
            assessed_words.append(item)

        expected_words = expected_line.split()
        if len(assessed_words) != len(expected_words):
            raise ValueError("Azure Speech words could not be aligned to the reference line")

        words: list[WordScore] = []
        for expected_word, item in zip(expected_words, assessed_words, strict=True):
            recognized_word = item["Word"]
            error_type = item["PronunciationAssessment"]["ErrorType"]
            if error_type == "Omission":
                status = "missed"
                recognized_word = None
            elif error_type == "Mispronunciation":
                status = "shaky"
            elif error_type == "None":
                status = "mastered"
            else:
                raise ValueError(f"Unsupported Azure Speech error type: {error_type}")
            words.append(
                WordScore(
                    expected_word=expected_word,
                    recognized_word=recognized_word,
                    status=status,
                )
            )
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("Azure Speech returned an invalid assessment result") from error

    if not words:
        raise ValueError("Azure Speech returned no scored words")
    return ScoreResult(words=words)


def process_line_score(
    session: Session,
    reading_session_id: UUID,
    story_line_id: UUID,
    score_result: ScoreResult,
) -> None:
    """Persist a line's score and update the child's phonics mastery."""
    reading_session = session.get(ReadingSession, reading_session_id)
    if reading_session is None:
        raise ValueError("Reading session does not exist")

    story_line = session.get(StoryLine, story_line_id)
    if story_line is None or story_line.story_id != reading_session.story_id:
        raise ValueError("Story line does not belong to the reading session")

    word_keys = {
        _normalize_scored_word(word.expected_word) for word in score_result.words
    }
    vocabulary_rows = session.execute(
        select(VocabularyWord, VocabularyWordPattern.phonics_pattern_id)
        .outerjoin(
            VocabularyWordPattern,
            VocabularyWordPattern.vocabulary_word_id == VocabularyWord.vocabulary_word_id,
        )
        .where(VocabularyWord.word.in_(word_keys))
    ).all()

    vocabulary_by_word: dict[str, tuple[VocabularyWord, set[int]]] = {}
    for vocabulary_word, pattern_id in vocabulary_rows:
        if vocabulary_word.word not in vocabulary_by_word:
            vocabulary_by_word[vocabulary_word.word] = (vocabulary_word, set())
        if pattern_id is not None:
            vocabulary_by_word[vocabulary_word.word][1].add(pattern_id)

    for word_index, word_score in enumerate(score_result.words, start=1):
        word_key = _normalize_scored_word(word_score.expected_word)
        vocabulary_entry = vocabulary_by_word.get(word_key)
        vocabulary_word = vocabulary_entry[0] if vocabulary_entry else None
        pattern_ids = vocabulary_entry[1] if vocabulary_entry else set()

        session.add(
            ReadingAttempt(
                reading_session_id=reading_session_id,
                story_line_id=story_line_id,
                word_index=word_index,
                expected_word=word_score.expected_word,
                recognized_word=word_score.recognized_word,
                vocabulary_word_id=(
                    vocabulary_word.vocabulary_word_id if vocabulary_word else None
                ),
                result_status=word_score.status,
            )
        )

        if vocabulary_word is None or vocabulary_word.is_sight_word:
            continue

        for pattern_id in pattern_ids:
            mastery = session.get(
                PhonicsMastery,
                (reading_session.child_id, pattern_id),
            )
            if mastery is None:
                mastery = PhonicsMastery(
                    child_id=reading_session.child_id,
                    phonics_pattern_id=pattern_id,
                    mastery_score=0,
                    attempts_count=0,
                    correct_count=0,
                )
                session.add(mastery)

            mastery.attempts_count += 1
            if word_score.status == "mastered":
                mastery.correct_count += 1
            mastery.mastery_score = mastery.correct_count / mastery.attempts_count

    session.flush()
