from sqlalchemy import Sequence

from app.database.base import Base

shipment_tracking_sequence = Sequence(
    "shipment_tracking_seq", metadata=Base.metadata, start=1
)
research_participant_code_sequence = Sequence(
    "research_participant_code_seq", metadata=Base.metadata, start=1
)
