"""Insert fixed-id dev rows (one caregiver, two children, one story) for wiring the frontend.

Run from backend/ (the target database comes from DATABASE_URL / backend/.env):

    uv run python -m scripts.dev_fixtures --dry-run   # does everything, then rolls back
    uv run python -m scripts.dev_fixtures             # local Docker only by default

The ids are fixed, so every machine and Neon `dev` get the same ones; put CAREGIVER_ID in
frontend/src/api/config.ts and use the child ids wherever the mock children used '1'/'2'.
Safe to re-run: each row is created only when its id is missing, and existing rows are
never modified. Separate from scripts.seed_dev_data (random ids, different email) on
purpose, so the two never touch each other's rows. Run scripts.seed_vocabulary first.
"""

import argparse
import sys
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.models import Caregiver, Child, PhonicsPattern, Story
from app.schemas.stories import ValidatedStory
from app.services.story_store import save_validated_story
from app.services.story_templates import FALLBACK_TEMPLATES

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}

CAREGIVER_ID = UUID("f1000000-0000-4000-8000-000000000001")
CAREGIVER_EMAIL = "fixtures.caregiver@example.com"
MIA_ID = UUID("f1000000-0000-4000-8000-0000000000a1")
LEO_ID = UUID("f1000000-0000-4000-8000-0000000000a2")
STORY_ID = UUID("f1000000-0000-4000-8000-0000000000b1")

CHILDREN = [
    (MIA_ID, "Mia", 1, ["dinosaurs", "the ocean"]),
    (LEO_ID, "Leo", 1, ["trucks", "space"]),
]


def seed_fixtures(session: Session) -> dict[str, str]:
    """Create the fixture rows that are missing. Flushes but never commits."""
    if session.scalar(select(PhonicsPattern.phonics_pattern_id).limit(1)) is None:
        raise RuntimeError("phonics_pattern is empty: run scripts.seed_vocabulary first")

    if session.get(Caregiver, CAREGIVER_ID) is None:
        session.add(
            Caregiver(id=CAREGIVER_ID, display_name="Fixtures Caregiver", email=CAREGIVER_EMAIL)
        )
        session.flush()

    for child_id, name, grade_level, interests in CHILDREN:
        if session.get(Child, child_id) is None:
            session.add(
                Child(
                    id=child_id,
                    caregiver_id=CAREGIVER_ID,
                    display_name=name,
                    grade_level=grade_level,
                    interests=interests,
                )
            )
            session.flush()

    if session.get(Story, STORY_ID) is None:
        template = FALLBACK_TEMPLATES[0]
        story = ValidatedStory(**template.model_dump(), source="fallback", attempts=0)
        save_validated_story(session, MIA_ID, story, story_id=STORY_ID)

    return {
        "caregiver_id": str(CAREGIVER_ID),
        "mia_child_id": str(MIA_ID),
        "leo_child_id": str(LEO_ID),
        "story_id": str(STORY_ID),
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
            ids = seed_fixtures(session)
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
