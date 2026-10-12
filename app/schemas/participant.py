from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ParticipantBase(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=128, description="Display name of the participant")


class ParticipantCreate(ParticipantBase):
    client_id: str = Field(..., min_length=1, max_length=64, description="Unique client session ID")
    is_host: bool = Field(False, description="Whether this participant is the meeting host")


class ParticipantUpdate(BaseModel):
    status: Optional[str] = Field(None, description="in_meeting, left, removed")
    is_muted: Optional[bool] = Field(None, description="Audio mute status")
    is_video_on: Optional[bool] = Field(None, description="Video track status")


class ParticipantResponse(ParticipantBase):
    id: int
    meeting_id: int
    client_id: str
    join_time: datetime
    leave_time: Optional[datetime] = None
    is_host: bool
    status: str
    is_muted: bool
    is_video_on: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
