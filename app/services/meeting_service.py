import secrets
import random
import re
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from backend.app.models.meeting import Meeting
from backend.app.models.participant import Participant
from backend.app.schemas.meeting import (
    InstantMeetingCreate,
    MeetingScheduleCreate,
    MeetingUpdate,
    MeetingJoinRequest,
    MeetingResponse,
    MeetingValidationResponse,
)
from backend.app.config import settings


def generate_meeting_id() -> str:
    """Generates a standard 10-digit Zoom-style meeting ID: XXX-XXXX-XXXX."""
    p1 = random.randint(100, 999)
    p2 = random.randint(1000, 9999)
    p3 = random.randint(1000, 9999)
    return f"{p1}-{p2}-{p3}"


def normalize_meeting_id(raw_id: str) -> str:
    """Strips dashes, spaces, and non-alphanumeric characters for clean comparison."""
    if not raw_id:
        return ""
    return re.sub(r"[^a-zA-Z0-9]", "", raw_id)


def generate_invite_token() -> str:
    return secrets.token_urlsafe(16)


def generate_passcode() -> str:
    return f"{random.randint(100000, 999999)}"


def is_host_name_match(name1: Optional[str], name2: Optional[str]) -> bool:
    """Robust comparison between host names ignoring case and (Host) suffixes."""
    if not name1 or not name2:
        return False
    clean1 = re.sub(r"\s*\(.*?\)\s*", "", name1).strip().lower()
    clean2 = re.sub(r"\s*\(.*?\)\s*", "", name2).strip().lower()
    return clean1 == clean2 and bool(clean1)


def build_meeting_response(meeting: Meeting, base_url: str = "http://localhost:3000") -> MeetingResponse:
    """Converts a Meeting model into a fully-populated MeetingResponse schema."""
    invite_url = f"{base_url}/meeting/{meeting.meeting_id}?pwd={meeting.passcode}"
    
    # Filter active participants count
    active_participants = [p for p in meeting.participants if p.status == "in_meeting"]
    
    return MeetingResponse(
        id=meeting.id,
        meeting_id=meeting.meeting_id,
        title=meeting.title,
        description=meeting.description,
        invite_token=meeting.invite_token,
        invite_url=invite_url,
        passcode=meeting.passcode,
        host_display_name=meeting.host_display_name,
        start_time=meeting.start_time,
        duration=meeting.duration,
        status=meeting.status,
        is_instant=meeting.is_instant,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
        participant_count=len(active_participants),
        participants=meeting.participants
    )


