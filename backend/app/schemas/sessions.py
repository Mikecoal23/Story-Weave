from typing import Literal

from pydantic import BaseModel

from app.schemas.scoring import ScoreResult


class LineAudioResponse(BaseModel):
    """Response from POST /sessions/{session_id}/lines/{line_number}/audio.

    `status` is present from day one so a future {"status": "pending", "job_id": ...}
    variant is an additive change, not a breaking one (see planning.md, 2026-09-30).
    `result` contains the per-word scores returned by the scoring service.
    """

    status: Literal["complete"]
    result: ScoreResult | None = None
