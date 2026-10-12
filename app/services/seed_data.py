from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.app.models.meeting import Meeting
from backend.app.models.participant import Participant
from backend.app.services.meeting_service import generate_meeting_id, generate_invite_token


def seed_database(db: Session):
    """Populates the database with realistic sample meetings and participants if empty."""
    existing_count = db.query(Meeting).count()
    if existing_count > 0:
        return

    now = datetime.now()

    # 1. Upcoming Meeting 1: Engineering Sync in 2 hours
    m1 = Meeting(
        meeting_id="842-1920-3341",
        title="Weekly Engineering Sync (Sample)",
        description="Discuss sprint deliverables, code reviews, WebRTC architecture, and release milestones.",
        invite_token=generate_invite_token(),
        passcode="912834",
        host_display_name="Sneha Debnath (Host)",
        start_time=now + timedelta(hours=2),
        duration=45,
        status="scheduled",
        is_instant=False
    )
    db.add(m1)

    # 2. Upcoming Meeting 2: Frontend Architecture tomorrow
    m2 = Meeting(
        meeting_id="910-3849-1120",
        title="Frontend Architecture & WebRTC Review (Sample)",
        description="Deep dive into Next.js App Router, Tailwind CSS component design, and media stream handling.",
        invite_token=generate_invite_token(),
        passcode="472019",
        host_display_name="Sneha Debnath (Host)",
        start_time=now + timedelta(days=1, hours=3),
        duration=60,
        status="scheduled",
        is_instant=False
    )
    db.add(m2)

    # 3. Upcoming Meeting 3: Product Design Walkthrough in 2 days
    m3 = Meeting(
        meeting_id="704-5512-8893",
        title="UI/UX Zoom Workplace Alignment (Sample)",
        description="Verify typography, dark-mode meeting room controls, toolbars, and participant drawer parity with Zoom Workplace.",
        invite_token=generate_invite_token(),
        passcode="638210",
        host_display_name="Sneha Debnath (Host)",
        start_time=now + timedelta(days=2, hours=5),
        duration=30,
        status="scheduled",
        is_instant=False
    )
    db.add(m3)

    # 4. Recent Past Meeting 1: Ended meeting with participants
    m4 = Meeting(
        meeting_id="512-9934-7721",
        title="Sprint 14 Retrospective (Sample Past)",
        description="Team retro on completed milestones and key learnings.",
        invite_token=generate_invite_token(),
        passcode="102938",
        host_display_name="Sneha Debnath (Host)",
        start_time=now - timedelta(days=1, hours=4),
        duration=45,
        status="ended",
        is_instant=False
    )
    db.add(m4)
    db.flush()

    # Seed participants for past retro
    p1 = Participant(
        meeting_id=m4.id,
        display_name="Sneha Debnath (Host)",
        client_id="sample-host-1",
        is_host=True,
        status="left",
        join_time=m4.start_time,
        leave_time=m4.start_time + timedelta(minutes=45)
    )
    p2 = Participant(
        meeting_id=m4.id,
        display_name="Alex Rivera",
        client_id="sample-alex-2",
        is_host=False,
        status="left",
        join_time=m4.start_time + timedelta(minutes=1),
        leave_time=m4.start_time + timedelta(minutes=44)
    )
    p3 = Participant(
        meeting_id=m4.id,
        display_name="Sarah Chen",
        client_id="sample-sarah-3",
        is_host=False,
        status="left",
        join_time=m4.start_time + timedelta(minutes=2),
        leave_time=m4.start_time + timedelta(minutes=45)
    )
    db.add_all([p1, p2, p3])

    # 5. Recent Past Meeting 2: Cancelled meeting
    m5 = Meeting(
        meeting_id="663-8821-0045",
        title="Vendor Security Assessment (Sample Cancelled)",
        description="Rescheduled to next quarter due to timeline adjustments.",
        invite_token=generate_invite_token(),
        passcode="552190",
        host_display_name="Sneha Debnath (Host)",
        start_time=now - timedelta(days=3),
        duration=30,
        status="cancelled",
        is_instant=False
    )
    db.add(m5)

    db.commit()
