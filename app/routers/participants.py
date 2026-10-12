from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.participant import Participant
from backend.app.schemas.participant import ParticipantUpdate, ParticipantResponse

router = APIRouter(prefix="/participants", tags=["participants"])


@router.patch("/{participant_id}", response_model=ParticipantResponse)
def update_participant(
    participant_id: int,
    payload: ParticipantUpdate,
    db: Session = Depends(get_db)
):
    """Update participant status, mute state, or video state."""
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found."
        )

    if payload.status is not None:
        participant.status = payload.status
    if payload.is_muted is not None:
        participant.is_muted = payload.is_muted
    if payload.is_video_on is not None:
        participant.is_video_on = payload.is_video_on

    db.commit()
    db.refresh(participant)
    return participant


@router.delete("/{participant_id}", status_code=status.HTTP_200_OK)
def remove_participant(
    participant_id: int,
    db: Session = Depends(get_db)
):
    """Host control to remove a participant from the meeting."""
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found."
        )

    participant.status = "removed"
    db.commit()
    return {"message": "Participant removed from meeting", "participant_id": participant_id}
