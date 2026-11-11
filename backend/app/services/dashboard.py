from datetime import UTC, datetime, timedelta
from string import punctuation
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.core.words import normalize_word
from app.models import (
    PhonicsMastery,
    PhonicsPattern,
    ReadingAttempt,
    ReadingSession,
    Story,
)
from app.schemas.dashboard import DashboardResponse, PatternProgress
from app.services.difficulty import confidence, is_mastered, select_difficulty_target

WEEK = timedelta(days=7)
MAX_PRACTICE_WORDS = 5
# Newest attempts to look at when picking practice words; plenty for 5 distinct words.
RECENT_ATTEMPTS = 50


def build_dashboard(db: Session, child_id: UUID) -> DashboardResponse:
    rows = db.execute(
        select(PhonicsPattern, PhonicsMastery)
        .join(
            PhonicsMastery, PhonicsMastery.phonics_pattern_id == PhonicsPattern.phonics_pattern_id
        )
        .where(PhonicsMastery.child_id == child_id, PhonicsMastery.attempts_count > 0)
        .order_by(PhonicsPattern.sequence_order)
    ).all()

    # Same mastery rule as the difficulty engine, so a pattern can't be both
    # "strongest" and "working on".
    mastered = [
        (pattern, mastery)
        for pattern, mastery in rows
        if is_mastered(mastery.correct_count, mastery.attempts_count)
    ]
    # max() keeps the first of equal scores, so a tie goes to the earlier pattern.
    best = max(
        mastered,
        key=lambda row: confidence(row[1].correct_count, row[1].attempts_count),
        default=None,
    )
    strongest = best[0].label if best else None

    # Same patterns the next story practises, so the dashboard follows the difficulty engine.
    target = select_difficulty_target(db, child_id)
    working_on_patterns = db.scalars(
        select(PhonicsPattern)
        .where(PhonicsPattern.phonics_pattern_id.in_(target.stretch_pattern_ids))
        .order_by(PhonicsPattern.sequence_order)
    ).all()

    return DashboardResponse(
        sessions=_sessions_this_week(db, child_id),
        last_story=_last_story_title(db, child_id),
        working_on=[p.label for p in working_on_patterns],
        strongest=strongest,
        patterns=[
            PatternProgress(label=pattern.label, fill=round(float(mastery.mastery_score) * 100))
            for pattern, mastery in rows
        ],
        try_at_home=_practice_words(db, child_id) or _example_words(working_on_patterns),
    )


def _sessions_this_week(db: Session, child_id: UUID) -> int:
    # A session with no scored word (opened, never read) doesn't count as reading.
    has_scored_word = exists().where(ReadingAttempt.reading_session_id == ReadingSession.id)
    count = db.scalar(
        select(func.count())
        .select_from(ReadingSession)
        .where(
            ReadingSession.child_id == child_id,
            ReadingSession.started_at >= datetime.now(UTC) - WEEK,
            has_scored_word,
        )
    )
    return count or 0


def _last_story_title(db: Session, child_id: UUID) -> str | None:
    return db.scalar(
        select(Story.title)
        .join(ReadingSession, ReadingSession.story_id == Story.id)
        .where(ReadingSession.child_id == child_id)
        .order_by(ReadingSession.started_at.desc())
        .limit(1)
    )


def _practice_words(db: Session, child_id: UUID) -> list[str]:
    """Up to 5 distinct words the child recently got `shaky` or `missed`, newest first."""
    expected_words = db.scalars(
        select(ReadingAttempt.expected_word)
        .join(ReadingSession, ReadingSession.id == ReadingAttempt.reading_session_id)
        .where(
            ReadingSession.child_id == child_id,
            ReadingAttempt.result_status.in_(("shaky", "missed")),
        )
        .order_by(ReadingAttempt.created_at.desc())
        .limit(RECENT_ATTEMPTS)
    )
    words: list[str] = []
    for expected in expected_words:
        # Expected words keep the line's punctuation ("ship."), so strip it, but keep apostrophes.
        word = normalize_word(expected).strip(punctuation.replace("'", ""))
        if word and word not in words:
            words.append(word)
        if len(words) == MAX_PRACTICE_WORDS:
            break
    return words


def _example_words(patterns: list[PhonicsPattern]) -> list[str]:
    """Fallback when there are no missed words yet: the working-on patterns' example words."""
    words: list[str] = []
    for pattern in patterns:
        for word in pattern.example_words:
            if word not in words:
                words.append(word)
    return words[:MAX_PRACTICE_WORDS]
