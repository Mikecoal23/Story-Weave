from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateChildRequest(BaseModel):
    caregiver_id: UUID
    display_name: str = Field(min_length=1, max_length=120)
    grade_level: int = Field(ge=1, le=3)  # matches ck_child_grade_level
    interests: list[str] = []
    pin: str = Field(pattern=r"^\d{4}$")


class ChildResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    grade_level: int
    interests: list[str]
    pin_set: bool


class PinRequest(BaseModel):
    pin: str = Field(pattern=r"^\d{4}$")


class PinVerificationResponse(BaseModel):
    verified: bool


class ChildPinResponse(BaseModel):
    pin: str
