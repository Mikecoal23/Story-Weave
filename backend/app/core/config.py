from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://storyweave:storyweave_dev_only@localhost:5432/storyweave"
    )
    speechace_api_key: str | None = None
    merriam_webster_api_key: str | None = None
    anthropic_api_key: str | None = None
    anthropic_story_model: str = "claude-haiku-4-5-20251001"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        extra="ignore",
    )


settings = Settings()