from uuid import UUID

from pydantic import BaseModel, Field


class CreateChildRequest(BaseModel):
    caregiver_id: UUID
    display_name: str = Field(min_length=1, max_length=120)
    grade_level: int = Field(ge=1, le=3)  # matches ck_child_grade_level
    interests: list[str] = []


class ChildResponse(BaseModel):
    id: UUID
    display_name: str
    grade_level: int
    interests: list[str]
