"""Seed phonics_pattern, vocabulary_word and vocabulary_word_pattern from scripts.seed_data.

Run from backend/ (the target database comes from DATABASE_URL / backend/.env):

    uv run python -m scripts.seed_vocabulary --dry-run   # does everything, then rolls back
    uv run python -m scripts.seed_vocabulary             # local Docker only by default

Safe to re-run: patterns upsert on `code`, words upsert on `word` (is_sight_word is
updated, so promoting a word is one edit plus one re-run), and each seeded word's
junction rows are reconciled to match the data exactly, so a sight word always ends
with zero pattern rows. The whole run is one transaction. Patterns are never deleted
(the junction table cascades, so a delete would silently drop word-to-pattern rows).
Words in the database that are not in the seed data are left alone and only counted.
"""

import argparse
import sys
from dataclasses import dataclass

from sqlalchemy import delete, func, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.models import PhonicsPattern, VocabularyWord, VocabularyWordPattern
from scripts.seed_data import PATTERNS, build_words

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


@dataclass(frozen=True)
class SeedReport:
    patterns: int
    words: int
    sight_words: int
    junction_rows: int
    junction_added: int
    junction_removed: int
    unmanaged_words: int


def seed(session: Session) -> SeedReport:
    """Make the three tables match the seed data. Flushes but never commits."""
    words = build_words()

    pattern_stmt = insert(PhonicsPattern).values(
        [
            {
                "code": p.code,
                "label": p.label,
                "category": p.category,
                "example_words": list(p.example_words),
                "sequence_order": p.sequence_order,
            }
            for p in PATTERNS
        ]
    )
    pattern_ids = dict(
        session.execute(
            pattern_stmt.on_conflict_do_update(
                index_elements=["code"],
                set_={
                    column: getattr(pattern_stmt.excluded, column)
                    for column in ("label", "category", "example_words", "sequence_order")
                },
            ).returning(PhonicsPattern.code, PhonicsPattern.phonics_pattern_id)
        ).all()
    )

    word_stmt = insert(VocabularyWord).values(
        [{"word": w.word, "is_sight_word": w.is_sight_word} for w in words]
    )
    word_ids = dict(
        session.execute(
            word_stmt.on_conflict_do_update(
                index_elements=["word"],
                set_={"is_sight_word": word_stmt.excluded.is_sight_word},
            ).returning(VocabularyWord.word, VocabularyWord.vocabulary_word_id)
        ).all()
    )

    seeded_word_ids = list(word_ids.values())
    desired = {(word_ids[w.word], pattern_ids[code]) for w in words for code in w.pattern_codes}
    existing = {
        (row[0], row[1])
        for row in session.execute(
            select(
                VocabularyWordPattern.vocabulary_word_id,
                VocabularyWordPattern.phonics_pattern_id,
            ).where(VocabularyWordPattern.vocabulary_word_id.in_(seeded_word_ids))
        )
    }
    stale = existing - desired
    missing = desired - existing

    if stale:
        session.execute(
            delete(VocabularyWordPattern).where(
                tuple_(
                    VocabularyWordPattern.vocabulary_word_id,
                    VocabularyWordPattern.phonics_pattern_id,
                ).in_(stale)
            )
        )
    if missing:
        session.execute(
            insert(VocabularyWordPattern)
            .values(
                [
                    {"vocabulary_word_id": word_id, "phonics_pattern_id": pattern_id}
                    for word_id, pattern_id in sorted(missing)
                ]
            )
            .on_conflict_do_nothing()
        )

    def count(model, *where) -> int:
        return session.scalar(select(func.count()).select_from(model).where(*where)) or 0

    return SeedReport(
        patterns=count(PhonicsPattern),
        words=count(VocabularyWord),
        sight_words=count(VocabularyWord, VocabularyWord.is_sight_word.is_(True)),
        junction_rows=count(VocabularyWordPattern),
        junction_added=len(missing),
        junction_removed=len(stale),
        unmanaged_words=count(
            VocabularyWord, VocabularyWord.vocabulary_word_id.not_in(seeded_word_ids)
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="run everything, then roll back")
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="permit a non-localhost database (e.g. Neon dev); never use on production",
    )
    args = parser.parse_args(argv)

    # Imported here so --help works without a database configured.
    from app.core.config import settings
    from app.db.session import SessionLocal

    url = make_url(settings.database_url)
    print(f"Target database: host={url.host} port={url.port} database={url.database}")
    if url.host not in LOCAL_HOSTS and not args.allow_remote:
        print("Refusing: not a localhost database. Re-run with --allow-remote if intended.")
        return 2

    with SessionLocal() as session:
        try:
            report = seed(session)
            if args.dry_run:
                session.rollback()
            else:
                session.commit()
        except Exception:
            session.rollback()
            raise

    mode = "DRY RUN (rolled back)" if args.dry_run else "COMMITTED"
    print(f"{mode}: {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
