from typing import Any, Literal

from pydantic import BaseModel


class LineAudioResponse(BaseModel):
    """Response from POST /sessions/{session_id}/lines/{line_number}/audio.

    `status` is present from day one so a future {"status": "pending", "job_id": ...}
    variant is an additive change, not a breaking one (see planning.md, 2026-09-30).
    `result` is a placeholder until Michael defines ScoreResult; then replace the
    `dict[str, Any] | None` type with that model.
    """

    status: Literal["complete"]
    result: dict[str, Any] | None = None
