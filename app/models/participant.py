import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    display_name = Column(String(128), nullable=False)
    client_id = Column(String(64), nullable=False, index=True)
    join_time = Column(DateTime, nullable=False, default=func.now())
    leave_time = Column(DateTime, nullable=True)
    is_host = Column(Boolean, nullable=False, default=False)
    status = Column(String(32), nullable=False, default="in_meeting")  # in_meeting, left, removed
    is_muted = Column(Boolean, nullable=False, default=False)
    is_video_on = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())

    meeting = relationship("Meeting", back_populates="participants")

    def __repr__(self):
        return f"<Participant(id={self.id}, display_name='{self.display_name}', meeting_id={self.meeting_id})>"
