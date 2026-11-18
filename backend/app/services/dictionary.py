import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from app.core.config import settings
from app.schemas.dictionary import DictionaryEntry

WORD_PATTERN = re.compile(r"^[A-Za-z]+(?:['’-][A-Za-z]+)*$")
API_URL = "https://www.dictionaryapi.com/api/v3/references/sd2/json"
AUDIO_BASE_URL = "https://media.merriam-webster.com/audio/prons/en/us/mp3"


def _audio_url(audio: str) -> str:
    if audio.startswith("bix"):
        directory = "bix"
    elif audio.startswith("gg"):
        directory = "gg"
    elif audio.startswith("_"):
        directory = "number"
    else:
        directory = audio[0]
    return f"{AUDIO_BASE_URL}/{directory}/{quote(audio)}.mp3"


def get_dictionary_entry(word: str) -> DictionaryEntry:
    normalized_word = word.strip()
    if len(normalized_word) > 50 or not WORD_PATTERN.fullmatch(normalized_word):
        raise ValueError("Word must contain only letters, apostrophes, or hyphens")
    if not settings.merriam_webster_api_key:
        raise RuntimeError("Set MERRIAM_WEBSTER_API_KEY in backend/.env")

    url = (
        f"{API_URL}/{quote(normalized_word, safe='')}"
        f"?key={quote(settings.merriam_webster_api_key, safe='')}"
    )
    try:
        with urlopen(url, timeout=5) as response:
            data: Any = json.loads(response.read())
    except HTTPError as error:
        raise RuntimeError(f"Merriam-Webster request failed with status {error.code}") from error
    except (URLError, TimeoutError) as error:
        raise RuntimeError("Merriam-Webster dictionary is unavailable") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise RuntimeError("Merriam-Webster returned an invalid response") from error

    if not isinstance(data, list):
        raise RuntimeError("Merriam-Webster returned an invalid response")
    entries = [item for item in data if isinstance(item, dict)]
    if not entries:
        raise LookupError("No dictionary entry found for that word")

    definitions: list[str] = []
    phonetic: str | None = None
    audio_url: str | None = None
    headword = normalized_word
    for item in entries:
        if phonetic is None:
            headword_data = item.get("hwi")
            if isinstance(headword_data, dict):
                candidate = headword_data.get("hw")
                if isinstance(candidate, str):
                    headword = candidate.replace("*", "")
                pronunciations = headword_data.get("prs", [])
                if isinstance(pronunciations, list):
                    for pronunciation in pronunciations:
                        if not isinstance(pronunciation, dict):
                            continue
                        mw_spelling = pronunciation.get("mw")
                        if phonetic is None and isinstance(mw_spelling, str):
                            phonetic = mw_spelling
                        sound = pronunciation.get("sound")
                        if audio_url is None and isinstance(sound, dict):
                            audio = sound.get("audio")
                            if isinstance(audio, str) and audio:
                                audio_url = _audio_url(audio)
        short_definitions = item.get("shortdef", [])
        if isinstance(short_definitions, list):
            definitions.extend(
                definition
                for definition in short_definitions
                if isinstance(definition, str) and definition.strip()
            )

    if not definitions:
        raise LookupError("No definition found for that word")

    return DictionaryEntry(
        word=headword,
        phonetic=phonetic,
        definition=definitions[0],
        audio_url=audio_url,
    )
