import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, func
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(String(32), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    invite_token = Column(String(64), unique=True, index=True, nullable=False)
    passcode = Column(String(16), nullable=False, default="123456")
    host_display_name = Column(String(128), nullable=False)
    start_time = Column(DateTime, nullable=False, default=func.now())
    duration = Column(Integer, nullable=False, default=30)  # duration in minutes
    status = Column(String(32), nullable=False, default="scheduled")  # scheduled, active, ended, cancelled
    is_instant = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    participants = relationship(
        "Participant",
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="Participant.join_time.asc()"
    )

    def __repr__(self):
        return f"<Meeting(id={self.id}, meeting_id='{self.meeting_id}', title='{self.title}', status='{self.status}')>"
