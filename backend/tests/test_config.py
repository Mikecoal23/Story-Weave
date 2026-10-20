import pytest

from app.core.config import Settings


def test_alembic_uses_direct_database_url_when_configured() -> None:
    settings = Settings(
        database_url=(
            "postgresql+psycopg://user:password@ep-example-pooler.us-east-2.aws.neon.tech/db"
        ),
        database_url_unpooled=(
            "postgresql+psycopg://user:password@ep-example.us-east-2.aws.neon.tech/db"
        ),
    )

    assert settings.alembic_database_url == settings.database_url_unpooled


def test_alembic_rejects_pooled_url_when_direct_url_is_missing() -> None:
    settings = Settings(
        database_url=(
            "postgresql+psycopg://user:password@ep-example-pooler.us-east-2.aws.neon.tech/db"
        ),
        database_url_unpooled=None,
    )

    with pytest.raises(ValueError, match="direct URL"):
        _ = settings.alembic_database_url
