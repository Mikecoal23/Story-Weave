from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.difficulty import DifficultyTarget


def make_target() -> DifficultyTarget:
    return DifficultyTarget(
        child_id=uuid4(),
        reinforce_pattern_ids=(1, 2),
        stretch_pattern_ids=(3,),
    )


def test_difficulty_target_is_frozen() -> None:
    target = make_target()

    with pytest.raises(ValidationError):
        target.child_id = uuid4()  # type: ignore[misc]


def test_difficulty_target_rejects_non_integer_pattern_ids() -> None:
    with pytest.raises(ValidationError):
        DifficultyTarget(
            child_id=uuid4(),
            reinforce_pattern_ids=("digraph_sh",),  # type: ignore[arg-type]
            stretch_pattern_ids=(),
        )
