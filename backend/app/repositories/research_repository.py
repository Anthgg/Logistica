from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.behavioral_batch import BehavioralBatch
from app.models.consent_record import ConsentRecord
from app.models.experimental_session import ExperimentalSession
from app.models.facial_capture import FacialCapture
from app.models.research_participant import ResearchParticipant


class ResearchRepository:
    def list_participants(
        self,
        database: Session,
        *,
        page: int,
        page_size: int,
        is_active: bool | None,
    ) -> tuple[list[ResearchParticipant], int]:
        filters = []
        if is_active is not None:
            filters.append(ResearchParticipant.is_active == is_active)
        total = database.scalar(
            select(func.count()).select_from(ResearchParticipant).where(*filters)
        ) or 0
        items = list(
            database.scalars(
                select(ResearchParticipant)
                .where(*filters)
                .order_by(ResearchParticipant.enrollment_date.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def get_participant(
        self, database: Session, participant_id: UUID
    ) -> ResearchParticipant | None:
        return database.get(ResearchParticipant, participant_id)

    def participant_for_user(
        self, database: Session, user_id: UUID
    ) -> ResearchParticipant | None:
        return database.scalar(
            select(ResearchParticipant)
            .where(ResearchParticipant.linked_user_id == user_id)
            .order_by(ResearchParticipant.enrollment_date.desc())
        )

    def current_consent(
        self, database: Session, participant_id: UUID
    ) -> ConsentRecord | None:
        return database.scalar(
            select(ConsentRecord)
            .where(
                ConsentRecord.participant_id == participant_id,
                ConsentRecord.accepted.is_(True),
                ConsentRecord.withdrawn_at.is_(None),
            )
            .order_by(ConsentRecord.accepted_at.desc())
        )

    def active_session(
        self, database: Session, participant_id: UUID
    ) -> ExperimentalSession | None:
        return database.scalar(
            select(ExperimentalSession).where(
                ExperimentalSession.participant_id == participant_id,
                ExperimentalSession.status == "active",
            )
        )

    def active_session_count_for_user(self, database: Session, user_id: UUID) -> int:
        return (
            database.scalar(
                select(func.count())
                .select_from(ExperimentalSession)
                .where(
                    ExperimentalSession.user_id == user_id,
                    ExperimentalSession.status == "active",
                )
            )
            or 0
        )

    def get_session(
        self, database: Session, session_id: UUID, *, lock: bool = False
    ) -> ExperimentalSession | None:
        statement = select(ExperimentalSession).where(
            ExperimentalSession.id == session_id
        )
        if lock:
            statement = statement.with_for_update()
        return database.scalar(statement)

    def capture_by_sequence(
        self, database: Session, session_id: UUID, sequence_number: int
    ) -> FacialCapture | None:
        return database.scalar(
            select(FacialCapture).where(
                FacialCapture.experimental_session_id == session_id,
                FacialCapture.sequence_number == sequence_number,
            )
        )

    def batch_by_id(
        self, database: Session, batch_id: UUID
    ) -> BehavioralBatch | None:
        return database.scalar(
            select(BehavioralBatch).where(BehavioralBatch.batch_id == batch_id)
        )

    def batch_by_sequence(
        self, database: Session, session_id: UUID, sequence_number: int
    ) -> BehavioralBatch | None:
        return database.scalar(
            select(BehavioralBatch).where(
                BehavioralBatch.experimental_session_id == session_id,
                BehavioralBatch.sequence_number == sequence_number,
            )
        )

    def session_counts(
        self, database: Session, session_id: UUID
    ) -> tuple[int, int, int, int]:
        capture_count = database.scalar(
            select(func.count())
            .select_from(FacialCapture)
            .where(FacialCapture.experimental_session_id == session_id)
        ) or 0
        row = database.execute(
            select(
                func.count(BehavioralBatch.id),
                func.coalesce(func.sum(BehavioralBatch.keyboard_event_count), 0),
                func.coalesce(func.sum(BehavioralBatch.mouse_event_count), 0),
            ).where(BehavioralBatch.experimental_session_id == session_id)
        ).one()
        return capture_count, int(row[0]), int(row[1]), int(row[2])

    def list_sessions(
        self,
        database: Session,
        *,
        page: int,
        page_size: int,
        participant_id: UUID | None,
        status: str | None,
        scenario: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> tuple[list[ExperimentalSession], int]:
        filters = []
        if participant_id:
            filters.append(ExperimentalSession.participant_id == participant_id)
        if status:
            filters.append(ExperimentalSession.status == status)
        if scenario:
            filters.append(ExperimentalSession.scenario == scenario)
        if date_from:
            filters.append(ExperimentalSession.started_at >= date_from)
        if date_to:
            filters.append(ExperimentalSession.started_at <= date_to)
        total = database.scalar(
            select(func.count()).select_from(ExperimentalSession).where(*filters)
        ) or 0
        sessions = list(
            database.scalars(
                select(ExperimentalSession)
                .where(*filters)
                .order_by(ExperimentalSession.started_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return sessions, total
