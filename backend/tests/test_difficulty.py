from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.difficulty import DifficultyTarget
from app.services.difficulty import confidence, is_mastered, pick_patterns

# Stand-in pattern ids in sequence order, so these tests need no database.
IDS = (10, 20, 30, 40, 50)


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


def test_confidence_pulls_few_attempts_toward_one_half() -> None:
    assert confidence(0, 0) == 0.5
    assert confidence(5, 5) == 6 / 7
    assert confidence(17, 20) == 18 / 22


@pytest.mark.parametrize(
    ("correct", "attempts", "expected"),
    [
        (5, 5, True),  # 6/7 = 0.857
        (4, 5, False),  # 5/7 = 0.714: the old rule called this mastered
        (4, 4, False),  # 5/6 = 0.833 but fewer than MIN_ATTEMPTS
        (7, 8, True),  # 8/10 = 0.8 exactly: the threshold is inclusive
        (9, 10, True),  # 10/12 = 0.833
        (8, 10, False),  # 9/12 = 0.75
        (17, 20, True),  # 18/22 = 0.818
        (16, 20, False),  # 17/22 = 0.773
    ],
)
def test_is_mastered(correct: int, attempts: int, expected: bool) -> None:
    assert is_mastered(correct, attempts) is expected


def test_a_new_child_stretches_the_first_two_patterns() -> None:
    assert pick_patterns(IDS, {}) == ((), (10, 20))


def test_sparse_data_stays_in_stretch() -> None:
    # 3 out of 3 is a good start, but too few attempts to call it mastered.
    assert pick_patterns(IDS, {10: (3, 3)}) == ((), (10, 20))


def test_reinforce_keeps_the_two_weakest_mastered_in_sequence_order() -> None:
    counts = {10: (20, 20), 20: (9, 10), 30: (5, 5)}  # 0.955, 0.833, 0.857

    assert pick_patterns(IDS, counts) == ((20, 30), (40, 50))


def test_a_confidence_tie_goes_to_the_earlier_pattern() -> None:
    counts = {10: (9, 10), 20: (9, 10), 30: (9, 10)}

    assert pick_patterns(IDS, counts) == ((10, 20), (40, 50))


def test_a_mastered_pattern_that_slips_goes_back_to_stretch() -> None:
    counts = {10: (9, 10), 20: (8, 12)}  # 20 was 8/8 once; now 9/14 = 0.643

    assert pick_patterns(IDS, counts) == ((10,), (20, 30))


def test_a_gap_in_the_sequence_stays_in_stretch() -> None:
    assert pick_patterns(IDS, {20: (9, 10)}) == ((20,), (10, 30))


def test_when_everything_is_mastered_stretch_is_empty() -> None:
    counts = {pattern_id: (9, 10) for pattern_id in IDS}

    assert pick_patterns(IDS, counts) == ((10, 20), ())


# --- spaced repetition: reinforce prefers the patterns practised longest ago ---------------

T0 = datetime(2026, 11, 1, tzinfo=UTC)
MASTERED = {10: (20, 20), 20: (9, 10), 30: (5, 5)}  # confidence 0.955, 0.833, 0.857


def test_reinforce_prefers_the_patterns_practised_longest_ago() -> None:
    # By confidence alone this would be (20, 30); 20 was read yesterday, so 10 comes in.
    last = {10: T0, 20: T0 + timedelta(days=9), 30: T0 + timedelta(days=5)}

    assert pick_patterns(IDS, MASTERED, last) == ((10, 30), (40, 50))


def test_a_never_practised_mastered_pattern_comes_before_any_practised_one() -> None:
    last = {10: T0, 20: T0 + timedelta(days=9)}  # 30 has no time

    assert pick_patterns(IDS, MASTERED, last) == ((10, 30), (40, 50))


def test_equal_times_fall_back_to_the_lowest_confidence() -> None:
    last = {10: T0, 20: T0, 30: T0}

    assert pick_patterns(IDS, MASTERED, last) == ((20, 30), (40, 50))


def test_without_times_the_rule_is_the_confidence_rule() -> None:
    assert pick_patterns(IDS, MASTERED) == pick_patterns(IDS, MASTERED, {}) == ((20, 30), (40, 50))


def test_recency_never_changes_which_patterns_are_stretched() -> None:
    counts = {**MASTERED, 40: (1, 2)}
    last = {10: T0, 20: T0, 30: T0, 40: T0 + timedelta(days=30)}

    assert pick_patterns(IDS, counts, last)[1] == pick_patterns(IDS, counts)[1] == (40, 50)
