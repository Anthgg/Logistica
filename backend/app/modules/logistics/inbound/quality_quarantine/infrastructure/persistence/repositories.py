"""Phase 042 — Repositories for quality quarantine module."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.models import (
    InboundInventoryDispositionAllocationModel,
    InventoryDispositionSplitModel,
    InboundQualityAvailabilityProjectionModel,
    QualityCertificateReviewModel,
    QualityDecisionApprovalModel,
    QualityDispositionDecisionModel,
    QualityDispositionEventModel,
    QualityInspectionControlModel,
    QualityInspectionControlResultModel,
    QualityInspectionEvidenceLinkModel,
    QualityInspectionModel,
    QualityInspectionSampleReferenceModel,
    QualityInspectionSampleSetModel,
    QualityInspectionSnapshotModel,
    QualityMeasurementModel,
    QualityQuarantineCaseModel,
    QualityQuarantineCaseRevisionModel,
    QualityReinspectionRequestModel,
    QuarantinePlacementConfirmationModel,
    QuarantineReleaseAuthorizationModel,
    QuarantineRejectionAuthorizationModel,
    QuarantineZoneConfigurationModel,
)


class AllocationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, allocation_id: UUID) -> InboundInventoryDispositionAllocationModel | None:
        return self._db.get(InboundInventoryDispositionAllocationModel, allocation_id)

    def get_by_received_line(
        self, receipt_id: UUID, received_line_id: UUID
    ) -> InboundInventoryDispositionAllocationModel | None:
        return (
            self._db.execute(
                select(InboundInventoryDispositionAllocationModel).where(
                    InboundInventoryDispositionAllocationModel.inbound_receipt_id == receipt_id,
                    InboundInventoryDispositionAllocationModel.inbound_received_line_id == received_line_id,
                    InboundInventoryDispositionAllocationModel.allocation_status != "SUPERSEDED",
                )
            )
            .scalars()
            .first()
        )

    def list_by_receipt(self, receipt_id: UUID) -> list[InboundInventoryDispositionAllocationModel]:
        return (
            self._db.execute(
                select(InboundInventoryDispositionAllocationModel)
                .where(InboundInventoryDispositionAllocationModel.inbound_receipt_id == receipt_id)
                .order_by(InboundInventoryDispositionAllocationModel.created_at)
            )
            .scalars()
            .all()
        )

    def list_by_warehouse(
        self, organization_id: UUID, warehouse_id: UUID
    ) -> list[InboundInventoryDispositionAllocationModel]:
        return (
            self._db.execute(
                select(InboundInventoryDispositionAllocationModel).where(
                    InboundInventoryDispositionAllocationModel.organization_id == organization_id,
                    InboundInventoryDispositionAllocationModel.warehouse_id == warehouse_id,
                )
            )
            .scalars()
            .all()
        )

    def create(self, model: InboundInventoryDispositionAllocationModel) -> InboundInventoryDispositionAllocationModel:
        self._db.add(model)
        self._db.flush()
        return model

    def update_status(
        self, allocation_id: UUID, *, status: str, availability_class: str, quality_status: str
    ) -> None:
        self._db.execute(
            update(InboundInventoryDispositionAllocationModel)
            .where(InboundInventoryDispositionAllocationModel.id == allocation_id)
            .values(
                allocation_status=status,
                availability_class=availability_class,
                quality_status=quality_status,
            )
        )
        self._db.flush()

    def count_active_by_line(self, receipt_id: UUID, received_line_id: UUID) -> int:
        result = self._db.execute(
            select(func.count()).select_from(InboundInventoryDispositionAllocationModel).where(
                InboundInventoryDispositionAllocationModel.inbound_receipt_id == receipt_id,
                InboundInventoryDispositionAllocationModel.inbound_received_line_id == received_line_id,
                InboundInventoryDispositionAllocationModel.allocation_status.notin_(
                    ["SUPERSEDED", "SUPERSEDED_BY_SPLIT", "CANCELLED"]
                ),
            )
        )
        return result.scalar() or 0


class QuarantineCaseRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, case_id: UUID) -> QualityQuarantineCaseModel | None:
        return self._db.get(QualityQuarantineCaseModel, case_id)

    def get_by_allocation(self, allocation_id: UUID) -> QualityQuarantineCaseModel | None:
        return (
            self._db.execute(
                select(QualityQuarantineCaseModel).where(
                    QualityQuarantineCaseModel.id == allocation_id
                )
            )
            .scalars()
            .first()
        )

    def list_by_warehouse(
        self, organization_id: UUID, warehouse_id: UUID
    ) -> list[QualityQuarantineCaseModel]:
        return (
            self._db.execute(
                select(QualityQuarantineCaseModel).where(
                    QualityQuarantineCaseModel.organization_id == organization_id,
                    QualityQuarantineCaseModel.warehouse_id == warehouse_id,
                )
            )
            .scalars()
            .all()
        )

    def create(self, model: QualityQuarantineCaseModel) -> QualityQuarantineCaseModel:
        self._db.add(model)
        self._db.flush()
        return model

    def next_sequence(self, case_id: UUID) -> int:
        result = self._db.execute(
            select(func.max(QualityQuarantineCaseRevisionModel.revision_number)).where(
                QualityQuarantineCaseRevisionModel.quarantine_case_id == case_id
            )
        )
        max_num = result.scalar() or 0
        return max_num + 1


class InspectionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, inspection_id: UUID) -> QualityInspectionModel | None:
        return self._db.get(QualityInspectionModel, inspection_id)

    def get_active_by_case(self, case_id: UUID) -> QualityInspectionModel | None:
        return (
            self._db.execute(
                select(QualityInspectionModel).where(
                    QualityInspectionModel.quarantine_case_id == case_id,
                    QualityInspectionModel.status.notin_(["COMPLETED", "CANCELLED", "SUPERSEDED"]),
                )
            )
            .scalars()
            .first()
        )

    def create(self, model: QualityInspectionModel) -> QualityInspectionModel:
        self._db.add(model)
        self._db.flush()
        return model


class InspectionControlRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_inspection(self, inspection_id: UUID) -> list[QualityInspectionControlModel]:
        return (
            self._db.execute(
                select(QualityInspectionControlModel)
                .where(QualityInspectionControlModel.inspection_id == inspection_id)
                .order_by(QualityInspectionControlModel.order_index)
            )
            .scalars()
            .all()
        )

    def get(self, control_id: UUID) -> QualityInspectionControlModel | None:
        return self._db.get(QualityInspectionControlModel, control_id)

    def create(self, model: QualityInspectionControlModel) -> QualityInspectionControlModel:
        self._db.add(model)
        self._db.flush()
        return model


class ControlResultRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_control(self, control_id: UUID) -> list[QualityInspectionControlResultModel]:
        return (
            self._db.execute(
                select(QualityInspectionControlResultModel).where(
                    QualityInspectionControlResultModel.inspection_control_id == control_id
                )
            )
            .scalars()
            .all()
        )

    def create(self, model: QualityInspectionControlResultModel) -> QualityInspectionControlResultModel:
        self._db.add(model)
        self._db.flush()
        return model


class MeasurementRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_inspection(self, inspection_id: UUID) -> list[QualityMeasurementModel]:
        return (
            self._db.execute(
                select(QualityMeasurementModel).where(
                    QualityMeasurementModel.inspection_id == inspection_id
                )
            )
            .scalars()
            .all()
        )

    def get(self, measurement_id: UUID) -> QualityMeasurementModel | None:
        return self._db.get(QualityMeasurementModel, measurement_id)

    def create(self, model: QualityMeasurementModel) -> QualityMeasurementModel:
        self._db.add(model)
        self._db.flush()
        return model


class SampleSetRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_inspection(self, inspection_id: UUID) -> list[QualityInspectionSampleSetModel]:
        return (
            self._db.execute(
                select(QualityInspectionSampleSetModel).where(
                    QualityInspectionSampleSetModel.inspection_id == inspection_id
                )
            )
            .scalars()
            .all()
        )

    def get(self, sample_set_id: UUID) -> QualityInspectionSampleSetModel | None:
        return self._db.get(QualityInspectionSampleSetModel, sample_set_id)

    def create(self, model: QualityInspectionSampleSetModel) -> QualityInspectionSampleSetModel:
        self._db.add(model)
        self._db.flush()
        return model


class SampleReferenceRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_set(self, sample_set_id: UUID) -> list[QualityInspectionSampleReferenceModel]:
        return (
            self._db.execute(
                select(QualityInspectionSampleReferenceModel).where(
                    QualityInspectionSampleReferenceModel.sample_set_id == sample_set_id
                )
            )
            .scalars()
            .all()
        )

    def create(self, model: QualityInspectionSampleReferenceModel) -> QualityInspectionSampleReferenceModel:
        self._db.add(model)
        self._db.flush()
        return model


class CertificateReviewRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_inspection(self, inspection_id: UUID) -> list[QualityCertificateReviewModel]:
        return (
            self._db.execute(
                select(QualityCertificateReviewModel).where(
                    QualityCertificateReviewModel.inspection_id == inspection_id
                )
            )
            .scalars()
            .all()
        )

    def get(self, review_id: UUID) -> QualityCertificateReviewModel | None:
        return self._db.get(QualityCertificateReviewModel, review_id)

    def create(self, model: QualityCertificateReviewModel) -> QualityCertificateReviewModel:
        self._db.add(model)
        self._db.flush()
        return model


class EvidenceLinkRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_inspection(self, inspection_id: UUID) -> list[QualityInspectionEvidenceLinkModel]:
        return (
            self._db.execute(
                select(QualityInspectionEvidenceLinkModel).where(
                    QualityInspectionEvidenceLinkModel.inspection_id == inspection_id
                )
            )
            .scalars()
            .all()
        )

    def create(self, model: QualityInspectionEvidenceLinkModel) -> QualityInspectionEvidenceLinkModel:
        self._db.add(model)
        self._db.flush()
        return model


class DecisionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, decision_id: UUID) -> QualityDispositionDecisionModel | None:
        return self._db.get(QualityDispositionDecisionModel, decision_id)

    def list_by_case(self, case_id: UUID) -> list[QualityDispositionDecisionModel]:
        return (
            self._db.execute(
                select(QualityDispositionDecisionModel).where(
                    QualityDispositionDecisionModel.quarantine_case_id == case_id
                )
            )
            .scalars()
            .all()
        )

    def create(self, model: QualityDispositionDecisionModel) -> QualityDispositionDecisionModel:
        self._db.add(model)
        self._db.flush()
        return model


class DecisionApprovalRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_decision(self, decision_id: UUID) -> list[QualityDecisionApprovalModel]:
        return (
            self._db.execute(
                select(QualityDecisionApprovalModel).where(
                    QualityDecisionApprovalModel.decision_id == decision_id
                )
            )
            .scalars()
            .all()
        )

    def create(self, model: QualityDecisionApprovalModel) -> QualityDecisionApprovalModel:
        self._db.add(model)
        self._db.flush()
        return model


class ReleaseRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, release_id: UUID) -> QuarantineReleaseAuthorizationModel | None:
        return self._db.get(QuarantineReleaseAuthorizationModel, release_id)

    def list_by_case(self, case_id: UUID) -> list[QuarantineReleaseAuthorizationModel]:
        return (
            self._db.execute(
                select(QuarantineReleaseAuthorizationModel).where(
                    QuarantineReleaseAuthorizationModel.quarantine_case_id == case_id
                )
            )
            .scalars()
            .all()
        )

    def create(self, model: QuarantineReleaseAuthorizationModel) -> QuarantineReleaseAuthorizationModel:
        self._db.add(model)
        self._db.flush()
        return model


class RejectionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, rejection_id: UUID) -> QuarantineRejectionAuthorizationModel | None:
        return self._db.get(QuarantineRejectionAuthorizationModel, rejection_id)

    def list_by_case(self, case_id: UUID) -> list[QuarantineRejectionAuthorizationModel]:
        return (
            self._db.execute(
                select(QuarantineRejectionAuthorizationModel).where(
                    QuarantineRejectionAuthorizationModel.quarantine_case_id == case_id
                )
            )
            .scalars()
            .all()
        )

    def create(self, model: QuarantineRejectionAuthorizationModel) -> QuarantineRejectionAuthorizationModel:
        self._db.add(model)
        self._db.flush()
        return model


class ReinspectionRequestRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, request_id: UUID) -> QualityReinspectionRequestModel | None:
        return self._db.get(QualityReinspectionRequestModel, request_id)

    def create(self, model: QualityReinspectionRequestModel) -> QualityReinspectionRequestModel:
        self._db.add(model)
        self._db.flush()
        return model


class ZoneRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, zone_id: UUID) -> QuarantineZoneConfigurationModel | None:
        return self._db.get(QuarantineZoneConfigurationModel, zone_id)

    def list_by_warehouse(self, organization_id: UUID, warehouse_id: UUID) -> list[QuarantineZoneConfigurationModel]:
        return (
            self._db.execute(
                select(QuarantineZoneConfigurationModel).where(
                    QuarantineZoneConfigurationModel.organization_id == organization_id,
                    QuarantineZoneConfigurationModel.warehouse_id == warehouse_id,
                )
            )
            .scalars()
            .all()
        )

    def create(self, model: QuarantineZoneConfigurationModel) -> QuarantineZoneConfigurationModel:
        self._db.add(model)
        self._db.flush()
        return model


class PlacementRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, placement_id: UUID) -> QuarantinePlacementConfirmationModel | None:
        return self._db.get(QuarantinePlacementConfirmationModel, placement_id)

    def list_by_case(self, case_id: UUID) -> list[QuarantinePlacementConfirmationModel]:
        return (
            self._db.execute(
                select(QuarantinePlacementConfirmationModel).where(
                    QuarantinePlacementConfirmationModel.quarantine_case_id == case_id
                )
            )
            .scalars()
            .all()
        )

    def create(self, model: QuarantinePlacementConfirmationModel) -> QuarantinePlacementConfirmationModel:
        self._db.add(model)
        self._db.flush()
        return model


class DispositionEventRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def next_sequence(self, case_id: UUID) -> int:
        result = self._db.execute(
            select(func.max(QualityDispositionEventModel.sequence_number)).where(
                QualityDispositionEventModel.quarantine_case_id == case_id
            )
        )
        max_num = result.scalar() or 0
        return max_num + 1

    def create(self, model: QualityDispositionEventModel) -> QualityDispositionEventModel:
        self._db.add(model)
        self._db.flush()
        return model


class ProjectionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def upsert(self, model: InboundQualityAvailabilityProjectionModel) -> None:
        self._db.merge(model)
        self._db.flush()

    def list_by_warehouse(
        self, organization_id: UUID, warehouse_id: UUID
    ) -> list[InboundQualityAvailabilityProjectionModel]:
        return (
            self._db.execute(
                select(InboundQualityAvailabilityProjectionModel).where(
                    InboundQualityAvailabilityProjectionModel.organization_id == organization_id,
                    InboundQualityAvailabilityProjectionModel.warehouse_id == warehouse_id,
                )
            )
            .scalars()
            .all()
        )


class SnapshotRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, model: QualityInspectionSnapshotModel) -> QualityInspectionSnapshotModel:
        self._db.add(model)
        self._db.flush()
        return model

    def get(self, snapshot_id: UUID) -> QualityInspectionSnapshotModel | None:
        return self._db.get(QualityInspectionSnapshotModel, snapshot_id)
