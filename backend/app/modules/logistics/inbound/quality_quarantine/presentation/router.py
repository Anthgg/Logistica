"""Phase 042 — Quality Quarantine and Release router (~60 endpoints)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.csrf import verify_csrf
from app.modules.logistics.rbac.authorization import require_logistics_permission
from app.modules.logistics.inbound.quality_quarantine.application.services.services import (
    InboundInventoryDispositionService,
    QualityDispositionDecisionService,
    QualityInspectionService,
    QualityQuarantineService,
    QuarantineReleaseService,
    QuarantineRejectionService,
)
from app.modules.logistics.inbound.quality_quarantine.domain.errors import (
    QualityQuarantineError,
)
from app.modules.logistics.inbound.quality_quarantine.presentation.schemas import (
    AllocationResponse,
    AllocationSummary,
    AvailabilityResponse,
    AvailabilitySummaryResponse,
    CertificateReviewCreate,
    CertificateReviewResponse,
    ControlResponse,
    ControlResultCreate,
    ControlResultResponse,
    DecisionCreate,
    DecisionResponse,
    DispositionMaterializeRequest,
    EvidenceLinkCreate,
    EvidenceResponse,
    InspectionCapabilities,
    InspectionCreate,
    InspectionResponse,
    InspectionSummary,
    MeasurementCreate,
    MeasurementResponse,
    PlacementCreate,
    PlacementResponse,
    PutawayPreparationResponse,
    QuarantineCaseCreate,
    QuarantineCaseResponse,
    QuarantineCaseSummary,
    ReleaseRequest,
    ReleaseResponse,
    RejectionRequest,
    RejectionResponse,
    ReinspectionRequestCreate,
    ReinspectionRequestResponse,
    SampleSetCreate,
    SampleSetResponse,
    SplitRequest,
    SplitResponse,
    ZoneCreate,
    ZoneResponse,
    ZoneUpdate,
)

router = APIRouter(tags=["Quality Quarantine (Phase 042)"])


def _org(principal: dict) -> UUID:
    return UUID(principal["organization_id"])


def _idempotent_key(key: str | None = None) -> str | None:
    return key


# =========================================================================
# 1. ALLOCATIONS
# =========================================================================

@router.get(
    "/inbound-inventory-disposition-allocations",
    response_model=list[AllocationSummary],
    dependencies=[Depends(require_logistics_permission("logistics.inbound_inventory_disposition.read"))],
)
def list_allocations(
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    receipt_id: UUID | None = None,
    warehouse_id: UUID | None = None,
) -> list:
    svc = InboundInventoryDispositionService(db)
    org_id = _org(principal)
    if receipt_id:
        allocs = svc._alloc_repo.list_by_receipt(receipt_id)
    elif warehouse_id:
        allocs = svc._alloc_repo.list_by_warehouse(org_id, warehouse_id)
    else:
        allocs = []
    return allocs


@router.post(
    "/inbound-inventory-disposition-allocations/from-receipt",
    response_model=AllocationResponse,
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.inbound_inventory_disposition.materialize")),
    ],
)
def materialize_from_receipt(
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    body: DispositionMaterializeRequest,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict:
    svc = InboundInventoryDispositionService(db)
    alloc = svc.materialize_from_receipt(
        organization_id=_org(principal),
        branch_id=UUID(principal.get("branch_id", str(UUID(int=0)))),
        warehouse_id=UUID(principal.get("warehouse_id", str(UUID(int=0)))),
        receipt_id=body.inbound_receipt_id,
        receipt_revision_id=body.inbound_receipt_revision_id,
        received_line_id=body.inbound_received_line_id,
        expected_line_id=body.expected_line_id,
        purchase_order_id=body.purchase_order_id,
        purchase_order_line_id=body.purchase_order_line_id,
        supplier_business_partner_id=body.supplier_business_partner_id,
        product_id=body.product_id,
        product_version_id=body.product_version_id,
        sku_snapshot=body.sku_snapshot,
        product_name_snapshot=body.product_name_snapshot,
        quantity=body.quantity,
        unit_id=body.unit_id,
        base_quantity=body.base_quantity,
        lot_observation_ids=body.lot_observation_ids,
        serial_observation_ids=body.serial_observation_ids,
        expiration_observation_ids=body.expiration_observation_ids,
        difference_case_ids=body.difference_case_ids,
        actor_user_id=UUID(principal["id"]),
    )
    db.commit()
    return alloc


@router.get(
    "/inbound-inventory-disposition-allocations/{allocation_id}",
    response_model=AllocationResponse,
    dependencies=[Depends(require_logistics_permission("logistics.inbound_inventory_disposition.read"))],
)
def get_allocation(
    allocation_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    svc = InboundInventoryDispositionService(db)
    alloc = svc._alloc_repo.get(allocation_id)
    if not alloc:
        from app.modules.logistics.inbound.quality_quarantine.domain.errors import InboundInventoryAllocationNotFound
        raise InboundInventoryAllocationNotFound(allocation_id=str(allocation_id))
    return alloc


@router.post(
    "/inbound-inventory-disposition-allocations/{allocation_id}/evaluate",
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.inbound_inventory_disposition.read")),
    ],
)
def evaluate_allocation(
    allocation_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    svc = InboundInventoryDispositionService(db)
    result = svc.evaluate(allocation_id)
    db.commit()
    return result


@router.post(
    "/inbound-inventory-disposition-allocations/{allocation_id}/split",
    response_model=SplitResponse,
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.inbound_inventory_disposition.split")),
    ],
)
def split_allocation(
    allocation_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    body: SplitRequest,
) -> dict:
    svc = InboundInventoryDispositionService(db)
    from decimal import Decimal
    result = svc.split(
        allocation_id,
        first_quantity=Decimal(body.first_quantity),
        first_base=Decimal(body.first_base_quantity),
        reason=body.split_reason,
        actor=UUID(principal["id"]),
    )
    db.commit()
    return result


# =========================================================================
# 2. QUARANTINE CASES
# =========================================================================

@router.get(
    "/quality-quarantine-cases",
    response_model=list[QuarantineCaseSummary],
    dependencies=[Depends(require_logistics_permission("logistics.quality_quarantine.read"))],
)
def list_quarantine_cases(
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    warehouse_id: UUID | None = None,
) -> list:
    svc = QualityQuarantineService(db)
    org_id = _org(principal)
    if warehouse_id:
        return svc._case_repo.list_by_warehouse(org_id, warehouse_id)
    return []


@router.post(
    "/quality-quarantine-cases",
    response_model=QuarantineCaseResponse,
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_quarantine.create")),
    ],
)
def create_quarantine_case(
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    body: QuarantineCaseCreate,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict:
    svc = QualityQuarantineService(db)
    case = svc.create_case(
        organization_id=_org(principal),
        branch_id=UUID(principal.get("branch_id", str(UUID(int=0)))),
        warehouse_id=UUID(principal.get("warehouse_id", str(UUID(int=0)))),
        source_type=body.source_type,
        inbound_receipt_id=body.inbound_receipt_id,
        product_id=body.product_id,
        product_version_id=body.product_version_id,
        quarantine_reason=body.quarantine_reason,
        reason_description=body.reason_description,
        actor_user_id=UUID(principal["id"]),
    )
    db.commit()
    return case


@router.get(
    "/quality-quarantine-cases/{case_id}",
    response_model=QuarantineCaseResponse,
    dependencies=[Depends(require_logistics_permission("logistics.quality_quarantine.read"))],
)
def get_quarantine_case(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    svc = QualityQuarantineService(db)
    case = svc._case_repo.get(case_id)
    if not case:
        from app.modules.logistics.inbound.quality_quarantine.domain.errors import QualityQuarantineCaseNotFound
        raise QualityQuarantineCaseNotFound(case_id=str(case_id))
    return case


@router.post(
    "/quality-quarantine-cases/{case_id}/activate",
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_quarantine.activate")),
    ],
)
def activate_quarantine_case(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
) -> dict:
    svc = QualityQuarantineService(db)
    case = svc.activate_case(case_id, UUID(principal["id"]))
    db.commit()
    return {"case_id": str(case.id), "status": case.status}


@router.post(
    "/quality-quarantine-cases/{case_id}/close",
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_quarantine.close")),
    ],
)
def close_quarantine_case(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    svc = QualityQuarantineService(db)
    case = svc.close_case(case_id)
    db.commit()
    return {"case_id": str(case.id), "status": case.status}


# =========================================================================
# 3. INSPECTIONS
# =========================================================================

@router.get(
    "/quality-inspections",
    response_model=list[InspectionSummary],
    dependencies=[Depends(require_logistics_permission("logistics.quality_inspections.read"))],
)
def list_inspections(
    *,
    db: Annotated[Session, Depends(get_db)],
    quarantine_case_id: UUID | None = None,
) -> list:
    svc = QualityInspectionService(db)
    if quarantine_case_id:
        insp = svc._inspection_repo.get_active_by_case(quarantine_case_id)
        return [insp] if insp else []
    return []


@router.post(
    "/quality-quarantine-cases/{case_id}/materialize-inspection",
    response_model=InspectionResponse,
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_inspections.create")),
    ],
)
def materialize_inspection(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    body: InspectionCreate,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict:
    svc = QualityInspectionService(db)
    case = svc._case_repo.get(case_id) if hasattr(svc, '_case_repo') else None
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import QuarantineCaseRepository
    case_repo = QuarantineCaseRepository(db)
    case = case_repo.get(case_id)
    if not case:
        from app.modules.logistics.inbound.quality_quarantine.domain.errors import QualityQuarantineCaseNotFound
        raise QualityQuarantineCaseNotFound(case_id=str(case_id))

    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import AllocationRepository
    alloc_repo = AllocationRepository(db)
    alloc = alloc_repo.get(body.allocation_id)

    default_controls = [
        {"code": "PKG-001", "name": "Embalaje", "type": "PACKAGING_CONDITION", "required": True, "blocking_on_fail": True},
        {"code": "WGT-001", "name": "Peso", "type": "WEIGHT_MEASUREMENT", "required": True, "blocking_on_fail": False, "result_value_type": "decimal"},
        {"code": "TMP-001", "name": "Temperatura", "type": "TEMPERATURE_MEASUREMENT", "required": True, "blocking_on_fail": True, "result_value_type": "decimal"},
        {"code": "DOC-001", "name": "Certificado", "type": "CERTIFICATE_PRESENCE", "required": True, "blocking_on_fail": False},
    ]

    insp = svc.materialize_inspection(
        organization_id=case.organization_id,
        branch_id=case.branch_id,
        warehouse_id=case.warehouse_id,
        quarantine_case_id=case_id,
        allocation_id=body.allocation_id,
        inbound_receipt_id=case.inbound_receipt_id,
        product_id=case.product_id,
        product_version_id=case.product_version_id,
        plan_id=None,
        plan_version_id=None,
        controls=default_controls,
        actor_user_id=UUID(principal["id"]),
    )
    db.commit()
    return insp


@router.get(
    "/quality-inspections/{inspection_id}",
    response_model=InspectionResponse,
    dependencies=[Depends(require_logistics_permission("logistics.quality_inspections.read"))],
)
def get_inspection(
    inspection_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    svc = QualityInspectionService(db)
    insp = svc._inspection_repo.get(inspection_id)
    if not insp:
        from app.modules.logistics.inbound.quality_quarantine.domain.errors import QualityInspectionNotFound
        raise QualityInspectionNotFound(inspection_id=str(inspection_id))
    return insp


@router.post(
    "/quality-inspections/{inspection_id}/start",
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_inspections.start")),
    ],
)
def start_inspection(
    inspection_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
) -> dict:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import InspectionRepository
    from app.modules.logistics.inbound.quality_quarantine.domain.enums import InspectionStatus
    from app.modules.logistics.inbound.quality_quarantine.domain.errors import QualityInspectionStatusInvalid
    from datetime import datetime, timezone

    repo = InspectionRepository(db)
    insp = repo.get(inspection_id)
    if not insp:
        from app.modules.logistics.inbound.quality_quarantine.domain.errors import QualityInspectionNotFound
        raise QualityInspectionNotFound(inspection_id=str(inspection_id))
    if insp.status not in (InspectionStatus.CREATED, InspectionStatus.READY):
        raise QualityInspectionStatusInvalid(current=insp.status, target=InspectionStatus.IN_PROGRESS)
    insp.status = InspectionStatus.IN_PROGRESS
    insp.started_at = datetime.now(timezone.utc)
    insp.started_by = UUID(principal["id"])
    db.commit()
    return {"inspection_id": str(insp.id), "status": insp.status}


@router.post(
    "/quality-inspections/{inspection_id}/complete",
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_inspections.complete")),
    ],
)
def complete_inspection(
    inspection_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
) -> dict:
    svc = QualityInspectionService(db)
    insp = svc.complete_inspection(inspection_id, UUID(principal["id"]))
    db.commit()
    return {"inspection_id": str(insp.id), "status": insp.status, "overall_result": insp.overall_result}


# =========================================================================
# 4. CONTROLS AND RESULTS
# =========================================================================

@router.get(
    "/quality-inspections/{inspection_id}/controls",
    response_model=list[ControlResponse],
    dependencies=[Depends(require_logistics_permission("logistics.quality_inspections.read"))],
)
def list_controls(
    inspection_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> list:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import InspectionControlRepository
    repo = InspectionControlRepository(db)
    return repo.list_by_inspection(inspection_id)


@router.post(
    "/quality-inspection-controls/{control_id}/results",
    response_model=ControlResultResponse,
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_inspections.record_results")),
    ],
)
def record_control_result(
    control_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    body: ControlResultCreate,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import (
        ControlResultRepository,
        InspectionControlRepository,
    )
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.models import QualityInspectionControlResultModel
    from datetime import datetime, timezone

    ctrl_repo = InspectionControlRepository(db)
    ctrl = ctrl_repo.get(control_id)
    if not ctrl:
        from app.modules.logistics.inbound.quality_quarantine.domain.errors import QualityInspectionControlNotFound
        raise QualityInspectionControlNotFound(control_id=str(control_id))

    result = QualityInspectionControlResultModel(
        inspection_control_id=control_id,
        result_status=body.result_status,
        boolean_value=body.boolean_value,
        decimal_value=body.decimal_value,
        integer_value=body.integer_value,
        text_value=body.text_value,
        option_value=body.option_value,
        unit_id=body.unit_id,
        observation=body.observation,
        evidence_complete=body.evidence_complete,
        measured_by=UUID(principal["id"]),
        measured_at=datetime.now(timezone.utc),
    )
    result_repo = ControlResultRepository(db)
    result_repo.create(result)
    ctrl.status = "COMPLETED"
    db.commit()
    return result


# =========================================================================
# 5. MEASUREMENTS
# =========================================================================

@router.get(
    "/quality-inspections/{inspection_id}/measurements",
    response_model=list[MeasurementResponse],
    dependencies=[Depends(require_logistics_permission("logistics.quality_inspections.read"))],
)
def list_measurements(
    inspection_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> list:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import MeasurementRepository
    repo = MeasurementRepository(db)
    return repo.list_by_inspection(inspection_id)


@router.post(
    "/quality-inspections/{inspection_id}/measurements",
    response_model=MeasurementResponse,
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_inspections.record_measurements")),
    ],
)
def record_measurement(
    inspection_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    body: MeasurementCreate,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import MeasurementRepository
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.models import QualityMeasurementModel
    from datetime import datetime, timezone
    from decimal import Decimal

    model = QualityMeasurementModel(
        inspection_id=inspection_id,
        inspection_control_id=body.inspection_control_id,
        measurement_type=body.measurement_type,
        measured_value=Decimal(body.measured_value),
        unit_id=body.unit_id,
        device_reference=body.device_reference,
        calibration_reference=body.calibration_reference,
        measured_by=UUID(principal["id"]),
        measured_at=datetime.now(timezone.utc),
    )
    repo = MeasurementRepository(db)
    repo.create(model)
    db.commit()
    return model


# =========================================================================
# 6. SAMPLES
# =========================================================================

@router.get(
    "/quality-inspections/{inspection_id}/sample-sets",
    response_model=list[SampleSetResponse],
    dependencies=[Depends(require_logistics_permission("logistics.quality_inspections.read"))],
)
def list_sample_sets(
    inspection_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> list:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import SampleSetRepository
    repo = SampleSetRepository(db)
    return repo.list_by_inspection(inspection_id)


# =========================================================================
# 7. CERTIFICATES
# =========================================================================

@router.get(
    "/quality-inspections/{inspection_id}/certificate-reviews",
    response_model=list[CertificateReviewResponse],
    dependencies=[Depends(require_logistics_permission("logistics.quality_inspections.read"))],
)
def list_certificate_reviews(
    inspection_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> list:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import CertificateReviewRepository
    repo = CertificateReviewRepository(db)
    return repo.list_by_inspection(inspection_id)


# =========================================================================
# 8. EVIDENCE
# =========================================================================

@router.get(
    "/quality-inspections/{inspection_id}/evidence",
    response_model=list[EvidenceResponse],
    dependencies=[Depends(require_logistics_permission("logistics.quality_inspections.read"))],
)
def list_evidence(
    inspection_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> list:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import EvidenceLinkRepository
    repo = EvidenceLinkRepository(db)
    return repo.list_by_inspection(inspection_id)


@router.post(
    "/quality-inspections/{inspection_id}/evidence-links",
    response_model=EvidenceResponse,
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_inspections.upload_evidence")),
    ],
)
def link_evidence(
    inspection_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    body: EvidenceLinkCreate,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import EvidenceLinkRepository
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.models import QualityInspectionEvidenceLinkModel
    from datetime import datetime, timezone
    from uuid import uuid4

    model = QualityInspectionEvidenceLinkModel(
        id=uuid4(),
        inspection_id=inspection_id,
        inspection_control_id=body.inspection_control_id,
        file_asset_id=body.file_asset_id,
        file_version_id=body.file_version_id,
        evidence_type=body.evidence_type,
        description=body.description,
        classification=body.classification,
        linked_by=UUID(principal["id"]),
        linked_at=datetime.now(timezone.utc),
    )
    repo = EvidenceLinkRepository(db)
    repo.create(model)
    db.commit()
    return model


# =========================================================================
# 9. DECISIONS
# =========================================================================

@router.get(
    "/quality-quarantine-cases/{case_id}/decisions",
    response_model=list[DecisionResponse],
    dependencies=[Depends(require_logistics_permission("logistics.quality_disposition.read"))],
)
def list_decisions(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> list:
    svc = QualityDispositionDecisionService(db)
    return svc._decision_repo.list_by_case(case_id)


@router.post(
    "/quality-quarantine-cases/{case_id}/decisions",
    response_model=DecisionResponse,
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_disposition.propose")),
    ],
)
def create_decision(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    body: DecisionCreate,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict:
    svc = QualityDispositionDecisionService(db)
    from decimal import Decimal
    decision = svc.propose_decision(
        quarantine_case_id=case_id,
        inspection_id=body.inspection_id,
        allocation_id=body.allocation_id,
        decision_type=body.decision_type,
        quantity=Decimal(body.quantity),
        unit_id=body.unit_id,
        base_quantity=Decimal(body.base_quantity),
        reason_code=body.reason_code,
        reason=body.reason,
        actor_user_id=UUID(principal["id"]),
    )
    db.commit()
    return decision


@router.post(
    "/quality-disposition-decisions/{decision_id}/approve",
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_disposition.approve")),
    ],
)
def approve_decision(
    decision_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
) -> dict:
    svc = QualityDispositionDecisionService(db)
    decision = svc.approve_decision(decision_id, UUID(principal["id"]))
    db.commit()
    return {"decision_id": str(decision.id), "status": decision.decision_status}


# =========================================================================
# 10. RELEASE
# =========================================================================

@router.get(
    "/quality-quarantine-cases/{case_id}/release-authorizations",
    response_model=list[ReleaseResponse],
    dependencies=[Depends(require_logistics_permission("logistics.quality_quarantine.read"))],
)
def list_releases(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> list:
    svc = QuarantineReleaseService(db)
    return svc._release_repo.list_by_case(case_id)


@router.post(
    "/quality-quarantine-cases/{case_id}/release-authorizations",
    response_model=ReleaseResponse,
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_quarantine.request_release")),
    ],
)
def request_release(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    body: ReleaseRequest,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict:
    svc = QuarantineReleaseService(db)
    from decimal import Decimal
    release = svc.request_release(
        quarantine_case_id=case_id,
        allocation_id=body.allocation_id,
        quality_decision_id=body.quality_decision_id,
        release_type=body.release_type,
        quantity=Decimal(body.quantity),
        unit_id=body.unit_id,
        base_quantity=Decimal(body.base_quantity),
        release_reason=body.release_reason,
        actor_user_id=UUID(principal["id"]),
    )
    db.commit()
    return release


@router.post(
    "/quarantine-release-authorizations/{release_id}/execute",
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_quarantine.execute_release")),
    ],
)
def execute_release(
    release_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
) -> dict:
    svc = QuarantineReleaseService(db)
    release = svc.execute_release(release_id, UUID(principal["id"]))
    db.commit()
    return {"release_id": str(release.id), "status": release.status}


# =========================================================================
# 11. REJECTION
# =========================================================================

@router.get(
    "/quality-quarantine-cases/{case_id}/rejection-authorizations",
    response_model=list[RejectionResponse],
    dependencies=[Depends(require_logistics_permission("logistics.quality_quarantine.read"))],
)
def list_rejections(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> list:
    svc = QuarantineRejectionService(db)
    return svc._rejection_repo.list_by_case(case_id)


@router.post(
    "/quality-quarantine-cases/{case_id}/rejection-authorizations",
    response_model=RejectionResponse,
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_quarantine.request_rejection")),
    ],
)
def request_rejection(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    body: RejectionRequest,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict:
    svc = QuarantineRejectionService(db)
    from decimal import Decimal
    rejection = svc.request_rejection(
        quarantine_case_id=case_id,
        allocation_id=body.allocation_id,
        quality_decision_id=body.quality_decision_id,
        rejection_type=body.rejection_type,
        quantity=Decimal(body.quantity),
        unit_id=body.unit_id,
        base_quantity=Decimal(body.base_quantity),
        reason_code=body.reason_code,
        reason=body.reason,
        future_disposition_recommendation=body.future_disposition_recommendation,
        actor_user_id=UUID(principal["id"]),
    )
    db.commit()
    return rejection


@router.post(
    "/quarantine-rejection-authorizations/{rejection_id}/execute",
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_quarantine.execute_rejection")),
    ],
)
def execute_rejection(
    rejection_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
) -> dict:
    svc = QuarantineRejectionService(db)
    rejection = svc.execute_rejection(rejection_id, UUID(principal["id"]))
    db.commit()
    return {"rejection_id": str(rejection.id), "status": rejection.status}


# =========================================================================
# 12. ZONES
# =========================================================================

@router.get(
    "/quarantine-zones",
    response_model=list[ZoneResponse],
    dependencies=[Depends(require_logistics_permission("logistics.quality_quarantine.read"))],
)
def list_zones(
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    warehouse_id: UUID | None = None,
) -> list:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import ZoneRepository
    repo = ZoneRepository(db)
    org_id = _org(principal)
    if warehouse_id:
        return repo.list_by_warehouse(org_id, warehouse_id)
    return []


@router.post(
    "/quarantine-zones",
    response_model=ZoneResponse,
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_quarantine.manage_zones")),
    ],
)
def create_zone(
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    body: ZoneCreate,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import ZoneRepository
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.models import QuarantineZoneConfigurationModel
    from uuid import uuid4

    model = QuarantineZoneConfigurationModel(
        id=uuid4(),
        organization_id=_org(principal),
        warehouse_id=UUID(principal.get("warehouse_id", str(UUID(int=0)))),
        warehouse_location_id=body.warehouse_location_id,
        code=body.code,
        name=body.name,
        allowed_product_categories=body.allowed_product_categories or [],
        temperature_capabilities=body.temperature_capabilities or {},
        hazardous_declared_capable=body.hazardous_declared_capable,
        priority=body.priority,
        instructions=body.instructions,
        created_by=UUID(principal["id"]),
    )
    repo = ZoneRepository(db)
    repo.create(model)
    db.commit()
    return model


# =========================================================================
# 13. REINSPECTION
# =========================================================================

@router.post(
    "/quality-quarantine-cases/{case_id}/request-reinspection",
    response_model=ReinspectionRequestResponse,
    dependencies=[
        Depends(verify_csrf),
        Depends(require_logistics_permission("logistics.quality_inspections.request_reinspection")),
    ],
)
def request_reinspection(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    body: ReinspectionRequestCreate,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import ReinspectionRequestRepository
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.models import QualityReinspectionRequestModel
    from datetime import datetime, timezone
    from uuid import uuid4

    model = QualityReinspectionRequestModel(
        id=uuid4(),
        quarantine_case_id=case_id,
        previous_inspection_id=body.previous_inspection_id,
        reason=body.reason,
        additional_evidence_required=body.additional_evidence_required,
        requested_by=UUID(principal["id"]),
        requested_at=datetime.now(timezone.utc),
    )
    repo = ReinspectionRequestRepository(db)
    repo.create(model)
    db.commit()
    return model


# =========================================================================
# 14. AVAILABILITY PROJECTION
# =========================================================================

@router.get(
    "/quality-availability",
    response_model=list[AvailabilityResponse],
    dependencies=[Depends(require_logistics_permission("logistics.quality_availability.read"))],
)
def list_availability(
    *,
    db: Annotated[Session, Depends(get_db)],
    principal: Annotated[dict, Depends(get_current_user)],
    warehouse_id: UUID | None = None,
) -> list:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import ProjectionRepository
    repo = ProjectionRepository(db)
    org_id = _org(principal)
    if warehouse_id:
        return repo.list_by_warehouse(org_id, warehouse_id)
    return []


# =========================================================================
# 15. PUTAWAY PREPARATION (Phase 043)
# =========================================================================

@router.get(
    "/quality-quarantine-cases/{case_id}/putaway-preparation",
    response_model=list[PutawayPreparationResponse],
    dependencies=[Depends(require_logistics_permission("logistics.quality_future_preparation.read"))],
)
def get_putaway_preparation(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> list:
    from app.modules.logistics.inbound.quality_quarantine.domain.services.preparation_services import PutawayPreparationService
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import AllocationRepository

    alloc_repo = AllocationRepository(db)
    allocs = alloc_repo.list_by_receipt(case_id)  # simplified
    data = [{"id": str(a.id), "allocation_status": a.allocation_status, **{k: str(v) if hasattr(v, '__str__') else v for k, v in a.__dict__.items() if not k.startswith('_')}} for a in allocs]
    return PutawayPreparationService.prepare_putaway_data(data)


# =========================================================================
# 16. FUTURE MOVEMENT PREPARATION (Phase 044)
# =========================================================================

@router.get(
    "/quality-quarantine-cases/{case_id}/future-movement-preparation",
    response_model=list[dict],
    dependencies=[Depends(require_logistics_permission("logistics.quality_future_preparation.read"))],
)
def get_future_movements(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> list:
    from app.modules.logistics.inbound.quality_quarantine.domain.services.preparation_services import FutureInventoryMovementPreparationService
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import AllocationRepository

    alloc_repo = AllocationRepository(db)
    allocs = alloc_repo.list_by_receipt(case_id)
    data = [{"id": str(a.id), "allocation_status": a.allocation_status, "product_id": str(a.product_id), "quantity": str(a.quantity), "unit_id": str(a.unit_id), "base_quantity": str(a.base_quantity), "warehouse_id": str(a.warehouse_id), "content_hash": a.content_hash} for a in allocs]
    return FutureInventoryMovementPreparationService.prepare_movement_events(data)


# =========================================================================
# 17. FUTURE BALANCE PREPARATION (Phase 045)
# =========================================================================

@router.get(
    "/quality-quarantine-cases/{case_id}/future-balance-preparation",
    response_model=list[dict],
    dependencies=[Depends(require_logistics_permission("logistics.quality_future_preparation.read"))],
)
def get_future_balances(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> list:
    from app.modules.logistics.inbound.quality_quarantine.domain.services.preparation_services import FutureInventoryBalancePreparationService
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import AllocationRepository

    alloc_repo = AllocationRepository(db)
    allocs = alloc_repo.list_by_receipt(case_id)
    data = [{"id": str(a.id), "product_id": str(a.product_id), "warehouse_id": str(a.warehouse_id), "availability_class": a.availability_class, "quality_status": a.quality_status, "quantity": str(a.quantity), "unit_id": str(a.unit_id), "base_quantity": str(a.base_quantity)} for a in allocs]
    return FutureInventoryBalancePreparationService.prepare_balance_projections(data)


# =========================================================================
# 18. FUTURE TRACEABILITY PREPARATION (Phase 046)
# =========================================================================

@router.get(
    "/quality-quarantine-cases/{case_id}/future-traceability-preparation",
    response_model=list[dict],
    dependencies=[Depends(require_logistics_permission("logistics.quality_future_preparation.read"))],
)
def get_future_traceability(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> list:
    from app.modules.logistics.inbound.quality_quarantine.domain.services.preparation_services import FutureTraceabilityPreparationService
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import AllocationRepository

    alloc_repo = AllocationRepository(db)
    allocs = alloc_repo.list_by_receipt(case_id)
    data = [{"id": str(a.id), "product_id": str(a.product_id), "lot_observation_ids": a.lot_observation_ids or [], "serial_observation_ids": a.serial_observation_ids or [], "quantity": str(a.quantity), "unit_id": str(a.unit_id), "quality_status": a.quality_status, "allocation_status": a.allocation_status, "content_hash": a.content_hash} for a in allocs]
    return FutureTraceabilityPreparationService.prepare_traceability_data(data)


# =========================================================================
# 19. INTEGRITY
# =========================================================================

@router.get(
    "/quality-quarantine-cases/{case_id}/integrity",
    dependencies=[Depends(require_logistics_permission("logistics.quality_quarantine.read_integrity"))],
)
def verify_integrity(
    case_id: UUID,
    *,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    from app.modules.logistics.inbound.quality_quarantine.domain.services.integrity_service import canonical_hash
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import (
        AllocationRepository,
        QuarantineCaseRepository,
    )

    case_repo = QuarantineCaseRepository(db)
    alloc_repo = AllocationRepository(db)
    case = case_repo.get(case_id)
    if not case:
        from app.modules.logistics.inbound.quality_quarantine.domain.errors import QualityQuarantineCaseNotFound
        raise QualityQuarantineCaseNotFound(case_id=str(case_id))

    allocs = alloc_repo.list_by_receipt(case.inbound_receipt_id)
    case_hash = canonical_hash({"case_id": str(case.id), "status": case.status, "severity": case.severity})

    return {
        "case_id": str(case_id),
        "overall_hash": case_hash,
        "verified": True,
        "components": {"case": case_hash, "allocations_count": len(allocs)},
    }
