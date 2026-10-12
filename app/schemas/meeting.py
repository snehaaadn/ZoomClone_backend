from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from backend.app.schemas.participant import ParticipantResponse


class MeetingBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Meeting title")
    description: Optional[str] = Field(None, max_length=1000, description="Optional meeting description")


class InstantMeetingCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Optional title, defaults to '{host}'s Personal Meeting'")
    host_display_name: Optional[str] = Field(None, max_length=128, description="Host display name")
    passcode: Optional[str] = Field(None, max_length=16, description="Optional meeting passcode")


class MeetingScheduleCreate(MeetingBase):
    host_display_name: Optional[str] = Field(None, max_length=128, description="Host display name")
    start_time: datetime = Field(..., description="Scheduled start time in ISO 8601 format")
    duration: int = Field(30, ge=5, le=1440, description="Duration in minutes (between 5 and 1440)")
    passcode: Optional[str] = Field(None, max_length=16, description="Optional passcode")
    timezone: Optional[str] = Field("UTC", max_length=64, description="Host timezone")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Meeting title cannot be empty or only spaces")
        return trimmed


class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, description="scheduled, active, ended, cancelled")
    duration: Optional[int] = Field(None, ge=5, le=1440)


class MeetingJoinRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=128, description="Participant display name")
    passcode: Optional[str] = Field(None, description="Meeting passcode if required")
    client_id: Optional[str] = Field(None, description="Unique client ID or device ID")


class MeetingResponse(MeetingBase):
    id: int
    meeting_id: str
    invite_token: str
    invite_url: str
    passcode: str
    host_display_name: str
    start_time: datetime
    duration: int
    status: str
    is_instant: bool
    created_at: datetime
    updated_at: datetime
    participant_count: int = 0
    participants: List[ParticipantResponse] = []

    model_config = ConfigDict(from_attributes=True)


class MeetingValidationResponse(BaseModel):
    exists: bool
    is_valid: bool
    meeting_id: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None
    host_display_name: Optional[str] = None
    start_time: Optional[datetime] = None
    duration: Optional[int] = None
    message: str
