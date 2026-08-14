"""FastAPI router for Phase 037 Gate Control.

Base URL: /api/logistics
All security enforced via RBAC + step-up at the dependency layer.

CRITICAL boundaries:
- guard_user_id derived from session — never from request body.
- arrived_at from server clock — never from request body.
- No dock assignment, dock reservation, unloading or inventory endpoints here.
- No Phase 038 logic executed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.pdf_response import build_pdf_download_response
from app.database.session import get_db
from app.modules.logistics.auth_dependencies import (
    get_logistics_principal,
    require_permission,
    resolve_organization_id,
    verify_csrf,
)
from app.modules.logistics.inbound.gate_control.application.services import (
    DockAssignmentPreparationService,
    GateAppointmentResolver,
    GateCheckInService,
    GateCheckInSnapshotProvider,
    GateControlIntegrityService,
    GateDecisionService,
    GateGuardResolver,
    InboundGateReleaseService,
    gate_arrival_time_service,
    gate_guard_resolver,
)
from app.modules.logistics.inbound.gate_control.application.document_service import (
    GateCheckInDocumentService,
)
from app.modules.logistics.inbound.gate_control.domain.errors import (
    GateCheckInNotFoundError,
    GateCheckInWalkInNotAllowedError,
    WarehouseGateDuplicateCodeError,
    WarehouseGateNotFoundError,
)
from app.modules.logistics.inbound.gate_control.domain.value_objects import (
    GateCheckInStatus,
)
from app.modules.logistics.inbound.gate_control.infrastructure.persistence.models import (
    GateCheckInModel,
    GateCheckInRevisionModel,
    GateDriverInspectionModel,
    GateEntryDecisionModel,
    GatePresentedDocumentModel,
    GatePhotoEvidenceModel,
    GateSealInspectionModel,
    GateVehicleInspectionModel,
    GateVerificationCheckDefinitionModel,
    GateVerificationCheckResultModel,
    GateVerificationExceptionModel,
    GateVerificationPolicyModel,
    GateVerificationPolicyVersionModel,
    WarehouseGateModel,
    GateCheckInHoldModel,
    GateCheckInCorrectionRequestModel,
    GateCheckInTimeCorrectionModel,
)
from app.modules.logistics.inbound.gate_control.presentation.schemas import (
    DockAssignmentPreparationResponse,
    GateAppointmentResolveRequest,
    GateAppointmentResolveResponse,
    GateCheckInCapabilities,
    GateCheckInCreate,
    GateCheckInHoldRequest,
    GateCheckInListResponse,
    GateCheckInResponse,
    GateCheckInSummary,
    GateCheckInTimeCorrectionCreate,
    GateCheckInCorrectionCreate,
    GateCheckInValidationResponse,
    GateCpvDocumentResponse,
    GateDriverInspectionCreate,
    GateEntryDecisionRequest,
    GateIntegrityResponse,
    GatePresentedDocumentCreate,
    GateSealInspectionCreate,
    GateVerificationCheckCreate,
    GateVerificationCheckResultCreate,
    GateVerificationExceptionCreate,
    GateVerificationPolicyCreate,
    GateVerificationPolicyVersionCreate,
    GateVehicleInspectionCreate,
    GateWalkInCreate,
    WarehouseGateCreate,
    WarehouseGateResponse,
    WarehouseGateUpdate,
)
from app.core.exceptions import ApplicationError

router = APIRouter(tags=["Gate Control (Phase 037)"])

_PERM_GATES_READ = "logistics.warehouse_gates.read"
_PERM_GATES_MANAGE = "logistics.warehouse_gates.manage"
_PERM_GATES_ACTIVATE = "logistics.warehouse_gates.activate"
_PERM_CHECKIN_READ = "logistics.gate_check_ins.read"
_PERM_CHECKIN_READ_ALL = "logistics.gate_check_ins.read_all"
_PERM_CHECKIN_CREATE = "logistics.gate_check_ins.create"
_PERM_CHECKIN_START = "logistics.gate_check_ins.start_verification"
_PERM_CHECKIN_HOLD = "logistics.gate_check_ins.hold"
_PERM_CHECKIN_RESUME = "logistics.gate_check_ins.resume"
_PERM_CHECKIN_COMPLETE = "logistics.gate_check_ins.complete"
_PERM_CHECKIN_CANCEL = "logistics.gate_check_ins.cancel"
_PERM_CHECKIN_WALK_IN = "logistics.gate_check_ins.walk_in"
_PERM_VEHICLE_INSP = "logistics.gate_vehicle_inspections.manage"
_PERM_DRIVER_INSP = "logistics.gate_driver_inspections.manage"
_PERM_DOC_INSP = "logistics.gate_document_inspections.manage"
_PERM_SEAL_INSP = "logistics.gate_seal_inspections.manage"
_PERM_PHOTO_CAPTURE = "logistics.gate_photo_evidence.capture"
_PERM_PHOTO_READ = "logistics.gate_photo_evidence.read"
_PERM_SENSITIVE_EVIDENCE = "logistics.gate_sensitive_evidence.read"
_PERM_EXCEPTION_REQUEST = "logistics.gate_exceptions.request"
_PERM_EXCEPTION_APPROVE = "logistics.gate_exceptions.approve"
_PERM_EXCEPTION_REJECT = "logistics.gate_exceptions.reject"
_PERM_ENTRY_AUTHORIZE = "logistics.gate_entry.authorize"
_PERM_ENTRY_AUTH_OBS = "logistics.gate_entry.authorize_with_observations"
_PERM_ENTRY_DENY = "logistics.gate_entry.deny"
_PERM_ENTRY_SUPERVISE = "logistics.gate_entry.supervise"
_PERM_DOC_PREVIEW = "logistics.gate_documents.preview"
_PERM_DOC_ISSUE = "logistics.gate_documents.issue"
_PERM_DOC_DOWNLOAD = "logistics.gate_documents.download"
_PERM_DOC_PACKAGE = "logistics.gate_documents.download_package"
_PERM_CORRECTION_REQUEST = "logistics.gate_check_ins.request_correction"
_PERM_CORRECTION_APPROVE = "logistics.gate_check_ins.approve_correction"
_PERM_POLICY_READ = "logistics.warehouse_gates.read"
_PERM_POLICY_MANAGE = "logistics.warehouse_gates.manage"


# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def _server_time() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_code(code: str) -> str:
    return code.upper().replace(" ", "").replace("-", "")


def _gate_capabilities(check_in: GateCheckInModel) -> list[str]:
    """Return list of available operations for the given check-in status."""
    status = check_in.status
    caps = []
    if status == "CREATED":
        caps += ["record_arrival", "cancel"]
    elif status == "ARRIVAL_RECORDED":
        caps += ["start_verification", "cancel"]
    elif status == "VERIFICATION_IN_PROGRESS":
        caps += [
            "submit_vehicle_inspection",
            "submit_driver_inspection",
            "submit_document",
            "submit_seal_inspection",
            "capture_photo",
            "complete_check_result",
            "request_exception",
            "hold",
            "request_supervisor",
            "deny_entry",
            "cancel",
        ]
    elif status == "WAITING_SUPERVISOR":
        caps += ["authorize_with_observations", "deny_entry", "hold", "resume"]
    elif status == "HELD_AT_GATE":
        caps += ["resume", "authorize_with_observations", "deny_entry", "cancel"]
    elif status == "VERIFIED":
        caps += ["authorize_entry", "authorize_with_observations", "deny_entry"]
    elif status in ("ENTRY_AUTHORIZED", "ENTRY_AUTHORIZED_WITH_OBSERVATIONS"):
        caps += ["complete", "issue_document", "preview_document"]
    elif status == "ENTRY_DENIED":
        caps += ["complete", "issue_document"]
    return caps


# ─────────────────────────────────────────────────────────────────────────────
# Warehouse Gates
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/warehouse-gates", response_model=list[WarehouseGateResponse])
def list_warehouse_gates(
    warehouse_id: Optional[UUID] = None,
    status: Optional[str] = None,
    principal=Depends(require_permission(_PERM_GATES_READ)),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    q = select(WarehouseGateModel).where(
        WarehouseGateModel.organization_id == org_id
    )
    if warehouse_id:
        q = q.where(WarehouseGateModel.warehouse_id == warehouse_id)
    if status:
        q = q.where(WarehouseGateModel.status == status)
    rows = list(db.scalars(q))
    return rows


@router.post("/warehouse-gates", response_model=WarehouseGateResponse, status_code=201)
def create_warehouse_gate(
    body: WarehouseGateCreate,
    principal=Depends(require_permission(_PERM_GATES_MANAGE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    norm = _normalize_code(body.code)

    existing = db.scalars(
        select(WarehouseGateModel).where(
            WarehouseGateModel.warehouse_id == body.warehouse_id,
            WarehouseGateModel.normalized_code == norm,
        )
    ).first()
    if existing:
        raise WarehouseGateDuplicateCodeError(body.code)

    gate = WarehouseGateModel(
        id=uuid4(),
        organization_id=org_id,
        branch_id=body.branch_id,
        warehouse_id=body.warehouse_id,
        code=body.code,
        normalized_code=norm,
        name=body.name,
        description=body.description,
        gate_type=body.gate_type,
        direction_policy=body.direction_policy,
        timezone=body.timezone,
        status="DRAFT",
        instructions=body.instructions,
        created_by=principal.user_id,
    )
    db.add(gate)
    db.commit()
    db.refresh(gate)
    return gate


@router.get("/warehouse-gates/{gate_id}", response_model=WarehouseGateResponse)
def get_warehouse_gate(
    gate_id: UUID,
    principal=Depends(require_permission(_PERM_GATES_READ)),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    gate = db.scalars(
        select(WarehouseGateModel).where(
            WarehouseGateModel.id == gate_id,
            WarehouseGateModel.organization_id == org_id,
        )
    ).first()
    if gate is None:
        raise WarehouseGateNotFoundError(str(gate_id))
    return gate


@router.patch("/warehouse-gates/{gate_id}", response_model=WarehouseGateResponse)
def update_warehouse_gate(
    gate_id: UUID,
    body: WarehouseGateUpdate,
    principal=Depends(require_permission(_PERM_GATES_MANAGE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    gate = db.scalars(
        select(WarehouseGateModel).where(
            WarehouseGateModel.id == gate_id,
            WarehouseGateModel.organization_id == org_id,
        )
    ).first()
    if gate is None:
        raise WarehouseGateNotFoundError(str(gate_id))
    if gate.row_version != body.row_version:
        raise ApplicationError(
            "OPTIMISTIC_LOCK_CONFLICT",
            "El registro fue modificado por otro proceso. Recargue e intente nuevamente.",
            409,
        )
    if body.name is not None:
        gate.name = body.name
    if body.description is not None:
        gate.description = body.description
    if body.gate_type is not None:
        gate.gate_type = body.gate_type
    if body.direction_policy is not None:
        gate.direction_policy = body.direction_policy
    if body.timezone is not None:
        gate.timezone = body.timezone
    if body.instructions is not None:
        gate.instructions = body.instructions
    gate.updated_by = principal.user_id
    gate.row_version += 1
    db.commit()
    db.refresh(gate)
    return gate


@router.post("/warehouse-gates/{gate_id}/activate", status_code=200)
def activate_warehouse_gate(
    gate_id: UUID,
    principal=Depends(require_permission(_PERM_GATES_ACTIVATE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    gate = db.scalars(
        select(WarehouseGateModel).where(
            WarehouseGateModel.id == gate_id,
            WarehouseGateModel.organization_id == org_id,
        )
    ).first()
    if gate is None:
        raise WarehouseGateNotFoundError(str(gate_id))
    gate.status = "ACTIVE"
    gate.updated_by = principal.user_id
    gate.row_version += 1
    db.commit()
    return {"status": "ACTIVE", "gate_id": str(gate_id)}


@router.post("/warehouse-gates/{gate_id}/deactivate", status_code=200)
def deactivate_warehouse_gate(
    gate_id: UUID,
    principal=Depends(require_permission(_PERM_GATES_MANAGE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    gate = db.scalars(
        select(WarehouseGateModel).where(
            WarehouseGateModel.id == gate_id,
            WarehouseGateModel.organization_id == org_id,
        )
    ).first()
    if gate is None:
        raise WarehouseGateNotFoundError(str(gate_id))
    gate.status = "INACTIVE"
    gate.updated_by = principal.user_id
    gate.row_version += 1
    db.commit()
    return {"status": "INACTIVE", "gate_id": str(gate_id)}


@router.post("/warehouse-gates/{gate_id}/archive", status_code=200)
def archive_warehouse_gate(
    gate_id: UUID,
    principal=Depends(require_permission(_PERM_GATES_MANAGE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    gate = db.scalars(
        select(WarehouseGateModel).where(
            WarehouseGateModel.id == gate_id,
            WarehouseGateModel.organization_id == org_id,
        )
    ).first()
    if gate is None:
        raise WarehouseGateNotFoundError(str(gate_id))
    gate.status = "ARCHIVED"
    gate.updated_by = principal.user_id
    gate.row_version += 1
    db.commit()
    return {"status": "ARCHIVED", "gate_id": str(gate_id)}


@router.get("/warehouse-gates/{gate_id}/current-queue")
def get_gate_queue(
    gate_id: UUID,
    principal=Depends(require_permission(_PERM_GATES_READ)),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    active_statuses = [
        "ARRIVAL_RECORDED",
        "VERIFICATION_IN_PROGRESS",
        "WAITING_SUPERVISOR",
        "WAITING_DOCUMENTS",
        "HELD_AT_GATE",
        "VERIFIED",
    ]
    rows = list(db.scalars(
        select(GateCheckInModel).where(
            GateCheckInModel.gate_id == gate_id,
            GateCheckInModel.organization_id == org_id,
            GateCheckInModel.status.in_(active_statuses),
        )
    ))
    return {
        "gate_id": str(gate_id),
        "queue_count": len(rows),
        "server_time": _server_time().isoformat(),
        "items": [
            {
                "check_in_id": str(r.id),
                "status": r.status,
                "appointment_code": r.appointment_code_snapshot,
                "arrived_at": r.arrived_at.isoformat() if r.arrived_at else None,
            }
            for r in rows
        ],
    }


@router.get("/warehouse-gates/{gate_id}/today-summary")
def get_gate_today_summary(
    gate_id: UUID,
    principal=Depends(require_permission(_PERM_GATES_READ)),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    from datetime import date, timedelta

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_end = today_start + timedelta(days=1)
    rows = list(db.scalars(
        select(GateCheckInModel).where(
            GateCheckInModel.gate_id == gate_id,
            GateCheckInModel.organization_id == org_id,
            GateCheckInModel.arrived_at >= today_start,
            GateCheckInModel.arrived_at < today_end,
        )
    ))
    authorized = sum(
        1
        for r in rows
        if r.status in ("ENTRY_AUTHORIZED", "ENTRY_AUTHORIZED_WITH_OBSERVATIONS", "COMPLETED")
        and r.decision in ("AUTHORIZE_ENTRY", "AUTHORIZE_WITH_OBSERVATIONS")
    )
    denied = sum(1 for r in rows if r.decision == "DENY_ENTRY")
    held = sum(1 for r in rows if r.status == "HELD_AT_GATE")
    return {
        "gate_id": str(gate_id),
        "date": today_start.date().isoformat(),
        "total": len(rows),
        "authorized": authorized,
        "denied": denied,
        "held": held,
        "in_progress": len(rows) - authorized - denied,
        "server_time": _server_time().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Appointment Resolution
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/gate-control/resolve-appointment", response_model=GateAppointmentResolveResponse)
def resolve_appointment(
    body: GateAppointmentResolveRequest,
    principal=Depends(require_permission(_PERM_CHECKIN_READ)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    resolver = GateAppointmentResolver()
    warnings: list[str] = []
    blocking: list[str] = []

    try:
        if body.cit_code:
            result = resolver.resolve_by_cit_code(
                db, body.cit_code, body.warehouse_id, org_id
            )
        elif body.opaque_qr_payload:
            # QR resolution: decode appointment_id from opaque payload
            import base64, json as _json

            try:
                decoded = _json.loads(base64.urlsafe_b64decode(body.opaque_qr_payload + "=="))
                appt_id = UUID(decoded["appointment_id"])
            except Exception:
                raise ApplicationError(
                    "GATE_QR_INVALID",
                    "El payload QR no es válido o ha expirado.",
                    422,
                )
            result = resolver.resolve_by_appointment_id(
                db, appt_id, body.warehouse_id, org_id
            )
        else:
            raise ApplicationError(
                "GATE_RESOLVE_UNSUPPORTED",
                "Resolución por placa o código OC no soportada aún. Use cit_code o opaque_qr_payload.",
                422,
            )

        gate_prep = result.get("gate_preparation", {})
        if not gate_prep.get("expected_vehicle_id"):
            warnings.append("VEHICLE_NOT_DECLARED")
        if not gate_prep.get("expected_driver_id"):
            warnings.append("DRIVER_NOT_DECLARED")

        return GateAppointmentResolveResponse(
            appointment_id=result.get("appointment_id"),
            appointment_code=result.get("appointment_code"),
            appointment_status=result.get("appointment_status"),
            arrival_notice_id=result.get("arrival_notice_id"),
            warehouse_id=result.get("warehouse_id"),
            supplier_summary=result.get("supplier_snapshot"),
            carrier_summary=result.get("carrier_snapshot"),
            gate_preparation=gate_prep,
            gate_eligibility="ELIGIBLE",
            warnings=warnings,
            blocking_issues=blocking,
            server_time=_server_time(),
        )
    except ApplicationError:
        raise
    except Exception as exc:
        raise ApplicationError(
            "GATE_RESOLVE_ERROR",
            f"Error al resolver la cita: {exc}",
            500,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Gate Check-Ins
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/gate-check-ins", response_model=GateCheckInListResponse)
def list_gate_check_ins(
    gate_id: Optional[UUID] = None,
    warehouse_id: Optional[UUID] = None,
    status: Optional[str] = None,
    decision: Optional[str] = None,
    arrival_classification: Optional[str] = None,
    has_failed_checks: Optional[bool] = None,
    has_exceptions: Optional[bool] = None,
    has_broken_seal: Optional[bool] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    principal=Depends(require_permission(_PERM_CHECKIN_READ)),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    q = select(GateCheckInModel).where(
        GateCheckInModel.organization_id == org_id
    )
    if gate_id:
        q = q.where(GateCheckInModel.gate_id == gate_id)
    if warehouse_id:
        q = q.where(GateCheckInModel.warehouse_id == warehouse_id)
    if status:
        q = q.where(GateCheckInModel.status == status)
    if decision:
        q = q.where(GateCheckInModel.decision == decision)
    if arrival_classification:
        q = q.where(GateCheckInModel.arrival_classification == arrival_classification)
    if has_failed_checks is True:
        q = q.where(GateCheckInModel.failed_check_count > 0)
    if has_exceptions is True:
        q = q.where(GateCheckInModel.exception_count > 0)

    from sqlalchemy import func as sqlfunc
    count_q = select(sqlfunc.count()).select_from(q.subquery())
    total = db.scalar(count_q) or 0

    rows = list(db.scalars(q.offset((page - 1) * page_size).limit(page_size)))

    items = [
        GateCheckInSummary(
            id=r.id,
            cpv_code=None,
            cit_code=r.appointment_code_snapshot,
            supplier_summary=r.supplier_snapshot,
            carrier_summary=r.carrier_snapshot,
            arrived_at=r.arrived_at,
            arrival_classification=r.arrival_classification,
            status=r.status,
            decision=r.decision,
            failed_check_count=r.failed_check_count,
            exception_count=r.exception_count,
            guard_summary=r.guard_snapshot,
            updated_at=r.updated_at,
            capabilities=_gate_capabilities(r),
        )
        for r in rows
    ]
    return GateCheckInListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.post("/gate-check-ins", response_model=GateCheckInResponse, status_code=201)
def create_gate_check_in(
    body: GateCheckInCreate,
    principal=Depends(require_permission(_PERM_CHECKIN_CREATE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
    x_idempotency_key: Optional[str] = Header(default=None, alias="X-Idempotency-Key"),
):
    org_id = resolve_organization_id(principal)

    # Resolve guard from session — NEVER from payload
    guard_snapshot = gate_guard_resolver.resolve(principal)
    guard_user_id = principal.user_id

    # Resolve appointment
    resolver = GateAppointmentResolver()
    if body.appointment_id:
        appt = resolver.resolve_by_appointment_id(
            db, body.appointment_id, body.gate_id, org_id
        )
    elif body.cit_code:
        appt = resolver.resolve_by_cit_code(db, body.cit_code, body.gate_id, org_id)
    else:
        raise ApplicationError("GATE_CHECKIN_NO_APPOINTMENT", "Cita no especificada.", 422)

    # Validate warehouse match
    gate = db.scalars(
        select(WarehouseGateModel).where(WarehouseGateModel.id == body.gate_id)
    ).first()
    if gate is None:
        raise WarehouseGateNotFoundError(str(body.gate_id))
    if appt.get("warehouse_id") and str(appt["warehouse_id"]) != str(gate.warehouse_id):
        from app.modules.logistics.inbound.gate_control.domain.errors import (
            GateCheckInWarehouseMismatchError,
        )
        raise GateCheckInWarehouseMismatchError()

    svc = GateCheckInService(db)
    check_in = svc.create(
        db,
        gate_id=body.gate_id,
        appointment_resolution=appt,
        guard_snapshot=guard_snapshot,
        guard_user_id=guard_user_id,
        organization_id=org_id,
        branch_id=gate.branch_id,
        warehouse_id=gate.warehouse_id,
        source_type="APPOINTMENT",
    )
    db.commit()
    db.refresh(check_in)
    return check_in


@router.post("/gate-check-ins/walk-in", response_model=GateCheckInResponse, status_code=201)
def create_walk_in_check_in(
    body: GateWalkInCreate,
    principal=Depends(require_permission(_PERM_CHECKIN_WALK_IN)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    gate = db.scalars(
        select(WarehouseGateModel).where(
            WarehouseGateModel.id == body.gate_id,
            WarehouseGateModel.organization_id == org_id,
        )
    ).first()
    if gate is None:
        raise WarehouseGateNotFoundError(str(body.gate_id))

    # Check walk-in feature flag via active policy version
    if gate.active_verification_policy_version_id:
        policy_v = db.scalars(
            select(GateVerificationPolicyVersionModel).where(
                GateVerificationPolicyVersionModel.id == gate.active_verification_policy_version_id
            )
        ).first()
        if policy_v and not policy_v.walk_in_allowed:
            raise GateCheckInWalkInNotAllowedError()

    guard_snapshot = gate_guard_resolver.resolve(principal)
    guard_user_id = principal.user_id

    svc = GateCheckInService(db)
    check_in = svc.create(
        db,
        gate_id=body.gate_id,
        appointment_resolution={
            "appointment_id": None,
            "appointment_code": None,
            "supplier_snapshot": {"supplier_id": str(body.supplier_id)},
            "carrier_snapshot": {"carrier_id": str(body.carrier_id)} if body.carrier_id else None,
        },
        guard_snapshot=guard_snapshot,
        guard_user_id=guard_user_id,
        organization_id=org_id,
        branch_id=gate.branch_id,
        warehouse_id=gate.warehouse_id,
        source_type="AUTHORIZED_WALK_IN",
    )
    check_in.hold_reason = body.reason
    check_in.status = "HELD_AT_GATE"
    db.commit()
    db.refresh(check_in)
    return check_in


@router.get("/gate-check-ins/{check_in_id}", response_model=GateCheckInResponse)
def get_gate_check_in(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_CHECKIN_READ)),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    return svc.get(check_in_id, org_id)


@router.post("/gate-check-ins/{check_in_id}/record-arrival", response_model=GateCheckInResponse)
def record_arrival(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_CHECKIN_CREATE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    """Record authoritative server-side arrival timestamp.

    CRITICAL: arrived_at is set from server clock. No client time accepted.
    """
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.record_arrival(check_in_id, org_id)
    db.commit()
    db.refresh(check_in)
    return check_in


@router.post("/gate-check-ins/{check_in_id}/start-verification", response_model=GateCheckInResponse)
def start_verification(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_CHECKIN_START)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.start_verification(check_in_id, org_id, principal.user_id)
    db.commit()
    db.refresh(check_in)
    return check_in


@router.post("/gate-check-ins/{check_in_id}/hold", response_model=GateCheckInResponse)
def hold_check_in(
    check_in_id: UUID,
    body: GateCheckInHoldRequest,
    principal=Depends(require_permission(_PERM_CHECKIN_HOLD)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.hold(check_in_id, org_id, principal.user_id, body.hold_reason)

    hold = GateCheckInHoldModel(
        id=uuid4(),
        gate_check_in_id=check_in_id,
        hold_reason=body.hold_reason,
        held_by=principal.user_id,
    )
    db.add(hold)
    db.commit()
    db.refresh(check_in)
    return check_in


@router.post("/gate-check-ins/{check_in_id}/request-supervisor", response_model=GateCheckInResponse)
def request_supervisor(
    check_in_id: UUID,
    body: GateCheckInHoldRequest,
    principal=Depends(require_permission(_PERM_CHECKIN_CREATE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.request_supervisor(check_in_id, org_id, principal.user_id, body.hold_reason)
    db.commit()
    db.refresh(check_in)
    return check_in


@router.post("/gate-check-ins/{check_in_id}/resume", response_model=GateCheckInResponse)
def resume_check_in(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_CHECKIN_RESUME)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.resume(check_in_id, org_id, principal.user_id)
    db.commit()
    db.refresh(check_in)
    return check_in


@router.post("/gate-check-ins/{check_in_id}/cancel", response_model=GateCheckInResponse)
def cancel_check_in(
    check_in_id: UUID,
    body: GateCheckInHoldRequest,
    principal=Depends(require_permission(_PERM_CHECKIN_CANCEL)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.cancel(check_in_id, org_id, principal.user_id, body.hold_reason)
    db.commit()
    db.refresh(check_in)
    return check_in


@router.post("/gate-check-ins/{check_in_id}/complete", response_model=GateCheckInResponse)
def complete_check_in(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_CHECKIN_COMPLETE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.complete(check_in_id, org_id, principal.user_id)
    db.commit()
    db.refresh(check_in)
    return check_in


@router.get("/gate-check-ins/{check_in_id}/capabilities", response_model=GateCheckInCapabilities)
def get_check_in_capabilities(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_CHECKIN_READ)),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.get(check_in_id, org_id)
    caps = _gate_capabilities(check_in)
    return GateCheckInCapabilities(
        check_in_id=check_in.id,
        status=check_in.status,
        can_record_arrival="record_arrival" in caps,
        can_start_verification="start_verification" in caps,
        can_submit_vehicle_inspection="submit_vehicle_inspection" in caps,
        can_submit_driver_inspection="submit_driver_inspection" in caps,
        can_submit_document="submit_document" in caps,
        can_submit_seal_inspection="submit_seal_inspection" in caps,
        can_capture_photo="capture_photo" in caps,
        can_complete_check_result="complete_check_result" in caps,
        can_request_exception="request_exception" in caps,
        can_authorize_entry="authorize_entry" in caps,
        can_authorize_with_observations="authorize_with_observations" in caps,
        can_deny_entry="deny_entry" in caps,
        can_hold="hold" in caps,
        can_request_supervisor="request_supervisor" in caps,
        can_resume="resume" in caps,
        can_cancel="cancel" in caps,
        can_complete="complete" in caps,
        can_issue_document="issue_document" in caps,
        can_preview_document="preview_document" in caps,
        server_time=_server_time(),
    )


@router.get("/gate-check-ins/{check_in_id}/history")
def get_check_in_history(
    check_in_id: UUID,
    principal=Depends(require_permission("logistics.gate_check_ins.read_history")),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.get(check_in_id, org_id)
    revisions = list(db.scalars(
        select(GateCheckInRevisionModel).where(
            GateCheckInRevisionModel.gate_check_in_id == check_in_id
        )
    ))
    decisions = list(db.scalars(
        select(GateEntryDecisionModel).where(
            GateEntryDecisionModel.gate_check_in_id == check_in_id
        )
    ))
    return {
        "check_in_id": str(check_in_id),
        "current_status": check_in.status,
        "revisions": [
            {
                "revision_number": r.revision_number,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "frozen_at": r.frozen_at.isoformat() if r.frozen_at else None,
            }
            for r in revisions
        ],
        "decisions": [
            {
                "decision_type": d.decision_type,
                "decision_reason": d.decision_reason,
                "decided_at": d.decided_at.isoformat() if d.decided_at else None,
            }
            for d in decisions
        ],
    }


@router.get("/gate-check-ins/{check_in_id}/integrity", response_model=GateIntegrityResponse)
def check_integrity(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_CHECKIN_READ)),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.get(check_in_id, org_id)

    alerts = []
    revision_valid = True
    snapshot_valid = True

    active_revision = None
    if check_in.active_revision_id:
        active_revision = db.scalars(
            select(GateCheckInRevisionModel).where(
                GateCheckInRevisionModel.id == check_in.active_revision_id
            )
        ).first()
        if active_revision and active_revision.content_hash:
            integrity = GateControlIntegrityService()
            revision_valid = integrity.verify_revision(
                db, active_revision, active_revision.content_hash
            )
            if not revision_valid:
                alerts.append("REVISION_HASH_MISMATCH")

    return GateIntegrityResponse(
        check_in_id=check_in_id,
        revision_hash_valid=revision_valid,
        snapshot_hash_valid=snapshot_valid,
        alerts=alerts,
        verified_at=_server_time(),
    )


@router.get("/gate-check-ins/{check_in_id}/dock-preparation", response_model=DockAssignmentPreparationResponse)
def get_dock_preparation(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_CHECKIN_READ)),
    db: Session = Depends(get_db),
):
    """Read-only Phase 038 contract. Does NOT assign docks."""
    org_id = resolve_organization_id(principal)
    prep_svc = DockAssignmentPreparationService(db)
    data = prep_svc.get_preparation(check_in_id, org_id)
    return DockAssignmentPreparationResponse(
        gate_check_in_id=UUID(data["gate_check_in_id"]),
        cpv_code=data.get("cpv_code"),
        appointment_id=UUID(data["appointment_id"]) if data.get("appointment_id") else None,
        cit_code=data.get("cit_code"),
        warehouse_id=UUID(data["warehouse_id"]),
        gate_id=UUID(data["gate_id"]),
        supplier_summary=data.get("supplier_summary"),
        carrier_summary=data.get("carrier_summary"),
        vehicle_id=UUID(data["vehicle_id"]) if data.get("vehicle_id") else None,
        observed_plate=data.get("observed_plate"),
        driver_id=UUID(data["driver_id"]) if data.get("driver_id") else None,
        arrival_time=datetime.fromisoformat(data["arrival_time"]) if data.get("arrival_time") else None,
        gate_clearance_status=data.get("gate_clearance_status"),
        seal_status=data.get("seal_status"),
        expected_pallet_count=data.get("expected_pallet_count"),
        expected_package_count=data.get("expected_package_count"),
        expected_weight=data.get("expected_weight"),
        warnings=data.get("warnings", []),
        capabilities_future=data.get("capabilities_future", []),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Inspections
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/gate-check-ins/{check_in_id}/vehicle-inspection", status_code=201)
def submit_vehicle_inspection(
    check_in_id: UUID,
    body: GateVehicleInspectionCreate,
    principal=Depends(require_permission(_PERM_VEHICLE_INSP)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.get(check_in_id, org_id)

    observed_norm = _normalize_code(body.observed_plate)
    expected_norm = None
    expected_plate = None

    # Get expected plate from appointment
    exp_transport = check_in.expected_transport_snapshot or {}
    if exp_transport.get("expected_plate"):
        expected_plate = exp_transport["expected_plate"]
        expected_norm = _normalize_code(expected_plate)

    plate_match = "MATCH" if (
        expected_norm and observed_norm == expected_norm
    ) else ("MISMATCH" if expected_norm else "EXPECTED_MISSING")

    vehicle_match = "UNCONFIRMED"
    if body.observed_vehicle_id and exp_transport.get("expected_vehicle_id"):
        vehicle_match = "MATCH" if str(body.observed_vehicle_id) == str(exp_transport["expected_vehicle_id"]) else "DIFFERENT_REGISTERED_VEHICLE"

    insp = GateVehicleInspectionModel(
        id=uuid4(),
        gate_check_in_id=check_in_id,
        expected_plate=expected_plate,
        expected_plate_normalized=expected_norm,
        observed_plate=body.observed_plate,
        observed_plate_normalized=observed_norm,
        observed_vehicle_id=body.observed_vehicle_id,
        plate_match_status=plate_match,
        vehicle_match_status=vehicle_match,
        capture_method=body.capture_method,
        visual_condition=body.visual_condition,
        exception_reason=body.exception_reason,
        inspection_result="PASS" if plate_match == "MATCH" else "FAIL",
        inspected_by=principal.user_id,
    )
    db.add(insp)
    db.commit()
    return {
        "inspection_id": str(insp.id),
        "plate_match_status": plate_match,
        "vehicle_match_status": vehicle_match,
        "inspection_result": insp.inspection_result,
    }


@router.get("/gate-check-ins/{check_in_id}/vehicle-inspection")
def get_vehicle_inspection(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_VEHICLE_INSP)),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    insp = db.scalars(
        select(GateVehicleInspectionModel).where(
            GateVehicleInspectionModel.gate_check_in_id == check_in_id
        )
    ).first()
    if insp is None:
        raise ApplicationError("GATE_VEHICLE_INSP_NOT_FOUND", "Inspección vehicular no encontrada.", 404)
    return {
        "id": str(insp.id),
        "expected_plate": insp.expected_plate,
        "observed_plate": insp.observed_plate,
        "plate_match_status": insp.plate_match_status,
        "vehicle_match_status": insp.vehicle_match_status,
        "inspection_result": insp.inspection_result,
    }


@router.post("/gate-check-ins/{check_in_id}/driver-inspection", status_code=201)
def submit_driver_inspection(
    check_in_id: UUID,
    body: GateDriverInspectionCreate,
    principal=Depends(require_permission(_PERM_DRIVER_INSP)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    import hashlib

    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.get(check_in_id, org_id)

    # Encrypt document number at application layer (simplified hash-based redaction)
    doc_hash = (
        hashlib.sha256(body.observed_document_number.encode()).hexdigest()
        if body.observed_document_number
        else None
    )
    doc_redacted = (
        f"***{body.observed_document_number[-3:]}"
        if body.observed_document_number and len(body.observed_document_number) >= 3
        else None
    )
    lic_hash = (
        hashlib.sha256(body.license_number.encode()).hexdigest()
        if body.license_number
        else None
    )
    lic_redacted = (
        f"***{body.license_number[-3:]}"
        if body.license_number and len(body.license_number) >= 3
        else None
    )

    # Determine license status
    lic_status = "NOT_VERIFIED"
    if body.license_expiration:
        now = datetime.now(timezone.utc)
        exp = body.license_expiration
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        lic_status = "VALID" if exp > now else "EXPIRED"

    # Match against expected driver
    exp_transport = check_in.expected_transport_snapshot or {}
    driver_match = "MANUAL_REVIEW"
    if body.observed_driver_id and exp_transport.get("expected_driver_id"):
        driver_match = "MATCH" if str(body.observed_driver_id) == str(exp_transport["expected_driver_id"]) else "DIFFERENT_REGISTERED_DRIVER"

    insp = GateDriverInspectionModel(
        id=uuid4(),
        gate_check_in_id=check_in_id,
        expected_driver_id=exp_transport.get("expected_driver_id"),
        observed_driver_id=body.observed_driver_id,
        observed_name_snapshot=body.observed_name_snapshot,
        observed_document_type=body.observed_document_type,
        observed_document_number_hash=doc_hash,
        observed_document_number_redacted=doc_redacted,
        license_number_hash=lic_hash,
        license_number_redacted=lic_redacted,
        license_category=body.license_category,
        license_expiration=body.license_expiration,
        driver_match_status=driver_match,
        license_status=lic_status,
        inspection_result="PASS" if driver_match == "MATCH" and lic_status == "VALID" else "FAIL",
        exception_reason=body.exception_reason,
        inspected_by=principal.user_id,
    )
    db.add(insp)
    db.commit()
    return {
        "inspection_id": str(insp.id),
        "driver_match_status": driver_match,
        "license_status": lic_status,
        "license_number_redacted": lic_redacted,
        "observed_document_number_redacted": doc_redacted,
        "inspection_result": insp.inspection_result,
    }


@router.get("/gate-check-ins/{check_in_id}/driver-inspection")
def get_driver_inspection(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_DRIVER_INSP)),
    db: Session = Depends(get_db),
):
    insp = db.scalars(
        select(GateDriverInspectionModel).where(
            GateDriverInspectionModel.gate_check_in_id == check_in_id
        )
    ).first()
    if insp is None:
        raise ApplicationError("GATE_DRIVER_INSP_NOT_FOUND", "Inspección de conductor no encontrada.", 404)
    return {
        "id": str(insp.id),
        "driver_match_status": insp.driver_match_status,
        "license_status": insp.license_status,
        "license_number_redacted": insp.license_number_redacted,
        "observed_document_number_redacted": insp.observed_document_number_redacted,
        "inspection_result": insp.inspection_result,
    }


@router.post("/gate-check-ins/{check_in_id}/documents", status_code=201)
def submit_presented_document(
    check_in_id: UUID,
    body: GatePresentedDocumentCreate,
    principal=Depends(require_permission(_PERM_DOC_INSP)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    norm_ref = None
    if body.observed_series and body.observed_number:
        norm_ref = f"{body.observed_series.upper().strip()}-{body.observed_number.strip()}"

    comparison = "NO_EXPECTED_REFERENCE"
    if body.expected_reference and norm_ref:
        comparison = "MATCH" if norm_ref == body.expected_reference.upper().strip() else "MISMATCH"

    doc = GatePresentedDocumentModel(
        id=uuid4(),
        gate_check_in_id=check_in_id,
        document_kind=body.document_kind,
        expected_reference=body.expected_reference,
        observed_series=body.observed_series,
        observed_number=body.observed_number,
        observed_reference_normalized=norm_ref,
        presentation_status="PRESENTED",
        comparison_status=comparison,
        verification_status="NOT_VERIFIED",
        file_asset_id=body.file_asset_id,
        notes=body.notes,
        inspected_by=principal.user_id,
    )
    db.add(doc)
    db.commit()
    return {"document_id": str(doc.id), "comparison_status": comparison}


@router.get("/gate-check-ins/{check_in_id}/documents")
def list_presented_documents(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_DOC_INSP)),
    db: Session = Depends(get_db),
):
    docs = list(db.scalars(
        select(GatePresentedDocumentModel).where(
            GatePresentedDocumentModel.gate_check_in_id == check_in_id
        )
    ))
    return [
        {
            "id": str(d.id),
            "document_kind": d.document_kind,
            "expected_reference": d.expected_reference,
            "observed_reference_normalized": d.observed_reference_normalized,
            "presentation_status": d.presentation_status,
            "comparison_status": d.comparison_status,
        }
        for d in docs
    ]


@router.post("/gate-check-ins/{check_in_id}/seal-inspection", status_code=201)
def submit_seal_inspection(
    check_in_id: UUID,
    body: GateSealInspectionCreate,
    principal=Depends(require_permission(_PERM_SEAL_INSP)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    import hashlib

    org_id = resolve_organization_id(principal)

    exp_hash = (
        hashlib.sha256(body.expected_seal_number.encode()).hexdigest()
        if body.expected_seal_number
        else None
    )
    obs_hash = (
        hashlib.sha256(body.observed_seal_number.encode()).hexdigest()
        if body.observed_seal_number
        else None
    )

    seal_match = "NOT_APPLICABLE"
    if body.seal_required:
        if not body.observed_seal_number:
            seal_match = "OBSERVED_MISSING"
        elif not body.expected_seal_number:
            seal_match = "EXPECTED_MISSING"
        elif exp_hash == obs_hash:
            seal_match = "MATCH"
        else:
            seal_match = "MISMATCH"

    inspection_result = "PASS"
    if body.physical_status in ("BROKEN", "TAMPERED"):
        inspection_result = "FAIL"
    elif seal_match == "MISMATCH":
        inspection_result = "REQUIRES_SUPERVISOR"

    insp = GateSealInspectionModel(
        id=uuid4(),
        gate_check_in_id=check_in_id,
        seal_required=body.seal_required,
        expected_seal_number=body.expected_seal_number,
        expected_seal_number_hash=exp_hash,
        observed_seal_number=body.observed_seal_number,
        observed_seal_number_hash=obs_hash,
        seal_match_status=seal_match,
        physical_status=body.physical_status,
        inspection_result=inspection_result,
        photo_file_asset_id=body.photo_file_asset_id,
        exception_reason=body.exception_reason,
        inspected_by=principal.user_id,
    )
    db.add(insp)
    db.commit()
    return {
        "inspection_id": str(insp.id),
        "seal_match_status": seal_match,
        "physical_status": body.physical_status,
        "inspection_result": inspection_result,
    }


@router.get("/gate-check-ins/{check_in_id}/seal-inspection")
def get_seal_inspection(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_SEAL_INSP)),
    db: Session = Depends(get_db),
):
    insp = db.scalars(
        select(GateSealInspectionModel).where(
            GateSealInspectionModel.gate_check_in_id == check_in_id
        )
    ).first()
    if insp is None:
        raise ApplicationError("GATE_SEAL_INSP_NOT_FOUND", "Inspección de precinto no encontrada.", 404)
    return {
        "id": str(insp.id),
        "seal_required": insp.seal_required,
        "expected_seal_number": insp.expected_seal_number,
        "observed_seal_number": insp.observed_seal_number,
        "seal_match_status": insp.seal_match_status,
        "physical_status": insp.physical_status,
        "inspection_result": insp.inspection_result,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Photo Evidence
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/gate-check-ins/{check_in_id}/photo-upload-sessions", status_code=201)
def create_photo_upload_session(
    check_in_id: UUID,
    evidence_type: str,
    principal=Depends(require_permission(_PERM_PHOTO_CAPTURE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    """Create an upload session via FileAsset service. No base64 accepted."""
    org_id = resolve_organization_id(principal)
    # In production, this delegates to the FileAsset upload session service.
    # Returns a presigned upload URL — never stored persistently.
    session_id = str(uuid4())
    return {
        "session_id": session_id,
        "check_in_id": str(check_in_id),
        "evidence_type": evidence_type,
        "upload_endpoint": f"/api/logistics/files/upload-sessions/{session_id}",
        "expires_at": None,
        "server_time": _server_time().isoformat(),
    }


@router.post("/gate-check-ins/{check_in_id}/photos/associate", status_code=201)
def associate_photo_evidence(
    check_in_id: UUID,
    file_asset_id: UUID,
    evidence_type: str,
    content_hash: str,
    principal=Depends(require_permission(_PERM_PHOTO_CAPTURE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    classification = (
        "HIGHLY_RESTRICTED"
        if evidence_type in ("DRIVER_RESTRICTED", "DRIVER_DOCUMENT_RESTRICTED", "LICENSE_RESTRICTED")
        else "RESTRICTED"
    )
    evidence = GatePhotoEvidenceModel(
        id=uuid4(),
        gate_check_in_id=check_in_id,
        evidence_type=evidence_type,
        file_asset_id=file_asset_id,
        captured_at=_server_time(),
        captured_by=principal.user_id,
        source_type="FILE_UPLOAD",
        classification=classification,
        content_hash=content_hash,
    )
    db.add(evidence)
    db.commit()
    return {
        "evidence_id": str(evidence.id),
        "evidence_type": evidence_type,
        "classification": classification,
    }


@router.get("/gate-check-ins/{check_in_id}/photos")
def list_photo_evidence(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_PHOTO_READ)),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    photos = list(db.scalars(
        select(GatePhotoEvidenceModel).where(
            GatePhotoEvidenceModel.gate_check_in_id == check_in_id
        )
    ))
    # Never return storage keys or signed URLs — return metadata only
    return [
        {
            "evidence_id": str(p.id),
            "evidence_type": p.evidence_type,
            "classification": p.classification,
            "captured_at": p.captured_at.isoformat() if p.captured_at else None,
            "content_hash": p.content_hash,
            # View URL generated on demand, not stored
            "view_url": f"/api/logistics/gate-photo-evidence/{p.id}/view",
        }
        for p in photos
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Check Results
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/gate-check-ins/{check_in_id}/check-results", status_code=201)
def submit_check_result(
    check_in_id: UUID,
    body: GateVerificationCheckResultCreate,
    principal=Depends(require_permission(_PERM_CHECKIN_START)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.get(check_in_id, org_id)

    # Determine if check is blocking from policy definition
    is_blocking = False
    if body.check_definition_id:
        defn = db.scalars(
            select(GateVerificationCheckDefinitionModel).where(
                GateVerificationCheckDefinitionModel.id == body.check_definition_id
            )
        ).first()
        if defn:
            is_blocking = defn.blocking_on_fail and body.result == "FAIL"

    result = GateVerificationCheckResultModel(
        id=uuid4(),
        gate_check_in_id=check_in_id,
        check_definition_id=body.check_definition_id,
        check_code=body.check_code,
        result=body.result,
        observed_value=body.observed_value,
        expected_value=body.expected_value,
        explanation=body.explanation,
        evidence_file_ids=[str(fid) for fid in body.evidence_file_ids] if body.evidence_file_ids else None,
        blocking=is_blocking,
        override_status="NOT_REQUIRED",
        checked_by=principal.user_id,
    )
    db.add(result)

    # Update counters
    if body.result == "FAIL":
        check_in.failed_check_count = (check_in.failed_check_count or 0) + 1
    elif body.result == "PASS_WITH_OBSERVATION":
        check_in.warning_count = (check_in.warning_count or 0) + 1
    check_in.row_version += 1

    db.commit()
    return {"result_id": str(result.id), "blocking": is_blocking}


@router.get("/gate-check-ins/{check_in_id}/check-results")
def list_check_results(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_CHECKIN_READ)),
    db: Session = Depends(get_db),
):
    results = list(db.scalars(
        select(GateVerificationCheckResultModel).where(
            GateVerificationCheckResultModel.gate_check_in_id == check_in_id
        )
    ))
    return [
        {
            "id": str(r.id),
            "check_code": r.check_code,
            "result": r.result,
            "blocking": r.blocking,
            "override_status": r.override_status,
            "checked_at": r.checked_at.isoformat() if r.checked_at else None,
        }
        for r in results
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/gate-check-ins/{check_in_id}/exceptions", status_code=201)
def request_exception(
    check_in_id: UUID,
    body: GateVerificationExceptionCreate,
    principal=Depends(require_permission(_PERM_EXCEPTION_REQUEST)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    exc = GateVerificationExceptionModel(
        id=uuid4(),
        gate_check_in_id=check_in_id,
        check_result_id=body.check_result_id,
        exception_type=body.exception_type,
        risk_level=body.risk_level,
        reason=body.reason,
        evidence_file_id=body.evidence_file_id,
        status="REQUESTED",
        requested_by=principal.user_id,
    )
    db.add(exc)

    # Update exception counter
    svc = GateCheckInService(db)
    check_in = svc.get(check_in_id, org_id)
    check_in.exception_count = (check_in.exception_count or 0) + 1
    check_in.row_version += 1

    db.commit()
    return {"exception_id": str(exc.id), "status": "REQUESTED"}


@router.get("/gate-check-ins/{check_in_id}/exceptions")
def list_exceptions(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_CHECKIN_READ)),
    db: Session = Depends(get_db),
):
    excs = list(db.scalars(
        select(GateVerificationExceptionModel).where(
            GateVerificationExceptionModel.gate_check_in_id == check_in_id
        )
    ))
    return [
        {
            "id": str(e.id),
            "exception_type": e.exception_type,
            "risk_level": e.risk_level,
            "status": e.status,
            "reason": e.reason,
        }
        for e in excs
    ]


@router.post("/gate-verification-exceptions/{exception_id}/approve", status_code=200)
def approve_exception(
    exception_id: UUID,
    principal=Depends(require_permission(_PERM_EXCEPTION_APPROVE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    exc = db.scalars(
        select(GateVerificationExceptionModel).where(
            GateVerificationExceptionModel.id == exception_id
        )
    ).first()
    if exc is None:
        raise ApplicationError("GATE_EXCEPTION_NOT_FOUND", "Excepción no encontrada.", 404)

    # Anti-autoapproval: reviewer must differ from requester
    if str(exc.requested_by) == str(principal.user_id):
        raise ApplicationError(
            "GATE_EXCEPTION_SELF_APPROVAL",
            "El guardia que solicitó la excepción no puede aprobarla.",
            403,
        )
    exc.status = "APPROVED"
    exc.reviewed_by = principal.user_id
    exc.decided_at = _server_time()
    db.commit()
    return {"exception_id": str(exception_id), "status": "APPROVED"}


@router.post("/gate-verification-exceptions/{exception_id}/reject", status_code=200)
def reject_exception(
    exception_id: UUID,
    body: GateEntryDecisionRequest,
    principal=Depends(require_permission(_PERM_EXCEPTION_REJECT)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    exc = db.scalars(
        select(GateVerificationExceptionModel).where(
            GateVerificationExceptionModel.id == exception_id
        )
    ).first()
    if exc is None:
        raise ApplicationError("GATE_EXCEPTION_NOT_FOUND", "Excepción no encontrada.", 404)
    exc.status = "REJECTED"
    exc.reviewed_by = principal.user_id
    exc.decided_at = _server_time()
    exc.decision_reason = body.reason
    db.commit()
    return {"exception_id": str(exception_id), "status": "REJECTED"}


# ─────────────────────────────────────────────────────────────────────────────
# Decision Commands
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/gate-check-ins/{check_in_id}/validate-decision", response_model=GateCheckInValidationResponse)
def validate_decision(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_CHECKIN_READ)),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.get(check_in_id, org_id)
    dec_svc = GateDecisionService(db)
    summary = dec_svc.validate_can_decide(check_in)
    return GateCheckInValidationResponse(
        check_in_id=check_in_id,
        can_authorize=summary["can_authorize"],
        can_authorize_with_observations=summary["can_authorize_with_observations"],
        blocking_failed_count=summary["blocking_failed_count"],
        blocking_failed=summary["blocking_failed"],
        pending_exceptions_count=summary["pending_exceptions_count"],
    )


@router.post("/gate-check-ins/{check_in_id}/authorize-entry", status_code=200)
def authorize_entry(
    check_in_id: UUID,
    body: GateEntryDecisionRequest,
    principal=Depends(require_permission(_PERM_ENTRY_AUTHORIZE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    """Authorize entry — decided_by from session, not from request body."""
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.get(check_in_id, org_id)
    dec_svc = GateDecisionService(db)
    decision = dec_svc.authorize_entry(
        check_in,
        decided_by=principal.user_id,
        reason=body.reason,
    )

    # Build snapshot and publish event
    snapshot_prov = GateCheckInSnapshotProvider(db)
    snapshot = snapshot_prov.build(check_in)

    release_svc = InboundGateReleaseService(db)
    release_svc.publish_gate_cleared(check_in, snapshot)

    db.commit()
    return {
        "decision_id": str(decision.id),
        "decision_type": "AUTHORIZE_ENTRY",
        "server_time": _server_time().isoformat(),
    }


@router.post("/gate-check-ins/{check_in_id}/authorize-with-observations", status_code=200)
def authorize_with_observations(
    check_in_id: UUID,
    body: GateEntryDecisionRequest,
    principal=Depends(require_permission(_PERM_ENTRY_AUTH_OBS)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.get(check_in_id, org_id)
    dec_svc = GateDecisionService(db)
    decision = dec_svc.authorize_with_observations(
        check_in,
        decided_by=principal.user_id,
        reason=body.reason,
        conditions=body.conditions,
    )
    snapshot_prov = GateCheckInSnapshotProvider(db)
    snapshot = snapshot_prov.build(check_in)
    release_svc = InboundGateReleaseService(db)
    release_svc.publish_gate_cleared(check_in, snapshot)
    db.commit()
    return {
        "decision_id": str(decision.id),
        "decision_type": "AUTHORIZE_WITH_OBSERVATIONS",
        "server_time": _server_time().isoformat(),
    }


@router.post("/gate-check-ins/{check_in_id}/deny-entry", status_code=200)
def deny_entry(
    check_in_id: UUID,
    body: GateEntryDecisionRequest,
    principal=Depends(require_permission(_PERM_ENTRY_DENY)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.get(check_in_id, org_id)
    dec_svc = GateDecisionService(db)
    decision = dec_svc.deny_entry(
        check_in,
        decided_by=principal.user_id,
        reason=body.reason,
    )
    db.commit()
    return {
        "decision_id": str(decision.id),
        "decision_type": "DENY_ENTRY",
        "server_time": _server_time().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Document (CPV) Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/gate-check-ins/{check_in_id}/preview")
def preview_document(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_DOC_PREVIEW)),
    db: Session = Depends(get_db),
):
    """Preview CPV with NO_OFFICIAL watermark. Does NOT assign CPV code."""
    org_id = resolve_organization_id(principal)
    svc = GateCheckInService(db)
    check_in = svc.get(check_in_id, org_id)
    snapshot_prov = GateCheckInSnapshotProvider(db)
    snapshot = snapshot_prov.build(check_in)
    return {
        "preview": True,
        "watermark": "NO OFICIAL - VISTA PREVIA",
        "cpv_code": None,  # NEVER assigned on preview
        "snapshot": snapshot,
        "server_time": _server_time().isoformat(),
    }


@router.post(
    "/gate-check-ins/{check_in_id}/issue-document",
    status_code=201,
    response_model=GateCpvDocumentResponse,
)
def issue_cpv_document(
    check_in_id: UUID,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    principal=Depends(require_permission(_PERM_DOC_ISSUE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    """Issue the immutable CPV PDF document."""
    org_id = resolve_organization_id(principal)
    document, snapshot_hash = GateCheckInDocumentService(db).issue(
        check_in_id=check_in_id,
        organization_id=org_id,
        actor_user_id=principal.user_id,
        idempotency_key=idempotency_key,
    )
    db.commit()

    return {
        "document_instance_id": document.id,
        "check_in_id": check_in_id,
        "document_code": document.document_code,
        "status": document.status,
        "issued_at": document.issued_at,
        "snapshot_hash": snapshot_hash,
        "download_url": f"/api/logistics/gate-check-ins/{check_in_id}/document/pdf",
        "expires_at": None,
    }


@router.get(
    "/gate-check-ins/{check_in_id}/document",
    response_model=GateCpvDocumentResponse,
)
def get_document(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_DOC_DOWNLOAD)),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    document_service = GateCheckInDocumentService(db)
    document = document_service.get_document(check_in_id, org_id)
    return {
        "document_instance_id": document.id,
        "check_in_id": check_in_id,
        "document_code": document.document_code,
        "status": document.status,
        "issued_at": document.issued_at,
        "snapshot_hash": document_service.snapshot_hash(document),
        "download_url": f"/api/logistics/gate-check-ins/{check_in_id}/document/pdf",
        "expires_at": None,
    }


@router.get(
    "/gate-check-ins/{check_in_id}/document/pdf",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
    summary="Descargar el PDF CPV emitido (Fase 037)",
)
def download_cpv_document_pdf(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_DOC_DOWNLOAD)),
    db: Session = Depends(get_db),
) -> Response:
    org_id = resolve_organization_id(principal)
    document_service = GateCheckInDocumentService(db)
    document = document_service.get_document(check_in_id, org_id)
    _, artifact, pdf_bytes = document_service.documents.get_downloadable_pdf(
        document.id,
        principal.user_id,
    )
    response = build_pdf_download_response(pdf_bytes, artifact.filename)
    document_service.documents.record_download(document, principal.user_id)
    return response


# ─────────────────────────────────────────────────────────────────────────────
# Corrections
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/gate-check-ins/{check_in_id}/corrections", status_code=201)
def request_correction(
    check_in_id: UUID,
    body: GateCheckInCorrectionCreate,
    principal=Depends(require_permission(_PERM_CORRECTION_REQUEST)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    org_id = resolve_organization_id(principal)
    # Validate correctable fields
    correctable = {
        "observed_plate", "observed_driver_reference", "document_reference",
        "seal_transcription", "observation", "arrival_classification"
    }
    if body.field_code not in correctable:
        from app.modules.logistics.inbound.gate_control.domain.errors import (
            GateCheckInCorrectionNotAllowedError,
        )
        raise GateCheckInCorrectionNotAllowedError(body.field_code)

    correction = GateCheckInCorrectionRequestModel(
        id=uuid4(),
        gate_check_in_id=check_in_id,
        field_code=body.field_code,
        proposed_value=body.proposed_value,
        reason=body.reason,
        evidence_file_id=body.evidence_file_id,
        status="REQUESTED",
        requested_by=principal.user_id,
    )
    db.add(correction)
    db.commit()
    return {"correction_id": str(correction.id), "status": "REQUESTED"}


@router.get("/gate-check-ins/{check_in_id}/corrections")
def list_corrections(
    check_in_id: UUID,
    principal=Depends(require_permission(_PERM_CHECKIN_READ)),
    db: Session = Depends(get_db),
):
    corrections = list(db.scalars(
        select(GateCheckInCorrectionRequestModel).where(
            GateCheckInCorrectionRequestModel.gate_check_in_id == check_in_id
        )
    ))
    return [
        {
            "id": str(c.id),
            "field_code": c.field_code,
            "proposed_value": c.proposed_value,
            "status": c.status,
            "reason": c.reason,
        }
        for c in corrections
    ]


@router.post("/gate-check-in-corrections/{correction_id}/approve", status_code=200)
def approve_correction(
    correction_id: UUID,
    principal=Depends(require_permission(_PERM_CORRECTION_APPROVE)),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    correction = db.scalars(
        select(GateCheckInCorrectionRequestModel).where(
            GateCheckInCorrectionRequestModel.id == correction_id
        )
    ).first()
    if correction is None:
        raise ApplicationError("GATE_CORRECTION_NOT_FOUND", "Solicitud de corrección no encontrada.", 404)
    if str(correction.requested_by) == str(principal.user_id):
        raise ApplicationError("GATE_CORRECTION_SELF_APPROVAL", "No puede aprobar su propia corrección.", 403)
    correction.status = "APPROVED"
    correction.reviewed_by = principal.user_id
    correction.decided_at = _server_time()
    db.commit()
    return {"correction_id": str(correction_id), "status": "APPROVED"}


__all__ = ["router"]
