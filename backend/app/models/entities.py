import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Caregiver(Base):
    __tablename__ = "caregiver"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CaregiverSession(Base):
    __tablename__ = "caregiver_session"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caregiver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("caregiver.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Child(Base):
    __tablename__ = "child"
    __table_args__ = (CheckConstraint("grade_level BETWEEN 1 AND 3", name="ck_child_grade_level"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caregiver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("caregiver.id", ondelete="CASCADE"), nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    grade_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    interests: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PhonicsPattern(Base):
    __tablename__ = "phonics_pattern"
    __table_args__ = (
        UniqueConstraint("sequence_order", name="uq_phonics_pattern_sequence_order"),
        CheckConstraint("sequence_order > 0", name="ck_phonics_pattern_sequence_order"),
    )

    phonics_pattern_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    example_words: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)


class VocabularyWord(Base):
    __tablename__ = "vocabulary_word"
    __table_args__ = (
        CheckConstraint("word = lower(word)", name="ck_vocabulary_word_lowercase"),
        CheckConstraint("word = trim(word)", name="ck_vocabulary_word_trimmed"),
        CheckConstraint("length(word) > 0", name="ck_vocabulary_word_not_empty"),
    )

    vocabulary_word_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    word: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_sight_word: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VocabularyWordPattern(Base):
    __tablename__ = "vocabulary_word_pattern"

    vocabulary_word_id: Mapped[int] = mapped_column(
        ForeignKey("vocabulary_word.vocabulary_word_id", ondelete="CASCADE"), primary_key=True
    )
    phonics_pattern_id: Mapped[int] = mapped_column(
        ForeignKey("phonics_pattern.phonics_pattern_id", ondelete="CASCADE"), primary_key=True
    )


class Story(Base):
    __tablename__ = "story"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'validated', 'approved')", name="ck_story_status"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    theme: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StoryPattern(Base):
    __tablename__ = "story_pattern"

    story_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("story.id", ondelete="CASCADE"), primary_key=True
    )
    phonics_pattern_id: Mapped[int] = mapped_column(
        ForeignKey("phonics_pattern.phonics_pattern_id", ondelete="RESTRICT"), primary_key=True
    )


class StoryLine(Base):
    __tablename__ = "story_line"
    __table_args__ = (
        UniqueConstraint("story_id", "line_number", name="uq_story_line_number"),
        CheckConstraint("line_number > 0", name="ck_story_line_positive_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("story.id", ondelete="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)


class ReadingSession(Base):
    __tablename__ = "reading_session"
    __table_args__ = (
        CheckConstraint(
            "status IN ('in_progress', 'completed', 'abandoned')",
            name="ck_reading_session_status",
        ),
        Index("ix_reading_session_child_started", "child_id", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id", ondelete="CASCADE"), nullable=False
    )
    story_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("story.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_progress")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PhonicsMastery(Base):
    __tablename__ = "phonics_mastery"
    __table_args__ = (
        CheckConstraint("mastery_score BETWEEN 0 AND 1", name="ck_phonics_mastery_score"),
        CheckConstraint("attempts_count >= 0", name="ck_phonics_mastery_attempts"),
        CheckConstraint(
            "correct_count >= 0 AND correct_count <= attempts_count",
            name="ck_phonics_mastery_correct_count",
        ),
        Index("ix_phonics_mastery_pattern_score", "phonics_pattern_id", "mastery_score"),
    )

    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id", ondelete="CASCADE"), primary_key=True
    )
    phonics_pattern_id: Mapped[int] = mapped_column(
        ForeignKey("phonics_pattern.phonics_pattern_id", ondelete="RESTRICT"), primary_key=True
    )
    mastery_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0)
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ReadingAttempt(Base):
    __tablename__ = "reading_attempt"
    __table_args__ = (
        CheckConstraint("word_index > 0", name="ck_reading_attempt_word_index"),
        CheckConstraint(
            "result_status IN ('mastered', 'shaky', 'missed')",
            name="ck_reading_attempt_result_status",
        ),
        Index("ix_reading_attempt_session_line", "reading_session_id", "story_line_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reading_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reading_session.id", ondelete="CASCADE"), nullable=False
    )
    story_line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("story_line.id", ondelete="CASCADE"), nullable=False
    )
    word_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    expected_word: Mapped[str] = mapped_column(String(100), nullable=False)
    recognized_word: Mapped[str | None] = mapped_column(String(100))
    vocabulary_word_id: Mapped[int | None] = mapped_column(
        ForeignKey("vocabulary_word.vocabulary_word_id", ondelete="SET NULL")
    )
    result_status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ArticulationFlag(Base):
    __tablename__ = "articulation_flag"
    __table_args__ = (
        CheckConstraint(
            "phoneme IS NOT NULL OR phonics_pattern_id IS NOT NULL",
            name="ck_articulation_flag_target",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id", ondelete="CASCADE"), nullable=False
    )
    phoneme: Mapped[str | None] = mapped_column(String(32))
    phonics_pattern_id: Mapped[int | None] = mapped_column(
        ForeignKey("phonics_pattern.phonics_pattern_id", ondelete="CASCADE")
    )
    note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())