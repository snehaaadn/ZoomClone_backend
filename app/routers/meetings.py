from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.participant import Participant
from backend.app.schemas.meeting import (
    InstantMeetingCreate,
    MeetingScheduleCreate,
    MeetingJoinRequest,
    MeetingResponse,
    MeetingValidationResponse
)
from backend.app.schemas.participant import ParticipantResponse
from backend.app.services.meeting_service import (
    MeetingService,
    build_meeting_response
)

router = APIRouter(prefix="/meetings", tags=["meetings"])


def get_base_url(request: Request) -> str:
    # Use referer or origin header if available, otherwise frontend default
    origin = request.headers.get("origin") or request.headers.get("referer")
    if origin:
        return origin.rstrip("/")
    return "http://localhost:3000"


@router.get("/upcoming", response_model=List[MeetingResponse])
def get_upcoming_meetings(request: Request, db: Session = Depends(get_db)):
    """List all scheduled and active meetings sorted chronologically."""
    meetings = MeetingService.list_upcoming_meetings(db)
    base_url = get_base_url(request)
    return [build_meeting_response(m, base_url) for m in meetings]


@router.get("/recent", response_model=List[MeetingResponse])
def get_recent_meetings(request: Request, limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """List recent meetings (ended or cancelled)."""
    meetings = MeetingService.list_recent_meetings(db, limit=limit)
    base_url = get_base_url(request)
    return [build_meeting_response(m, base_url) for m in meetings]


@router.post("/instant", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
def create_instant_meeting(
    payload: InstantMeetingCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Instantly create and launch a new Zoom meeting."""
    meeting = MeetingService.create_instant_meeting(db, payload)
    base_url = get_base_url(request)
    return build_meeting_response(meeting, base_url)


@router.post("/schedule", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
def schedule_meeting(
    payload: MeetingScheduleCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Schedule a future meeting with title, start time, and duration."""
    meeting = MeetingService.schedule_meeting(db, payload)
    base_url = get_base_url(request)
    return build_meeting_response(meeting, base_url)


@router.get("/{meeting_id}/validate", response_model=MeetingValidationResponse)
def validate_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """Validate whether a meeting ID exists and can currently be joined."""
    return MeetingService.validate_meeting(db, meeting_id)


@router.get("/{meeting_id}", response_model=MeetingResponse)
def get_meeting_details(meeting_id: str, request: Request, db: Session = Depends(get_db)):
    """Retrieve full details for a meeting by meeting ID or invite token."""
    meeting = MeetingService.get_meeting_by_identifier(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting '{meeting_id}' not found."
        )
    base_url = get_base_url(request)
    return build_meeting_response(meeting, base_url)


@router.post("/{meeting_id}/join", response_model=ParticipantResponse)
def join_meeting(
    meeting_id: str,
    payload: MeetingJoinRequest,
    db: Session = Depends(get_db)
):
    """Join a meeting with a display name and optional client ID."""
    meeting = MeetingService.get_meeting_by_identifier(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found."
        )
    if meeting.status in ["ended", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot join meeting with status '{meeting.status}'."
        )

    participant = MeetingService.join_meeting(db, meeting, payload)
    return participant


@router.post("/{meeting_id}/leave")
def leave_meeting(
    meeting_id: str,
    client_id: str = Query(..., description="Client ID of participant leaving"),
    db: Session = Depends(get_db)
):
    """Mark a participant as left from the meeting."""
    participant = MeetingService.leave_meeting(db, meeting_id, client_id)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant or meeting not found."
        )
    return {"message": "Left meeting successfully", "participant_id": participant.id}


@router.post("/{meeting_id}/end", response_model=MeetingResponse)
def end_meeting(meeting_id: str, request: Request, db: Session = Depends(get_db)):
    """End a meeting for all participants (host control)."""
    meeting = MeetingService.end_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found."
        )
    base_url = get_base_url(request)
    return build_meeting_response(meeting, base_url)


@router.post("/{meeting_id}/cancel", response_model=MeetingResponse)
def cancel_meeting(meeting_id: str, request: Request, db: Session = Depends(get_db)):
    """Cancel a scheduled meeting."""
    meeting = MeetingService.cancel_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found."
        )
    base_url = get_base_url(request)
    return build_meeting_response(meeting, base_url)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """Delete a meeting permanently from the database."""
    deleted = MeetingService.delete_meeting(db, meeting_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found."
        )
    return None


@router.get("/{meeting_id}/participants", response_model=List[ParticipantResponse])
def get_meeting_participants(
    meeting_id: str,
    active_only: bool = Query(True, description="Only return currently active participants"),
    db: Session = Depends(get_db)
):
    """Get all participants for a meeting."""
    meeting = MeetingService.get_meeting_by_identifier(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found."
        )
    
    if active_only:
        return [p for p in meeting.participants if p.status == "in_meeting"]
    return meeting.participants
