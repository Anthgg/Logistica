"""Transactional service layer for Document Series, Talonarios, and Numbering (Phase 013)."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.logistics.documents.codes.code_repository import DocumentSiteCodeRepository
from app.modules.logistics.documents.codes.domain import DocumentCodeFormatter
from app.modules.logistics.documents.repository import DocumentTypeRepository
from app.modules.logistics.documents.series.series_models import (
    DocumentNumberModel,
    DocumentSeriesModel,
    DocumentTalonarioModel,
    IdempotencyRecordModel,
    utc_now,
)
from app.modules.logistics.documents.series.series_repository import (
    DocumentNumberRepository,
    DocumentSeriesRepository,
    DocumentTalonarioRepository,
    IdempotencyRecordRepository,
)
from app.modules.logistics.documents.series.series_schemas import (
    DocumentNumberResponse,
    DocumentSeriesCreateRequest,
    DocumentSeriesResponse,
    DocumentTalonarioCreateRequest,
    DocumentTalonarioManifestResponse,
    DocumentTalonarioResponse,
)


class DocumentSeriesExhaustedError(HTTPException):
    def __init__(self, detail: str = "Document series sequence exhausted (999999)"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class IdempotencyConflictError(HTTPException):
    def __init__(self, detail: str = "Idempotency key reused with different request payload"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class DocumentSeriesService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.series_repo = DocumentSeriesRepository(db)
        self.talonario_repo = DocumentTalonarioRepository(db)
        self.number_repo = DocumentNumberRepository(db)
        self.site_repo = DocumentSiteCodeRepository(db)
        self.type_repo = DocumentTypeRepository(db)
        self.idem_repo = IdempotencyRecordRepository(db)

    def _check_idempotency(
        self, organization_id: UUID, operation: str, idempotency_key: str | None, payload: dict
    ) -> dict | None:
        if not idempotency_key:
            return None
        req_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        rec = self.idem_repo.get_record(organization_id, operation, idempotency_key)
        if rec:
            if rec.request_hash != req_hash:
                raise IdempotencyConflictError()
            return rec.response_payload
        return None

    def _record_idempotency(
        self, organization_id: UUID, operation: str, idempotency_key: str | None, payload: dict, response: dict, user_id: UUID | None
    ) -> None:
        if not idempotency_key:
            return
        req_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        clean_response = json.loads(json.dumps(response, default=str)) if response else None
        rec = IdempotencyRecordModel(
            organization_id=organization_id,
            user_id=user_id,
            operation=operation,
            idempotency_key=idempotency_key,
            request_hash=req_hash,
            response_payload=clean_response,
            status="COMPLETED",
        )
        self.idem_repo.save(rec)

    def create_series(
        self, organization_id: UUID, req: DocumentSeriesCreateRequest, actor_id: UUID | None = None
    ) -> DocumentSeriesResponse:
        cached = self._check_idempotency(organization_id, "CREATE_SERIES", req.idempotency_key, req.model_dump())
        if cached:
            return DocumentSeriesResponse.model_validate(cached)

        doc_type = self.type_repo.get_by_code(req.document_type_code.upper())
        if not doc_type:
            raise HTTPException(status_code=404, detail=f"DocumentType '{req.document_type_code}' not found")

        site_code_obj = self.site_repo.get_primary_by_branch(req.branch_id)
        site_str = site_code_obj.code if site_code_obj else "LIM"

        existing = self.series_repo.get_by_scope(
            organization_id=organization_id,
            document_type_id=doc_type.id,
            document_site_code_id=site_code_obj.id if site_code_obj else req.branch_id,
            document_year=req.document_year,
        )
        if existing:
            return DocumentSeriesResponse.model_validate(existing)

        prefix = f"{doc_type.code}-{site_str}-{req.document_year}"

        series = DocumentSeriesModel(
            organization_id=organization_id,
            branch_id=req.branch_id,
            document_site_code_id=site_code_obj.id if site_code_obj else req.branch_id,
            document_type_id=doc_type.id,
            document_year=req.document_year,
            prefix=prefix,
            sequence_start=req.sequence_start,
            next_sequence=req.sequence_start,
            sequence_max=req.sequence_max,
            status="DRAFT",
            opened_by=actor_id,
        )
        self.series_repo.save(series)
        resp = DocumentSeriesResponse.model_validate(series)
        self._record_idempotency(organization_id, "CREATE_SERIES", req.idempotency_key, req.model_dump(), resp.model_dump(), actor_id)
        self.db.commit()
        return resp

    def activate_series(self, series_id: UUID, reason: str, actor_id: UUID | None = None) -> DocumentSeriesResponse:
        series = self.series_repo.get_for_update(series_id)
        if not series:
            raise HTTPException(status_code=404, detail="DocumentSeries not found")
        series.status = "ACTIVE"
        series.opened_at = utc_now()
        series.opened_by = actor_id
        self.series_repo.save(series)
        self.db.commit()
        return DocumentSeriesResponse.model_validate(series)

    def suspend_series(self, series_id: UUID, reason: str, actor_id: UUID | None = None) -> DocumentSeriesResponse:
        series = self.series_repo.get_for_update(series_id)
        if not series:
            raise HTTPException(status_code=404, detail="DocumentSeries not found")
        series.status = "SUSPENDED"
        self.series_repo.save(series)
        self.db.commit()
        return DocumentSeriesResponse.model_validate(series)

    def close_series(self, series_id: UUID, reason: str, actor_id: UUID | None = None) -> DocumentSeriesResponse:
        series = self.series_repo.get_for_update(series_id)
        if not series:
            raise HTTPException(status_code=404, detail="DocumentSeries not found")
        series.status = "CLOSED"
        series.closed_at = utc_now()
        series.closed_by = actor_id
        series.close_reason = reason
        self.series_repo.save(series)
        self.db.commit()
        return DocumentSeriesResponse.model_validate(series)

    def reserve_next_number(
        self,
        series_id: UUID,
        purpose: str = "Document issuance",
        actor_id: UUID | None = None,
        idempotency_key: str | None = None,
    ) -> DocumentNumberResponse:
        """Internal transactional service to reserve the next atomic sequence number."""
        series = self.series_repo.get_for_update(series_id)
        if not series:
            raise HTTPException(status_code=404, detail="DocumentSeries not found")
        if series.status != "ACTIVE":
            raise HTTPException(status_code=400, detail=f"Cannot reserve from series in status '{series.status}'")
        if series.next_sequence > series.sequence_max:
            series.status = "EXHAUSTED"
            series.exhausted_at = utc_now()
            self.series_repo.save(series)
            self.db.commit()
            raise DocumentSeriesExhaustedError()

        seq_num = series.next_sequence
        series.next_sequence += 1
        if series.next_sequence > series.sequence_max:
            series.status = "EXHAUSTED"
            series.exhausted_at = utc_now()

        self.series_repo.save(series)

        site_code = series.prefix.split("-")[1]
        doc_type_code = series.prefix.split("-")[0]
        full_code = DocumentCodeFormatter.format(doc_type_code, site_code, series.document_year, seq_num)

        num_obj = DocumentNumberModel(
            organization_id=series.organization_id,
            series_id=series.id,
            sequence_number=seq_num,
            full_document_code=full_code,
            status="RESERVED",
            reservation_type="INDIVIDUAL",
            reservation_purpose=purpose,
            reserved_by=actor_id,
            idempotency_key=idempotency_key,
        )
        self.number_repo.save(num_obj)
        self.db.commit()
        return DocumentNumberResponse.model_validate(num_obj)

    def reserve_number_range(
        self,
        series_id: UUID,
        req: DocumentTalonarioCreateRequest,
        actor_id: UUID | None = None,
    ) -> DocumentTalonarioResponse:
        series = self.series_repo.get_for_update(series_id)
        if not series:
            raise HTTPException(status_code=404, detail="DocumentSeries not found")

        cached = self._check_idempotency(series.organization_id, "RESERVE_RANGE", req.idempotency_key, req.model_dump())
        if cached:
            return DocumentTalonarioResponse.model_validate(cached)

        if series.status != "ACTIVE":
            raise HTTPException(status_code=400, detail=f"Cannot reserve range from series in status '{series.status}'")

        if series.next_sequence + req.quantity - 1 > series.sequence_max:
            raise HTTPException(
                status_code=409,
                detail=f"Requested range ({req.quantity}) exceeds series maximum sequence limit ({series.sequence_max})",
            )

        range_start = series.next_sequence
        range_end = range_start + req.quantity - 1
        series.next_sequence = range_end + 1

        if series.next_sequence > series.sequence_max:
            series.status = "EXHAUSTED"
            series.exhausted_at = utc_now()

        self.series_repo.save(series)

        tal_code = f"TAL-{series.prefix}-{range_start:06d}-{range_end:06d}"

        talonario = DocumentTalonarioModel(
            organization_id=series.organization_id,
            series_id=series.id,
            talonario_code=tal_code,
            range_start=range_start,
            range_end=range_end,
            total_numbers=req.quantity,
            reserved_numbers=req.quantity,
            available_numbers=req.quantity,
            status="RESERVED",
            purpose=req.purpose,
            requested_by=actor_id,
            idempotency_key=req.idempotency_key,
        )
        self.talonario_repo.save(talonario)

        site_code = series.prefix.split("-")[1]
        doc_type_code = series.prefix.split("-")[0]

        numbers_to_insert: list[DocumentNumberModel] = []
        for seq in range(range_start, range_end + 1):
            fcode = DocumentCodeFormatter.format(doc_type_code, site_code, series.document_year, seq)
            numbers_to_insert.append(
                DocumentNumberModel(
                    organization_id=series.organization_id,
                    series_id=series.id,
                    talonario_id=talonario.id,
                    sequence_number=seq,
                    full_document_code=fcode,
                    status="RESERVED",
                    reservation_type="TALONARIO",
                    reservation_purpose=req.purpose,
                    reserved_by=actor_id,
                )
            )

        self.number_repo.save_all(numbers_to_insert)
        resp = DocumentTalonarioResponse.model_validate(talonario)

        self._record_idempotency(
            series.organization_id, "RESERVE_RANGE", req.idempotency_key, req.model_dump(), resp.model_dump(), actor_id
        )
        self.db.commit()
        return resp

    def cancel_talonario(
        self, talonario_id: UUID, reason: str, actor_id: UUID | None = None
    ) -> DocumentTalonarioResponse:
        talonario = self.talonario_repo.get_for_update(talonario_id)
        if not talonario:
            raise HTTPException(status_code=404, detail="DocumentTalonario not found")

        if talonario.status in ("CANCELLED", "CLOSED"):
            return DocumentTalonarioResponse.model_validate(talonario)

        talonario.status = "CANCELLED"
        talonario.cancelled_at = utc_now()
        talonario.cancel_reason = reason

        numbers = self.number_repo.list_by_talonario(talonario_id)
        voided_count = 0
        for num in numbers:
            if num.status == "RESERVED":
                num.status = "VOIDED"
                num.voided_at = utc_now()
                num.voided_by = actor_id
                num.void_reason = f"Talonario cancelado: {reason}"
                self.number_repo.save(num)
                voided_count += 1

        talonario.voided_numbers = voided_count
        talonario.available_numbers = 0
        self.talonario_repo.save(talonario)
        self.db.commit()
        return DocumentTalonarioResponse.model_validate(talonario)

    def generate_manifest(self, talonario_id: UUID) -> DocumentTalonarioManifestResponse:
        talonario = self.talonario_repo.get_by_id(talonario_id)
        if not talonario:
            raise HTTPException(status_code=404, detail="DocumentTalonario not found")
        series = self.series_repo.get_by_id(talonario.series_id)
        numbers = self.number_repo.list_by_talonario(talonario_id)

        num_responses = [DocumentNumberResponse.model_validate(n) for n in numbers]

        return DocumentTalonarioManifestResponse(
            manifest_version="1.0.0",
            talonario_id=talonario.id,
            talonario_code=talonario.talonario_code,
            organization_id=talonario.organization_id,
            prefix=series.prefix if series else "",
            range_start=talonario.range_start,
            range_end=talonario.range_end,
            total_numbers=talonario.total_numbers,
            status=talonario.status,
            reserved_at=talonario.reserved_at,
            numbers=num_responses,
            rendering_status="PENDING_RENDERER_PHASE_014",
        )
