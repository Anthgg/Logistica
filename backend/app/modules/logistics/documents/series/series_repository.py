"""Repository classes for Document Series, Talonarios, Numbers, and Idempotency (Phase 013)."""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.documents.series.series_models import (
    DocumentNumberModel,
    DocumentSeriesModel,
    DocumentTalonarioModel,
    IdempotencyRecordModel,
)


class DocumentSeriesRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, series_id: UUID) -> DocumentSeriesModel | None:
        return self.db.scalars(
            select(DocumentSeriesModel).where(DocumentSeriesModel.id == series_id)
        ).first()

    def get_for_update(self, series_id: UUID) -> DocumentSeriesModel | None:
        """Retrieves DocumentSeries with a row-level SELECT FOR UPDATE lock."""
        return self.db.scalars(
            select(DocumentSeriesModel)
            .where(DocumentSeriesModel.id == series_id)
            .with_for_update()
        ).first()

    def get_by_scope(
        self,
        organization_id: UUID,
        document_type_id: UUID,
        document_site_code_id: UUID,
        document_year: int,
    ) -> DocumentSeriesModel | None:
        return self.db.scalars(
            select(DocumentSeriesModel).where(
                DocumentSeriesModel.organization_id == organization_id,
                DocumentSeriesModel.document_type_id == document_type_id,
                DocumentSeriesModel.document_site_code_id == document_site_code_id,
                DocumentSeriesModel.document_year == document_year,
            )
        ).first()

    def list(
        self,
        organization_id: UUID,
        status: str | None = None,
        branch_id: UUID | None = None,
        document_year: int | None = None,
    ) -> Sequence[DocumentSeriesModel]:
        stmt = select(DocumentSeriesModel).where(DocumentSeriesModel.organization_id == organization_id)
        if status:
            stmt = stmt.where(DocumentSeriesModel.status == status)
        if branch_id:
            stmt = stmt.where(DocumentSeriesModel.branch_id == branch_id)
        if document_year:
            stmt = stmt.where(DocumentSeriesModel.document_year == document_year)
        return self.db.scalars(stmt.order_by(DocumentSeriesModel.prefix.asc())).all()

    def save(self, series: DocumentSeriesModel) -> DocumentSeriesModel:
        self.db.add(series)
        self.db.flush()
        return series


class DocumentTalonarioRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, talonario_id: UUID) -> DocumentTalonarioModel | None:
        return self.db.scalars(
            select(DocumentTalonarioModel).where(DocumentTalonarioModel.id == talonario_id)
        ).first()

    def get_for_update(self, talonario_id: UUID) -> DocumentTalonarioModel | None:
        return self.db.scalars(
            select(DocumentTalonarioModel)
            .where(DocumentTalonarioModel.id == talonario_id)
            .with_for_update()
        ).first()

    def list_by_series(self, series_id: UUID) -> Sequence[DocumentTalonarioModel]:
        return self.db.scalars(
            select(DocumentTalonarioModel)
            .where(DocumentTalonarioModel.series_id == series_id)
            .order_by(DocumentTalonarioModel.range_start.asc())
        ).all()

    def save(self, talonario: DocumentTalonarioModel) -> DocumentTalonarioModel:
        self.db.add(talonario)
        self.db.flush()
        return talonario


class DocumentNumberRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, number_id: UUID) -> DocumentNumberModel | None:
        return self.db.scalars(
            select(DocumentNumberModel).where(DocumentNumberModel.id == number_id)
        ).first()

    def get_by_code(self, organization_id: UUID, full_code: str) -> DocumentNumberModel | None:
        return self.db.scalars(
            select(DocumentNumberModel).where(
                DocumentNumberModel.organization_id == organization_id,
                DocumentNumberModel.full_document_code == full_code,
            )
        ).first()

    def list_by_series(
        self,
        series_id: UUID,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[DocumentNumberModel]:
        stmt = select(DocumentNumberModel).where(DocumentNumberModel.series_id == series_id)
        if status:
            stmt = stmt.where(DocumentNumberModel.status == status)
        stmt = stmt.order_by(DocumentNumberModel.sequence_number.asc()).offset(offset).limit(limit)
        return self.db.scalars(stmt).all()

    def list_by_talonario(self, talonario_id: UUID) -> Sequence[DocumentNumberModel]:
        return self.db.scalars(
            select(DocumentNumberModel)
            .where(DocumentNumberModel.talonario_id == talonario_id)
            .order_by(DocumentNumberModel.sequence_number.asc())
        ).all()

    def save(self, number: DocumentNumberModel) -> DocumentNumberModel:
        self.db.add(number)
        self.db.flush()
        return number

    def save_all(self, numbers: list[DocumentNumberModel]) -> None:
        self.db.add_all(numbers)
        self.db.flush()


class IdempotencyRecordRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_record(
        self, organization_id: UUID, operation: str, idempotency_key: str
    ) -> IdempotencyRecordModel | None:
        return self.db.scalars(
            select(IdempotencyRecordModel).where(
                IdempotencyRecordModel.organization_id == organization_id,
                IdempotencyRecordModel.operation == operation,
                IdempotencyRecordModel.idempotency_key == idempotency_key,
            )
        ).first()

    def save(self, rec: IdempotencyRecordModel) -> IdempotencyRecordModel:
        self.db.add(rec)
        self.db.flush()
        return rec