class MeetingService:
    @staticmethod
    def get_meeting_by_identifier(db: Session, identifier: str) -> Optional[Meeting]:
        """Looks up meeting by meeting_id (formatted or raw), numeric id, or invite_token."""
        if not identifier:
            return None
        clean_id = identifier.strip()
        if not clean_id:
            return None
        normalized = normalize_meeting_id(clean_id)
        
        # Try exact match on meeting_id, invite_token, or integer id
        meeting = db.query(Meeting).filter(
            or_(
                Meeting.meeting_id == clean_id,
                Meeting.invite_token == clean_id
            )
        ).first()
        
        if meeting:
            return meeting
            
        # Try matching normalized meeting_id
        all_meetings = db.query(Meeting).all()
        for m in all_meetings:
            if normalized and normalize_meeting_id(m.meeting_id) == normalized:
                return m
            if m.invite_token == clean_id:
                return m
            if clean_id.isdigit() and m.id == int(clean_id):
                return m
                
        return None

    @staticmethod
    def create_instant_meeting(db: Session, data: InstantMeetingCreate) -> Meeting:
        host_name = data.host_display_name or settings.DEFAULT_USER_NAME
        title = data.title or f"{host_name}'s Meeting"
        passcode = data.passcode or generate_passcode()
        
        meeting = Meeting(
            meeting_id=generate_meeting_id(),
            title=title,
            description="Instant Zoom Meeting started from dashboard.",
            invite_token=generate_invite_token(),
            passcode=passcode,
            host_display_name=host_name,
            start_time=datetime.now(),
            duration=45,
            status="active",
            is_instant=True
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        # Register host placeholder participant that gets bound when browser joins
        host_participant = Participant(
            meeting_id=meeting.id,
            display_name=host_name,
            client_id=f"host-{secrets.token_hex(4)}",
            is_host=True,
            status="in_meeting"
        )
        db.add(host_participant)
        db.commit()
        db.refresh(meeting)
        return meeting

    @staticmethod
    def schedule_meeting(db: Session, data: MeetingScheduleCreate) -> Meeting:
        host_name = data.host_display_name or settings.DEFAULT_USER_NAME
        passcode = data.passcode or generate_passcode()
        
        # Ensure start_time has no tzinfo issues in SQLite
        start_dt = data.start_time
        if start_dt.tzinfo is not None:
            start_dt = start_dt.astimezone(timezone.utc).replace(tzinfo=None)

        meeting = Meeting(
            meeting_id=generate_meeting_id(),
            title=data.title,
            description=data.description,
            invite_token=generate_invite_token(),
            passcode=passcode,
            host_display_name=host_name,
            start_time=start_dt,
            duration=data.duration,
            status="scheduled",
            is_instant=False
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)
        return meeting

    @staticmethod
    def list_upcoming_meetings(db: Session) -> List[Meeting]:
        """Returns meetings that are scheduled or currently active."""
        return (
            db.query(Meeting)
            .filter(Meeting.status.in_(["scheduled", "active"]))
            .order_by(asc(Meeting.start_time))
            .all()
        )

    @staticmethod
    def list_recent_meetings(db: Session, limit: int = 20) -> List[Meeting]:
        """Returns meetings that have ended, were cancelled, or past instant meetings."""
        return (
            db.query(Meeting)
            .filter(Meeting.status.in_(["ended", "cancelled"]))
            .order_by(desc(Meeting.updated_at))
            .limit(limit)
            .all()
        )

    @staticmethod
    def validate_meeting(db: Session, identifier: str) -> MeetingValidationResponse:
        meeting = MeetingService.get_meeting_by_identifier(db, identifier)
        if not meeting:
            return MeetingValidationResponse(
                exists=False,
                is_valid=False,
                message="Meeting ID not found. Please verify the ID or invite link."
            )
            
        if meeting.status == "ended":
            return MeetingValidationResponse(
                exists=True,
                is_valid=False,
                meeting_id=meeting.meeting_id,
                title=meeting.title,
                status=meeting.status,
                host_display_name=meeting.host_display_name,
                start_time=meeting.start_time,
                duration=meeting.duration,
                message="This meeting has ended by the host."
            )
            
        if meeting.status == "cancelled":
            return MeetingValidationResponse(
                exists=True,
                is_valid=False,
                meeting_id=meeting.meeting_id,
                title=meeting.title,
                status=meeting.status,
                host_display_name=meeting.host_display_name,
                start_time=meeting.start_time,
                duration=meeting.duration,
                message="This scheduled meeting was cancelled."
            )
            
        return MeetingValidationResponse(
            exists=True,
            is_valid=True,
            meeting_id=meeting.meeting_id,
            title=meeting.title,
            status=meeting.status,
            host_display_name=meeting.host_display_name,
            start_time=meeting.start_time,
            duration=meeting.duration,
            message="Meeting is valid and ready to join."
        )

    @staticmethod
    def join_meeting(db: Session, meeting: Meeting, request: MeetingJoinRequest) -> Participant:
        client_id = request.client_id or f"client-{secrets.token_hex(6)}"
        
        # If the meeting was scheduled, activate it upon joining
        if meeting.status == "scheduled":
            meeting.status = "active"
            db.add(meeting)

        # Determine host status: guests explicitly sending is_host=False never get host privileges
        if request.is_host is not None:
            is_host = bool(request.is_host and is_host_name_match(request.display_name, meeting.host_display_name))
        else:
            is_host = is_host_name_match(request.display_name, meeting.host_display_name)

        # Check if participant with this client_id is already in meeting
        existing = db.query(Participant).filter(
            Participant.meeting_id == meeting.id,
            Participant.client_id == client_id
        ).first()

        if existing:
            existing.status = "in_meeting"
            existing.display_name = request.display_name
            existing.is_host = is_host or existing.is_host
            existing.leave_time = None
            db.commit()
            db.refresh(existing)
            return existing

        # If user is the host, check if an unattached host placeholder participant exists
        if is_host:
            unattached_host = db.query(Participant).filter(
                Participant.meeting_id == meeting.id,
                Participant.is_host == True,
                Participant.client_id.like("host-%")
            ).first()
            if unattached_host:
                unattached_host.client_id = client_id
                unattached_host.display_name = request.display_name
                unattached_host.status = "in_meeting"
                unattached_host.leave_time = None
                db.commit()
                db.refresh(unattached_host)
                return unattached_host

        participant = Participant(
            meeting_id=meeting.id,
            display_name=request.display_name,
            client_id=client_id,
            is_host=is_host,
            status="in_meeting"
        )
        db.add(participant)
        db.commit()
        db.refresh(participant)
        return participant

    @staticmethod
    def leave_meeting(db: Session, meeting_id: str, client_id: str) -> Optional[Participant]:
        meeting = MeetingService.get_meeting_by_identifier(db, meeting_id)
        if not meeting:
            return None
            
        participant = db.query(Participant).filter(
            Participant.meeting_id == meeting.id,
            Participant.client_id == client_id
        ).first()
        
        if participant:
            participant.status = "left"
            participant.leave_time = datetime.now()
            db.commit()
            db.refresh(participant)
            
        return participant

    @staticmethod
    def end_meeting(db: Session, meeting_id: str) -> Optional[Meeting]:
        meeting = MeetingService.get_meeting_by_identifier(db, meeting_id)
        if not meeting:
            return None
            
        meeting.status = "ended"
        for p in meeting.participants:
            if p.status == "in_meeting":
                p.status = "left"
                p.leave_time = datetime.now()
                
        db.commit()
        db.refresh(meeting)
        return meeting

    @staticmethod
    def cancel_meeting(db: Session, meeting_id: str) -> Optional[Meeting]:
        meeting = MeetingService.get_meeting_by_identifier(db, meeting_id)
        if not meeting:
            return None
            
        meeting.status = "cancelled"
        db.commit()
        db.refresh(meeting)
        return meeting

    @staticmethod
    def delete_meeting(db: Session, meeting_id: str) -> bool:
        meeting = MeetingService.get_meeting_by_identifier(db, meeting_id)
        if not meeting:
            return False
            
        db.delete(meeting)
        db.commit()
        return True
