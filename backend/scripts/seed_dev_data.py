"""Seed one caregiver, one child and one short story for local development.

Run from backend/ (the target database comes from DATABASE_URL / backend/.env):

    uv run python -m scripts.seed_dev_data --dry-run   # does everything, then rolls back
    uv run python -m scripts.seed_dev_data             # local Docker only by default

Safe to re-run: each row is looked up first (caregiver by email, child by caregiver and
name, story by child and title) and only created when missing. Prints the three ids; put
the caregiver id in CAREGIVER_ID in frontend/src/api/config.ts. Run
scripts.seed_vocabulary first so the story's words exist in vocabulary_word.
"""

import argparse
import sys

from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.models import Caregiver, Child, Story, StoryLine

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}

CAREGIVER_EMAIL = "dev.caregiver@example.com"
CHILD_NAME = "Dev Reader"
STORY_TITLE = "The Big Dog"
STORY_LINES = [
    "The big dog ran.",
    "The dog sat in the sun.",
    "She can see the dog.",
    "It is fun.",
]


def seed(session: Session) -> dict[str, str]:
    """Create the dev rows that are missing. Flushes but never commits."""
    caregiver = session.scalar(select(Caregiver).where(Caregiver.email == CAREGIVER_EMAIL))
    if caregiver is None:
        caregiver = Caregiver(display_name="Dev Caregiver", email=CAREGIVER_EMAIL)
        session.add(caregiver)
        session.flush()

    child = session.scalar(
        select(Child).where(
            Child.caregiver_id == caregiver.id, Child.display_name == CHILD_NAME
        )
    )
    if child is None:
        child = Child(
            caregiver_id=caregiver.id,
            display_name=CHILD_NAME,
            grade_level=1,
            interests=["dogs", "space"],
        )
        session.add(child)
        session.flush()

    story = session.scalar(
        select(Story).where(Story.child_id == child.id, Story.title == STORY_TITLE)
    )
    if story is None:
        story = Story(child_id=child.id, title=STORY_TITLE, theme="dogs", status="approved")
        session.add(story)
        session.flush()
        session.add_all(
            StoryLine(story_id=story.id, line_number=number, text=text)
            for number, text in enumerate(STORY_LINES, start=1)
        )
        session.flush()

    return {
        "caregiver_id": str(caregiver.id),
        "child_id": str(child.id),
        "story_id": str(story.id),
    }


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
            ids = seed(session)
            if args.dry_run:
                session.rollback()
            else:
                session.commit()
        except Exception:
            session.rollback()
            raise

    mode = "DRY RUN (rolled back)" if args.dry_run else "COMMITTED"
    print(f"{mode}:")
    for name, value in ids.items():
        print(f"  {name} = {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
