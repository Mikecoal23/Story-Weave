from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateCaregiverRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=320)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class CaregiverSessionResponse(BaseModel):
    caregiver_id: UUID
    display_name: str
    token: str  # returned once; only its hash is stored
    expires_at: datetime
