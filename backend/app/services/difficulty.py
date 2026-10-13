from uuid import UUID

from sqlalchemy.orm import Session

from app.schemas.difficulty import DifficultyTarget


def select_difficulty_target(session: Session, child_id: UUID) -> DifficultyTarget:
    """Choose the phonics patterns a child's next story should use.

    Stage 1 seam: placeholder only, so the signature is in place for Component 3 to call.
    The naive first-pass body (reuse mastered patterns, pick stretch patterns by
    sequence_order) is a Stage 2 task. Component 2 replaces this body in Sprint 3.
    The signature (session, child_id) is part of the frozen contract, so don't change it
    without a Decisions Log entry.
    """
    raise NotImplementedError("select_difficulty_target is a Stage 2 task")
