from __future__ import annotations

from datetime import datetime
from typing import List, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.continuous_auth_evaluation import ContinuousAuthEvaluation
from app.models.facial_capture import FacialCapture
from app.models.experimental_session import ExperimentalSession
from app.models.session import UserSession


class ContinuousAuthRepository:
    def create(
        self,
        database: Session,
        evaluation: ContinuousAuthEvaluation,
    ) -> ContinuousAuthEvaluation:
        database.add(evaluation)
        database.flush()
        return evaluation

    def get(
        self, database: Session, evaluation_id: UUID
    ) -> ContinuousAuthEvaluation | None:
        return database.get(ContinuousAuthEvaluation, evaluation_id)

    def lock_session(
        self, database: Session, session_id: UUID
    ) -> UserSession | None:
        stmt = (
            select(UserSession)
            .where(UserSession.id == session_id)
            .with_for_update()
        )
        return database.scalar(stmt)

    def last_for_session(
        self, database: Session, session_id: UUID
    ) -> ContinuousAuthEvaluation | None:
        stmt = (
            select(ContinuousAuthEvaluation)
            .where(ContinuousAuthEvaluation.session_id == session_id)
            .order_by(ContinuousAuthEvaluation.evaluated_at.desc())
            .limit(1)
        )
        return database.scalar(stmt)

    def recent_risks(
        self,
        database: Session,
        *,
        session_id: UUID,
        since: datetime,
        reset_after: datetime | None,
        limit: int,
    ) -> List[float]:
        filters = [
            ContinuousAuthEvaluation.session_id == session_id,
            ContinuousAuthEvaluation.evaluated_at >= since,
        ]
        if reset_after:
            filters.append(ContinuousAuthEvaluation.evaluated_at > reset_after)

        stmt = (
            select(ContinuousAuthEvaluation.combined_risk)
            .where(*filters)
            .order_by(ContinuousAuthEvaluation.evaluated_at.desc())
            .limit(limit)
        )
        rows = database.scalars(stmt).all()
        return [float(r) for r in rows]

    def capture(
        self, database: Session, capture_id: UUID
    ) -> FacialCapture | None:
        return database.get(FacialCapture, capture_id)

    def experimental_session(
        self, database: Session, experimental_session_id: UUID
    ) -> ExperimentalSession | None:
        return database.get(ExperimentalSession, experimental_session_id)

    def list(
        self,
        database: Session,
        *,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
        participant_id: UUID | None = None,
        risk_level: str | None = None,
        authentication_level: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ContinuousAuthEvaluation], int]:
        filters = []
        if user_id:
            filters.append(ContinuousAuthEvaluation.user_id == user_id)
        if session_id:
            filters.append(ContinuousAuthEvaluation.session_id == session_id)
        if participant_id:
            filters.append(ContinuousAuthEvaluation.participant_id == participant_id)
        if risk_level:
            filters.append(ContinuousAuthEvaluation.risk_level == risk_level)
        if authentication_level:
            filters.append(ContinuousAuthEvaluation.authentication_level == authentication_level)
        if date_from:
            filters.append(ContinuousAuthEvaluation.evaluated_at >= date_from)
        if date_to:
            filters.append(ContinuousAuthEvaluation.evaluated_at <= date_to)

        total = (
            database.scalar(
                select(func.count()).select_from(ContinuousAuthEvaluation).where(*filters)
            )
            or 0
        )

        items = list(
            database.scalars(
                select(ContinuousAuthEvaluation)
                .where(*filters)
                .order_by(ContinuousAuthEvaluation.evaluated_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total
