from typing import Literal

from pydantic import BaseModel


class WordScore(BaseModel):
    expected_word: str
    recognized_word: str | None = None
    status: Literal["mastered", "shaky", "missed"]


class ScoreResult(BaseModel):
    words: list[WordScore]
