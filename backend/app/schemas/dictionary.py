from pydantic import BaseModel


class DictionaryEntry(BaseModel):
    word: str
    phonetic: str | None
    definition: str
    audio_url: str | None
