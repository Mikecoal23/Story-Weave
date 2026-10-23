"""Shared test helpers. Imported as `support` (pytest puts tests/ on sys.path)."""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager

import pytest
from sqlalchemy import Table, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.session import engine
from scripts.seed_vocabulary import LOCAL_HOSTS, seed


@contextmanager
def throwaway_schema(
    schema: str, tables: Sequence[Table], *, not_tested: str, seeded: bool = True
) -> Iterator[Session]:
    """A session on a fresh schema holding `tables`, inside a transaction that is always
    rolled back, so a test never touches real rows.

    Skips unless the database is local Postgres: tests must not run against a shared
    database (planning.md, 2026-10-09). The skip message names what was NOT tested, so a
    skip is never mistaken for a pass. `seeded` loads the real vocabulary seed first. The
    session has autoflush off and expire_on_commit off, like the app's `SessionLocal`, so a
    bug that depends on flush timing shows up here too.
    """
    if make_url(str(engine.url)).host not in LOCAL_HOSTS:
        pytest.skip(f"DB tests only run against a local database: {not_tested} was NOT tested")
    try:
        connection = engine.connect()
    except OperationalError:
        pytest.skip(
            f"local Postgres is not running (docker compose up -d db): {not_tested} was NOT tested"
        )
    transaction = connection.begin()
    try:
        connection.execute(text(f"CREATE SCHEMA {schema}"))
        connection.execute(text(f"SET LOCAL search_path TO {schema}"))
        for table in tables:
            table.create(connection, checkfirst=False)
        with Session(bind=connection, autoflush=False, expire_on_commit=False) as session:
            if seeded:
                seed(session)
            yield session
    finally:
        transaction.rollback()
        connection.close()
