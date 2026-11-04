from pydantic import BaseModel


class PatternProgress(BaseModel):
    label: str
    fill: int  # percent mastered, 0-100


# Mirrors the `Dashboard` type in frontend/src/api/types.ts. Keep the two in step.
class DashboardResponse(BaseModel):
    sessions: int  # reading sessions this week that have at least one scored word
    last_story: str | None  # None until the child's first session
    working_on: list[str]  # pattern labels
    strongest: str | None  # None until a pattern is mastered
    patterns: list[PatternProgress]
    try_at_home: list[str]  # practice words
