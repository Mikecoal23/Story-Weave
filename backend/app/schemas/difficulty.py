from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DifficultyTarget(BaseModel):
    """What a child's next story should practice.

    This is the FROZEN contract between Component 2 (adaptive difficulty engine,
    which fills it in) and Component 3 (story generator, which reads it). Don't
    rename or retype these fields casually: the generator depends on them directly.
    Adding a new optional field is fine; changing an existing one needs a Decisions
    Log entry in planning.md first.

    Pattern values are `phonics_pattern.phonics_pattern_id` integers.
    """

    model_config = ConfigDict(frozen=True)

    child_id: UUID
    # Patterns the child has already mastered; the next story reuses them.
    reinforce_pattern_ids: tuple[int, ...]
    # New patterns to introduce, in `sequence_order` order.
    stretch_pattern_ids: tuple[int, ...]
