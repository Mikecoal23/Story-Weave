from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://storyweave:storyweave_dev_only@localhost:5432/storyweave"
    )
    database_url_unpooled: str | None = None
    azure_speech_key: str | None = None
    azure_speech_region: str | None = None
    merriam_webster_api_key: str | None = None
    anthropic_api_key: str | None = None
    anthropic_story_model: str = "claude-haiku-4-5-20251001"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        extra="ignore",
    )

    @property
    def alembic_database_url(self) -> str:
        """Return a direct connection URL and reject Neon transaction-pooler hosts."""
        url = self.database_url_unpooled or self.database_url
        host = make_url(url).host
        if host is not None and "-pooler" in host:
            raise ValueError("Alembic requires the direct URL in DATABASE_URL_UNPOOLED")
        return url


settings = Settings()