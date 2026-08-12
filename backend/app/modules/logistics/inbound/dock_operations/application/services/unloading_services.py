"""Unloading readiness, responsibility, seal, execution, metrics, and handover."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeExpectedLineModel,
    ArrivalNoticeModel,
    ArrivalNoticePurchaseOrderReferenceModel,
    ArrivalNoticeRevisionModel,
    ArrivalNoticeTransportDocumentModel,
)
from app.modules.logistics.inbound.dock_operations.application.services.common import (
    UnloadingOperationalEventService,
    actor_snapshot,
    server_now,
    sha256_payload,
)
from app.modules.logistics.inbound.dock_operations.application.services.dock_services import (
    DockAssignmentService,
    DockOccupancyService,
    WarehouseDockAvailabilityService,
    WarehouseDockService,
    _as_json,
)
from app.modules.logistics.inbound.dock_operations.domain.enums import (
    ACTIVE_UNLOADING_STATUSES,
    CheckResult,
    DockAssignmentStatus,
    DockOperationalEventType,
    OperationalTimeQualityStatus,
    PauseStatus,
    QueueStatus,
    ReadinessStatus,
    UnloadingStatus,
)
from app.modules.logistics.inbound.dock_operations.domain.errors import (
    UnloadingOperationNotFound,
    conflict,
    invalid,
)
from app.modules.logistics.inbound.dock_operations.domain.policies.state_machine import (
    ASSIGNMENT_TRANSITIONS,
    UNLOADING_TRANSITIONS,
    require_transition,
)
from app.modules.logistics.inbound.dock_operations.domain.services.metrics import (
    DockOperationalMetricsService,
)
from app.modules.logistics.inbound.dock_operations.infrastructure.persistence.models import (
    DockOperationMetricsProjectionModel,
    DockOperationalEventModel,
    DockOperationalTimeCorrectionModel,
    InboundDockAssignmentModel,
    InboundDockQueueEntryModel,
    UnloadingCompletionCheckDefinitionModel,
    UnloadingCompletionCheckResultModel,
    UnloadingEquipmentAssignmentModel,
    UnloadingOperationModel,
    UnloadingPauseModel,
    UnloadingReadinessCheckDefinitionModel,
    UnloadingReadinessCheckResultModel,
    UnloadingResponsibleAssignmentModel,
    UnloadingSealOpeningEventModel,
)
from app.modules.logistics.inbound.gate_control.application.services import (
    DockAssignmentPreparationService,
)
from app.modules.logistics.inbound.gate_control.infrastructure.persistence.models import (
    GateCheckInModel,
    GateSealInspectionModel,
)
from app.modules.logistics.partners.models import BusinessPartnerModel
from app.modules.logistics.principal import LogisticsPrincipal


_READINESS_DEFINITIONS = (
    ("GATE_CLEARANCE_VALID", True, True, False, False),
    ("VEHICLE_AT_ASSIGNED_DOCK", True, True, False, False),
    ("DOCK_OPERATIONAL", True, True, False, False),
    ("DOCK_AREA_CLEAR", True, True, False, True),
    ("VEHICLE_SECURED", True, True, False, True),
    ("WHEEL_CHOCKS_CONFIRMED", True, True, False, True),
    ("DOCK_LEVELER_READY", False, True, False, True),
    ("TEAM_ASSIGNED", True, True, False, False),
    ("SUPERVISOR_IDENTIFIED", True, True, False, False),
    ("REQUIRED_EQUIPMENT_AVAILABLE", True, True, False, True),
    ("REQUIRED_DOCUMENTS_AVAILABLE", True, True, False, True),
    ("SEAL_STATUS_REVIEWED", True, True, False, True),
    ("SPECIAL_HANDLING_ACKNOWLEDGED", False, True, False, True),
    ("PPE_ACKNOWLEDGED", True, True, False, True),
    ("EMERGENCY_PATH_CLEAR", True, True, False, True),
    ("RECEIVING_SCAN_HANDOVER_PREPARED", True, False, False, True),
)

_COMPLETION_DEFINITIONS = (
    "UNLOADING_ACTIVITY_STOPPED",
    "VEHICLE_LOAD_AREA_REVIEWED",
    "DOCK_AREA_SAFE",
    "EQUIPMENT_RETURNED",
    "DOCUMENTS_HANDED_OVER",
    "RECEIVING_SCAN_READY",
    "EXCEPTIONS_RECORDED",
    "VEHICLE_READY_FOR_RELEASE",
    "RESPONSIBLES_CONFIRMED",
)

_SEAL_ANOMALIES = {
    "NUMBER_MISMATCH",
    "PREVIOUSLY_BROKEN",
    "TAMPERING_SUSPECTED",
}


class UnloadingReadinessService:
    def __init__(self, db: Session):
        self.db = db
        self.events = UnloadingOperationalEventService(db)

    def ensure_definitions(self, operation: UnloadingOperationModel) -> list[UnloadingReadinessCheckDefinitionModel]:
        rows = list(
            self.db.scalars(
                select(UnloadingReadinessCheckDefinitionModel).where(
                    UnloadingReadinessCheckDefinitionModel.organization_id == operation.organization_id,
                    UnloadingReadinessCheckDefinitionModel.dock_id == operation.dock_id,
                    UnloadingReadinessCheckDefinitionModel.status == "ACTIVE",
                )
            )
        )
        if rows:
            return rows
        for index, (code, required, blocking, evidence, override) in enumerate(_READINESS_DEFINITIONS, 1):
            self.db.add(
                UnloadingReadinessCheckDefinitionModel(
                    id=uuid4(),
                    organization_id=operation.organization_id,
                    warehouse_id=operation.warehouse_id,
                    dock_id=operation.dock_id,
                    check_code=code,
                    name=code.replace("_", " ").title(),
                    description=f"Comprobación operativa configurable: {code}",
                    order_index=index,
                    required=required,
                    blocking_on_fail=blocking,
                    requires_evidence=evidence,
                    allow_override=override,
                    status="ACTIVE",
                )
            )
        self.db.flush()
        return list(
            self.db.scalars(
                select(UnloadingReadinessCheckDefinitionModel).where(
                    UnloadingReadinessCheckDefinitionModel.organization_id == operation.organization_id,
                    UnloadingReadinessCheckDefinitionModel.dock_id == operation.dock_id,
                    UnloadingReadinessCheckDefinitionModel.status == "ACTIVE",
                )
            )
        )

    def record(
        self,
        operation: UnloadingOperationModel,
        principal: LogisticsPrincipal,
        check_definition_id: UUID,
        result: str,
        observation: str | None,
        evidence_file_id: UUID | None,
    ) -> UnloadingReadinessCheckResultModel:
        definition = self.db.scalar(
            select(UnloadingReadinessCheckDefinitionModel).where(
                UnloadingReadinessCheckDefinitionModel.id == check_definition_id,
                UnloadingReadinessCheckDefinitionModel.organization_id == operation.organization_id,
                UnloadingReadinessCheckDefinitionModel.status == "ACTIVE",
            )
        )
        if definition is None:
            raise invalid("READINESS_CHECK_NOT_FOUND", "Comprobación de readiness no encontrada.")
        if definition.requires_evidence and evidence_file_id is None:
            raise invalid("READINESS_EVIDENCE_REQUIRED", "La comprobación requiere evidencia.")
        existing = self.db.scalar(
            select(UnloadingReadinessCheckResultModel.id).where(
                UnloadingReadinessCheckResultModel.unloading_operation_id == operation.id,
                UnloadingReadinessCheckResultModel.check_code == definition.check_code,
            )
        )
        if existing:
            raise conflict("READINESS_RESULT_ALREADY_RECORDED", "El resultado es inmutable; solicite un override o corrección.")
        row = UnloadingReadinessCheckResultModel(
            id=uuid4(),
            unloading_operation_id=operation.id,
            check_definition_id=definition.id,
            check_code=definition.check_code,
            result=result,
            observation=observation,
            evidence_file_id=evidence_file_id,
            blocking=definition.blocking_on_fail and result in {CheckResult.FAIL.value, CheckResult.REQUIRES_REVIEW.value},
            override_status="NOT_REQUESTED",
            checked_by=principal.user_id,
            checked_at=server_now(),
        )
        self.db.add(row)
        operation.status = UnloadingStatus.READINESS_PENDING.value
        operation.readiness_status = ReadinessStatus.IN_PROGRESS.value
        operation.row_version += 1
        self.db.flush()
        return row

    def validate(
        self,
        operation: UnloadingOperationModel,
        assignment: InboundDockAssignmentModel,
        principal: LogisticsPrincipal,
    ) -> UnloadingOperationModel:
        definitions = self.ensure_definitions(operation)
        results = list(
            self.db.scalars(
                select(UnloadingReadinessCheckResultModel).where(
                    UnloadingReadinessCheckResultModel.unloading_operation_id == operation.id
                )
            )
        )
        by_code = {row.check_code: row for row in results}
        missing = [row.check_code for row in definitions if row.required and row.check_code not in by_code]
        blocking = [
            row.check_code
            for row in results
            if row.blocking and row.override_status != "APPROVED"
        ]
        previous = operation.readiness_status
        if missing:
            operation.status = UnloadingStatus.READINESS_PENDING.value
            operation.readiness_status = ReadinessStatus.IN_PROGRESS.value
        elif blocking:
            operation.status = UnloadingStatus.READINESS_PENDING.value
            operation.readiness_status = ReadinessStatus.BLOCKED.value
        else:
            operation.status = UnloadingStatus.READY.value
            operation.readiness_status = ReadinessStatus.READY.value
            if assignment.status == DockAssignmentStatus.AT_DOCK.value:
                assignment.status = DockAssignmentStatus.READY_FOR_UNLOADING.value
                assignment.row_version += 1
        operation.row_version += 1
        self.events.append(
            principal=principal,
            organization_id=operation.organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.READINESS_COMPLETED.value,
            audit_code="logistics.unloading_operation.readiness_completed",
            payload={"missing": missing, "blocking": blocking},
            previous_status=previous,
            new_status=operation.readiness_status,
        )
        self.db.flush()
        return operation

    def request_override(
        self,
        result_id: UUID,
        operation: UnloadingOperationModel,
        principal: LogisticsPrincipal,
        reason: str,
    ) -> UnloadingReadinessCheckResultModel:
        result = self.db.scalar(
            select(UnloadingReadinessCheckResultModel).where(
                UnloadingReadinessCheckResultModel.id == result_id,
                UnloadingReadinessCheckResultModel.unloading_operation_id == operation.id,
            ).with_for_update()
        )
        if result is None or result.result not in {CheckResult.FAIL.value, CheckResult.REQUIRES_REVIEW.value}:
            raise invalid("READINESS_OVERRIDE_NOT_ALLOWED", "Solo se puede solicitar override sobre un resultado fallido.")
        definition = self.db.get(UnloadingReadinessCheckDefinitionModel, result.check_definition_id)
        if definition is None or not definition.allow_override:
            raise invalid("READINESS_OVERRIDE_NOT_ALLOWED", "La política no permite override para este check.")
        result.override_status = "REQUESTED"
        result.override_reason = reason
        result.override_requested_by = principal.user_id
        self.db.flush()
        return result

    def decide_override(
        self,
        result_id: UUID,
        operation: UnloadingOperationModel,
        principal: LogisticsPrincipal,
        approve: bool,
        reason: str,
    ) -> UnloadingReadinessCheckResultModel:
        result = self.db.scalar(
            select(UnloadingReadinessCheckResultModel).where(
                UnloadingReadinessCheckResultModel.id == result_id,
                UnloadingReadinessCheckResultModel.unloading_operation_id == operation.id,
            ).with_for_update()
        )
        if result is None or result.override_status != "REQUESTED":
            raise invalid("READINESS_OVERRIDE_NOT_REQUESTED", "No existe un override pendiente.")
        if result.override_requested_by == principal.user_id:
            raise invalid("SEPARATION_OF_DUTIES_REQUIRED", "Quien solicita no puede aprobar su propio override.")
        result.override_status = "APPROVED" if approve else "REJECTED"
        result.override_reviewed_by = principal.user_id
        result.override_reason = f"{result.override_reason}\nDECISION: {reason}"
        self.db.flush()
        return result


class UnloadingCompletionService:
    """Owns the immutable, organization-scoped checklist used to close unloading."""

    def __init__(self, db: Session):
        self.db = db

    def ensure_definitions(self, organization_id: UUID) -> list[UnloadingCompletionCheckDefinitionModel]:
        rows = list(
            self.db.scalars(
                select(UnloadingCompletionCheckDefinitionModel).where(
                    UnloadingCompletionCheckDefinitionModel.organization_id == organization_id,
                    UnloadingCompletionCheckDefinitionModel.status == "ACTIVE",
                ).order_by(UnloadingCompletionCheckDefinitionModel.order_index)
            )
        )
        if rows:
            return rows
        for index, code in enumerate(_COMPLETION_DEFINITIONS, 1):
            self.db.add(
                UnloadingCompletionCheckDefinitionModel(
                    id=uuid4(),
                    organization_id=organization_id,
                    check_code=code,
                    name=code.replace("_", " ").title(),
                    order_index=index,
                    required=True,
                    blocking_on_fail=True,
                    status="ACTIVE",
                )
            )
        self.db.flush()
        return list(
            self.db.scalars(
                select(UnloadingCompletionCheckDefinitionModel).where(
                    UnloadingCompletionCheckDefinitionModel.organization_id == organization_id,
                    UnloadingCompletionCheckDefinitionModel.status == "ACTIVE",
                ).order_by(UnloadingCompletionCheckDefinitionModel.order_index)
            )
        )

    def record(
        self,
        operation: UnloadingOperationModel,
        principal: LogisticsPrincipal,
        check_definition_id: UUID,
        result: str,
        observation: str | None,
    ) -> UnloadingCompletionCheckResultModel:
        if operation.status not in {UnloadingStatus.IN_PROGRESS.value, UnloadingStatus.PAUSED.value}:
            raise invalid("UNLOADING_COMPLETION_CHECK_NOT_ALLOWED", "El checklist de cierre requiere una descarga iniciada.")
        definition = self.db.scalar(
            select(UnloadingCompletionCheckDefinitionModel).where(
                UnloadingCompletionCheckDefinitionModel.id == check_definition_id,
                UnloadingCompletionCheckDefinitionModel.organization_id == operation.organization_id,
                UnloadingCompletionCheckDefinitionModel.status == "ACTIVE",
            )
        )
        if definition is None:
            raise invalid("UNLOADING_COMPLETION_CHECK_NOT_FOUND", "Comprobación de cierre no encontrada.")
        if self.db.scalar(
            select(UnloadingCompletionCheckResultModel.id).where(
                UnloadingCompletionCheckResultModel.unloading_operation_id == operation.id,
                UnloadingCompletionCheckResultModel.check_code == definition.check_code,
            )
        ):
            raise conflict("UNLOADING_COMPLETION_RESULT_ALREADY_RECORDED", "El resultado de cierre es inmutable.")
        row = UnloadingCompletionCheckResultModel(
            id=uuid4(),
            unloading_operation_id=operation.id,
            check_definition_id=definition.id,
            check_code=definition.check_code,
            result=result,
            observation=observation,
            checked_by=principal.user_id,
            checked_at=server_now(),
        )
        self.db.add(row)
        self.db.flush()
        return row


class UnloadingResponsibilityService:
    def __init__(self, db: Session):
        self.db = db
        self.events = UnloadingOperationalEventService(db)

    def assign(
        self,
        operation: UnloadingOperationModel,
        principal: LogisticsPrincipal,
        responsibility_type: str,
        user_id: UUID | None,
        business_partner_id: UUID | None,
        team_reference_id: UUID | None,
    ) -> UnloadingResponsibleAssignmentModel:
        snapshot: dict[str, str]
        if user_id is not None:
            user = self.db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
            if user is None:
                raise invalid("UNLOADING_RESPONSIBLE_INVALID", "El usuario responsable no existe o está inactivo.")
            snapshot = {"user_id": str(user.id), "display_name": user.full_name, "email": user.email}
        elif business_partner_id is not None:
            partner = self.db.scalar(
                select(BusinessPartnerModel).where(
                    BusinessPartnerModel.id == business_partner_id,
                    BusinessPartnerModel.organization_id == operation.organization_id,
                    BusinessPartnerModel.lifecycle_status == "ACTIVE",
                )
            )
            if partner is None:
                raise invalid("UNLOADING_RESPONSIBLE_INVALID", "El contratista no existe o está inactivo.")
            snapshot = {
                "business_partner_id": str(partner.id),
                "partner_code": partner.partner_code,
                "legal_name": partner.legal_name,
            }
        else:
            raise invalid("TEAM_CATALOG_NOT_AVAILABLE", "No existe un catálogo aprobado de equipos para validar team_reference_id.")
        row = UnloadingResponsibleAssignmentModel(
            id=uuid4(),
            unloading_operation_id=operation.id,
            responsibility_type=responsibility_type,
            user_id=user_id,
            business_partner_id=business_partner_id,
            team_reference_id=team_reference_id,
            responsible_snapshot=snapshot,
            status="ASSIGNED",
            assigned_at=server_now(),
            assigned_by=principal.user_id,
        )
        self.db.add(row)
        self.db.flush()
        self.events.append(
            principal=principal,
            organization_id=operation.organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.RESPONSIBLE_ASSIGNED.value,
            audit_code="logistics.unloading_operation.responsible_assigned",
            payload={"responsibility_type": responsibility_type, "responsible_assignment_id": str(row.id)},
        )
        return row

    def transition(self, row_id: UUID, operation: UnloadingOperationModel, target: str) -> UnloadingResponsibleAssignmentModel:
        row = self.db.scalar(
            select(UnloadingResponsibleAssignmentModel).where(
                UnloadingResponsibleAssignmentModel.id == row_id,
                UnloadingResponsibleAssignmentModel.unloading_operation_id == operation.id,
            ).with_for_update()
        )
        if row is None:
            raise invalid("UNLOADING_RESPONSIBLE_NOT_FOUND", "Asignación de responsable no encontrada.")
        allowed = {
            "ASSIGNED": {"ACCEPTED", "REVOKED"},
            "ACCEPTED": {"ACTIVE", "RELEASED", "REVOKED"},
            "ACTIVE": {"RELEASED", "REVOKED"},
        }
        if target not in allowed.get(row.status, set()):
            raise invalid("UNLOADING_RESPONSIBLE_STATUS_INVALID", "Transición inválida del responsable.")
        row.status = target
        now = server_now()
        if target in {"ACCEPTED", "ACTIVE"} and row.accepted_at is None:
            row.accepted_at = now
        if target in {"RELEASED", "REVOKED"}:
            row.released_at = now
        self.db.flush()
        return row


class UnloadingEquipmentService:
    """Tracks approved-catalog references without claiming live availability."""

    def __init__(self, db: Session):
        self.db = db
        self.events = UnloadingOperationalEventService(db)

    def assign(
        self,
        operation: UnloadingOperationModel,
        principal: LogisticsPrincipal,
        equipment_reference_id: UUID | None,
        equipment_type: str,
        source_type: str,
        identifier_snapshot: str | None,
    ) -> UnloadingEquipmentAssignmentModel:
        if operation.status in {
            UnloadingStatus.COMPLETED.value,
            UnloadingStatus.ABORTED.value,
            UnloadingStatus.CANCELLED.value,
            UnloadingStatus.SUPERSEDED.value,
        }:
            raise invalid(
                "UNLOADING_EQUIPMENT_ASSIGNMENT_CLOSED",
                "No puede asignarse equipo a una operación cerrada.",
            )
        row = UnloadingEquipmentAssignmentModel(
            id=uuid4(),
            unloading_operation_id=operation.id,
            equipment_reference_id=equipment_reference_id,
            equipment_type=equipment_type,
            source_type=source_type,
            identifier_snapshot=identifier_snapshot,
            status="ASSIGNED",
            assigned_at=server_now(),
        )
        self.db.add(row)
        self.db.flush()
        self.events.append(
            principal=principal,
            organization_id=operation.organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.EQUIPMENT_ASSIGNED.value,
            audit_code="logistics.unloading_operation.equipment_assigned",
            payload={
                "equipment_assignment_id": str(row.id),
                "equipment_type": equipment_type,
                "source_type": source_type,
            },
        )
        return row

    def release(
        self,
        equipment_assignment_id: UUID,
        operation: UnloadingOperationModel,
        principal: LogisticsPrincipal,
    ) -> UnloadingEquipmentAssignmentModel:
        row = self.db.scalar(
            select(UnloadingEquipmentAssignmentModel)
            .where(
                UnloadingEquipmentAssignmentModel.id == equipment_assignment_id,
                UnloadingEquipmentAssignmentModel.unloading_operation_id == operation.id,
            )
            .with_for_update()
        )
        if row is None:
            raise invalid(
                "UNLOADING_EQUIPMENT_NOT_FOUND",
                "Asignación de equipo no encontrada.",
            )
        if row.status != "ASSIGNED":
            raise invalid(
                "UNLOADING_EQUIPMENT_ALREADY_RELEASED",
                "La asignación de equipo ya fue liberada.",
            )
        row.status = "RELEASED"
        row.released_at = server_now()
        self.events.append(
            principal=principal,
            organization_id=operation.organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.EQUIPMENT_RELEASED.value,
            audit_code="logistics.unloading_operation.equipment_released",
            payload={"equipment_assignment_id": str(row.id)},
        )
        self.db.flush()
        return row


def _redact_seal(value: str | None) -> str | None:
    if not value:
        return None
    return f"***{value[-4:]}"


class UnloadingSealOpeningService:
    def __init__(self, db: Session):
        self.db = db
        self.events = UnloadingOperationalEventService(db)

    def record(
        self,
        operation: UnloadingOperationModel,
        principal: LogisticsPrincipal,
        opening_status: str,
        witnessed_by_user_id: UUID | None,
        photo_file_id: UUID | None,
        observation: str | None,
    ) -> UnloadingSealOpeningEventModel:
        if self.db.scalar(select(UnloadingSealOpeningEventModel.id).where(UnloadingSealOpeningEventModel.unloading_operation_id == operation.id)):
            raise conflict("UNLOADING_SEAL_OPENING_ALREADY_RECORDED", "La apertura de precinto es inmutable y ya fue registrada.")
        gate_seal = self.db.scalar(
            select(GateSealInspectionModel).where(GateSealInspectionModel.gate_check_in_id == operation.gate_check_in_id)
        )
        anomaly = opening_status in _SEAL_ANOMALIES
        if anomaly and photo_file_id is None:
            raise invalid("UNLOADING_SEAL_ANOMALY_PHOTO_REQUIRED", "Una anomalía de precinto requiere fotografía.")
        row = UnloadingSealOpeningEventModel(
            id=uuid4(),
            unloading_operation_id=operation.id,
            gate_seal_inspection_id=gate_seal.id if gate_seal else None,
            expected_seal_number_redacted=_redact_seal(gate_seal.expected_seal_number if gate_seal else None),
            observed_seal_number_redacted=_redact_seal(gate_seal.observed_seal_number if gate_seal else None),
            prior_physical_status=gate_seal.physical_status if gate_seal else None,
            opening_status=opening_status,
            opened_at=server_now(),
            opened_by_user_id=principal.user_id,
            opened_by_snapshot=actor_snapshot(principal),
            witnessed_by_user_id=witnessed_by_user_id,
            photo_file_id=photo_file_id,
            observation=observation,
            anomaly_detected=anomaly,
        )
        self.db.add(row)
        self.db.flush()
        self.events.append(
            principal=principal,
            organization_id=operation.organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.SEAL_OPENED.value,
            audit_code="logistics.unloading_operation.seal_opened",
            payload={"opening_status": opening_status, "anomaly_detected": anomaly},
        )
        return row


class UnloadingOperationService:
    def __init__(self, db: Session):
        self.db = db
        self.assignments = DockAssignmentService(db)
        self.events = UnloadingOperationalEventService(db)

    def get(self, operation_id: UUID, organization_id: UUID, *, lock: bool = False) -> UnloadingOperationModel:
        query = select(UnloadingOperationModel).where(
            UnloadingOperationModel.id == operation_id,
            UnloadingOperationModel.organization_id == organization_id,
        )
        if lock:
            query = query.with_for_update()
        operation = self.db.scalar(query)
        if operation is None:
            raise UnloadingOperationNotFound()
        return operation

    def create(
        self,
        assignment_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        unloading_method: str,
        notes: str | None,
    ) -> UnloadingOperationModel:
        assignment = self.assignments.get(assignment_id, organization_id, lock=True)
        if assignment.status not in {DockAssignmentStatus.AT_DOCK.value, DockAssignmentStatus.READY_FOR_UNLOADING.value}:
            raise invalid("UNLOADING_OPERATION_STATUS_INVALID", "La operación solo puede crearse después de llegar al muelle.")
        if self.db.scalar(
            select(UnloadingOperationModel.id).where(
                UnloadingOperationModel.dock_assignment_id == assignment.id,
                UnloadingOperationModel.status.in_(ACTIVE_UNLOADING_STATUSES),
            ).with_for_update()
        ):
            raise conflict("UNLOADING_OPERATION_ALREADY_EXISTS", "Ya existe una operación activa para la asignación.")
        preparation = DockAssignmentPreparationService(self.db).get_preparation(assignment.gate_check_in_id, organization_id)
        now = server_now()
        operation = UnloadingOperationModel(
            id=uuid4(),
            organization_id=organization_id,
            warehouse_id=assignment.warehouse_id,
            dock_id=assignment.dock_id,
            dock_assignment_id=assignment.id,
            gate_check_in_id=assignment.gate_check_in_id,
            appointment_id=assignment.appointment_id,
            arrival_notice_id=assignment.arrival_notice_id,
            operation_code=f"UDO-{now:%Y%m%d}-{uuid4().hex[:10].upper()}",
            status=UnloadingStatus.READINESS_PENDING.value,
            readiness_status=ReadinessStatus.PENDING.value,
            unloading_method=unloading_method,
            expected_load_summary={
                "expected_pallet_count": preparation.get("expected_pallet_count"),
                "expected_package_count": preparation.get("expected_package_count"),
                "expected_weight": preparation.get("expected_weight"),
            },
            special_requirements_snapshot=preparation.get("special_requirements"),
            notes=notes,
        )
        self.db.add(operation)
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise conflict("UNLOADING_OPERATION_ALREADY_EXISTS", "Otra transacción creó la operación.") from exc
        definitions = UnloadingReadinessService(self.db).ensure_definitions(operation)
        UnloadingCompletionService(self.db).ensure_definitions(organization_id)
        system_checks = {"GATE_CLEARANCE_VALID", "VEHICLE_AT_ASSIGNED_DOCK", "DOCK_OPERATIONAL"}
        for definition in definitions:
            if definition.check_code in system_checks:
                self.db.add(
                    UnloadingReadinessCheckResultModel(
                        id=uuid4(),
                        unloading_operation_id=operation.id,
                        check_definition_id=definition.id,
                        check_code=definition.check_code,
                        result=CheckResult.PASS.value,
                        observation="Validado por estado autoritativo del backend.",
                        blocking=False,
                        override_status="NOT_REQUESTED",
                        checked_by=principal.user_id,
                        checked_at=now,
                    )
                )
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.READINESS_STARTED.value,
            audit_code="logistics.unloading_operation.created",
            new_status=operation.status,
        )
        self.db.flush()
        return operation

    def start(self, operation_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> UnloadingOperationModel:
        operation = self.get(operation_id, organization_id, lock=True)
        assignment = self.assignments.get(operation.dock_assignment_id, organization_id, lock=True)
        require_transition(operation.status, UnloadingStatus.IN_PROGRESS.value, UNLOADING_TRANSITIONS, "unloading_operation")
        if operation.readiness_status != ReadinessStatus.READY.value:
            raise invalid("UNLOADING_READINESS_INCOMPLETE", "Readiness no está READY.")
        if assignment.status not in {DockAssignmentStatus.AT_DOCK.value, DockAssignmentStatus.READY_FOR_UNLOADING.value}:
            raise invalid("DOCK_ASSIGNMENT_STATUS_INVALID", "La asignación no está lista para descarga.")
        DockAssignmentPreparationService(self.db).get_preparation(operation.gate_check_in_id, organization_id)
        dock = WarehouseDockService(self.db).get(operation.dock_id, organization_id, lock=True)
        availability = WarehouseDockAvailabilityService(self.db).resolve(dock)
        if availability["blackout_active"] or dock.status != "ACTIVE":
            raise invalid("WAREHOUSE_DOCK_UNAVAILABLE", "El muelle no está operativo para iniciar descarga.")
        active_responsibilities = list(
            self.db.scalars(
                select(UnloadingResponsibleAssignmentModel).where(
                    UnloadingResponsibleAssignmentModel.unloading_operation_id == operation.id,
                    UnloadingResponsibleAssignmentModel.status.in_({"ASSIGNED", "ACCEPTED", "ACTIVE"}),
                )
            )
        )
        responsibility_types = {row.responsibility_type for row in active_responsibilities}
        if not {"DOCK_SUPERVISOR", "UNLOADING_LEAD"}.issubset(responsibility_types):
            raise invalid("UNLOADING_RESPONSIBLE_MISSING", "Se requieren supervisor y responsable de descarga.")
        gate_seal = self.db.scalar(
            select(GateSealInspectionModel).where(GateSealInspectionModel.gate_check_in_id == operation.gate_check_in_id)
        )
        opening = self.db.scalar(
            select(UnloadingSealOpeningEventModel).where(UnloadingSealOpeningEventModel.unloading_operation_id == operation.id)
        )
        if gate_seal and gate_seal.seal_required and opening is None:
            raise invalid("UNLOADING_SEAL_OPENING_REQUIRED", "Debe registrarse la apertura del precinto.")
        if opening and opening.anomaly_detected:
            raise invalid("UNLOADING_SEAL_ANOMALY", "La anomalía de precinto bloquea el inicio hasta un override documentado.")
        now = server_now()
        previous = operation.status
        operation.status = UnloadingStatus.IN_PROGRESS.value
        operation.started_at = now
        operation.started_by_user_id = principal.user_id
        operation.started_by_snapshot = actor_snapshot(principal)
        operation.row_version += 1
        assignment.status = DockAssignmentStatus.UNLOADING_IN_PROGRESS.value
        assignment.row_version += 1
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.UNLOADING_STARTED.value,
            audit_code="logistics.unloading_operation.started",
            previous_status=previous,
            new_status=operation.status,
        )
        self.db.flush()
        return operation

    def cancel(
        self,
        operation_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        reason: str,
    ) -> UnloadingOperationModel:
        operation = self.get(operation_id, organization_id, lock=True)
        require_transition(
            operation.status,
            UnloadingStatus.CANCELLED.value,
            UNLOADING_TRANSITIONS,
            "unloading_operation",
        )
        assignment = self.assignments.get(
            operation.dock_assignment_id, organization_id, lock=True
        )
        previous = operation.status
        operation.status = UnloadingStatus.CANCELLED.value
        operation.notes = "\n".join(
            value for value in [operation.notes, f"CANCELLED: {reason}"] if value
        )
        operation.row_version += 1
        assignment.status = DockAssignmentStatus.READY_FOR_UNLOADING.value
        assignment.row_version += 1
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.UNLOADING_CANCELLED.value,
            audit_code="logistics.unloading_operation.cancelled",
            reason=reason,
            previous_status=previous,
            new_status=operation.status,
        )
        self.db.flush()
        return operation

    def pause(
        self,
        operation_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        reason_code: str,
        reason: str,
        severity: str,
        evidence_file_id: UUID | None,
    ) -> tuple[UnloadingOperationModel, UnloadingPauseModel]:
        operation = self.get(operation_id, organization_id, lock=True)
        require_transition(operation.status, UnloadingStatus.PAUSED.value, UNLOADING_TRANSITIONS, "unloading_operation")
        assignment = self.assignments.get(operation.dock_assignment_id, organization_id, lock=True)
        active = self.db.scalar(
            select(UnloadingPauseModel.id).where(
                UnloadingPauseModel.unloading_operation_id == operation.id,
                UnloadingPauseModel.status == PauseStatus.ACTIVE.value,
            ).with_for_update()
        )
        if active:
            raise conflict("UNLOADING_PAUSE_ALREADY_ACTIVE", "La operación ya tiene una pausa activa.")
        number = int(
            self.db.scalar(
                select(func.coalesce(func.max(UnloadingPauseModel.pause_number), 0)).where(
                    UnloadingPauseModel.unloading_operation_id == operation.id
                )
            )
            or 0
        ) + 1
        pause = UnloadingPauseModel(
            id=uuid4(),
            unloading_operation_id=operation.id,
            pause_number=number,
            reason_code=reason_code,
            reason=reason,
            severity=severity,
            started_at=server_now(),
            started_by_user_id=principal.user_id,
            started_by_snapshot=actor_snapshot(principal),
            evidence_file_id=evidence_file_id,
            status=PauseStatus.ACTIVE.value,
        )
        self.db.add(pause)
        previous = operation.status
        operation.status = UnloadingStatus.PAUSED.value
        operation.row_version += 1
        assignment.status = DockAssignmentStatus.UNLOADING_PAUSED.value
        assignment.row_version += 1
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise conflict("UNLOADING_PAUSE_ALREADY_ACTIVE", "Otra transacción registró una pausa.") from exc
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.UNLOADING_PAUSED.value,
            audit_code="logistics.unloading_operation.paused",
            payload={"pause_id": str(pause.id), "reason_code": reason_code, "severity": severity},
            reason=reason,
            previous_status=previous,
            new_status=operation.status,
        )
        return operation, pause

    def resume(
        self,
        operation_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        resolution: str,
    ) -> tuple[UnloadingOperationModel, UnloadingPauseModel]:
        operation = self.get(operation_id, organization_id, lock=True)
        require_transition(operation.status, UnloadingStatus.IN_PROGRESS.value, UNLOADING_TRANSITIONS, "unloading_operation")
        assignment = self.assignments.get(operation.dock_assignment_id, organization_id, lock=True)
        pause = self.db.scalar(
            select(UnloadingPauseModel).where(
                UnloadingPauseModel.unloading_operation_id == operation.id,
                UnloadingPauseModel.status == PauseStatus.ACTIVE.value,
            ).with_for_update()
        )
        if pause is None:
            raise invalid("UNLOADING_PAUSE_NOT_FOUND", "No existe una pausa activa.")
        now = server_now()
        duration = int((now - pause.started_at).total_seconds())
        if duration < 0:
            raise invalid("UNLOADING_TIME_SEQUENCE_INVALID", "La reanudación produciría una duración negativa.")
        pause.ended_at = now
        pause.ended_by_user_id = principal.user_id
        pause.ended_by_snapshot = actor_snapshot(principal)
        pause.duration_seconds = duration
        pause.status = PauseStatus.RESOLVED.value
        pause.reason = f"{pause.reason}\nRESOLUTION: {resolution}"
        previous = operation.status
        operation.status = UnloadingStatus.IN_PROGRESS.value
        operation.total_pause_seconds += duration
        operation.row_version += 1
        assignment.status = DockAssignmentStatus.UNLOADING_IN_PROGRESS.value
        assignment.row_version += 1
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.UNLOADING_RESUMED.value,
            audit_code="logistics.unloading_operation.resumed",
            payload={"pause_id": str(pause.id), "duration_seconds": duration},
            previous_status=previous,
            new_status=operation.status,
        )
        self.db.flush()
        return operation, pause

    def cancel_pause(
        self,
        pause_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        reason: str,
    ) -> tuple[UnloadingOperationModel, UnloadingPauseModel]:
        pause = self.db.scalar(
            select(UnloadingPauseModel)
            .join(
                UnloadingOperationModel,
                UnloadingOperationModel.id == UnloadingPauseModel.unloading_operation_id,
            )
            .where(
                UnloadingPauseModel.id == pause_id,
                UnloadingOperationModel.organization_id == organization_id,
            )
            .with_for_update()
        )
        if pause is None or pause.status != PauseStatus.ACTIVE.value:
            raise invalid(
                "UNLOADING_PAUSE_NOT_ACTIVE",
                "La pausa no existe o ya no está activa.",
            )
        operation = self.get(pause.unloading_operation_id, organization_id, lock=True)
        if operation.status != UnloadingStatus.PAUSED.value:
            raise invalid(
                "UNLOADING_OPERATION_STATUS_INVALID",
                "Solo puede anularse la pausa activa de una operación pausada.",
            )
        assignment = self.assignments.get(
            operation.dock_assignment_id, organization_id, lock=True
        )
        now = server_now()
        duration = max(int((now - pause.started_at).total_seconds()), 0)
        pause.ended_at = now
        pause.ended_by_user_id = principal.user_id
        pause.ended_by_snapshot = actor_snapshot(principal)
        pause.duration_seconds = duration
        pause.status = PauseStatus.CANCELLED.value
        pause.reason = f"{pause.reason}\nCANCELLATION: {reason}"
        previous = operation.status
        operation.status = UnloadingStatus.IN_PROGRESS.value
        operation.row_version += 1
        assignment.status = DockAssignmentStatus.UNLOADING_IN_PROGRESS.value
        assignment.row_version += 1
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.UNLOADING_PAUSE_CANCELLED.value,
            audit_code="logistics.unloading_operation.pause_cancelled",
            reason=reason,
            payload={"pause_id": str(pause.id), "elapsed_seconds": duration},
            previous_status=previous,
            new_status=operation.status,
        )
        self.db.flush()
        return operation, pause

    def abort(
        self,
        operation_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        reason: str,
    ) -> UnloadingOperationModel:
        operation = self.get(operation_id, organization_id, lock=True)
        if operation.status not in {UnloadingStatus.IN_PROGRESS.value, UnloadingStatus.PAUSED.value}:
            raise invalid("UNLOADING_OPERATION_STATUS_INVALID", "Solo una descarga iniciada o pausada puede abortarse.")
        assignment = self.assignments.get(operation.dock_assignment_id, organization_id, lock=True)
        now = server_now()
        pause = self.db.scalar(
            select(UnloadingPauseModel).where(
                UnloadingPauseModel.unloading_operation_id == operation.id,
                UnloadingPauseModel.status == PauseStatus.ACTIVE.value,
            ).with_for_update()
        )
        if pause:
            pause.ended_at = now
            pause.ended_by_user_id = principal.user_id
            pause.ended_by_snapshot = actor_snapshot(principal)
            pause.duration_seconds = max(int((now - pause.started_at).total_seconds()), 0)
            pause.status = PauseStatus.RESOLVED.value
            operation.total_pause_seconds += pause.duration_seconds
        previous = operation.status
        operation.status = UnloadingStatus.ABORTED.value
        operation.aborted_at = now
        operation.aborted_by_user_id = principal.user_id
        operation.abort_reason = reason
        operation.row_version += 1
        assignment.status = DockAssignmentStatus.RELEASE_PENDING.value
        assignment.row_version += 1
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.UNLOADING_ABORTED.value,
            audit_code="logistics.unloading_operation.aborted",
            reason=reason,
            previous_status=previous,
            new_status=operation.status,
        )
        self.db.flush()
        return operation

    def complete(
        self,
        operation_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        completion_note: str | None,
    ) -> UnloadingOperationModel:
        operation = self.get(operation_id, organization_id, lock=True)
        require_transition(operation.status, UnloadingStatus.COMPLETED.value, UNLOADING_TRANSITIONS, "unloading_operation")
        assignment = self.assignments.get(operation.dock_assignment_id, organization_id, lock=True)
        if self.db.scalar(
            select(UnloadingPauseModel.id).where(
                UnloadingPauseModel.unloading_operation_id == operation.id,
                UnloadingPauseModel.status == PauseStatus.ACTIVE.value,
            ).with_for_update()
        ):
            raise invalid("UNLOADING_CANNOT_COMPLETE_WHILE_PAUSED", "Reanude o aborte antes de finalizar.")
        definitions = UnloadingCompletionService(self.db).ensure_definitions(organization_id)
        if definitions:
            results = {
                row.check_code: row
                for row in self.db.scalars(
                    select(UnloadingCompletionCheckResultModel).where(
                        UnloadingCompletionCheckResultModel.unloading_operation_id == operation.id
                    )
                )
            }
            blocking = [
                definition.check_code
                for definition in definitions
                if definition.required
                and (
                    definition.check_code not in results
                    or results[definition.check_code].result in {CheckResult.FAIL.value, CheckResult.REQUIRES_REVIEW.value}
                )
            ]
            if blocking:
                raise invalid("UNLOADING_COMPLETION_CHECKLIST_INCOMPLETE", "El checklist de cierre tiene faltantes o fallas bloqueantes.")
        if operation.started_at is None:
            raise invalid("UNLOADING_TIME_SEQUENCE_INVALID", "No existe hora autoritativa de inicio.")
        now = server_now()
        gross = int((now - operation.started_at).total_seconds())
        if gross < 0 or operation.total_pause_seconds > gross:
            raise invalid("UNLOADING_TIME_SEQUENCE_INVALID", "Las duraciones producirían una secuencia inválida.")
        previous = operation.status
        operation.status = UnloadingStatus.COMPLETED.value
        operation.completed_at = now
        operation.completed_by_user_id = principal.user_id
        operation.completed_by_snapshot = actor_snapshot(principal)
        operation.gross_duration_seconds = gross
        operation.net_duration_seconds = gross - operation.total_pause_seconds
        operation.notes = "\n".join(value for value in [operation.notes, completion_note] if value)
        operation.row_version += 1
        assignment.status = DockAssignmentStatus.UNLOADING_COMPLETED.value
        assignment.row_version += 1
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.UNLOADING_COMPLETED.value,
            audit_code="logistics.unloading_operation.completed",
            payload={
                "gross_duration_seconds": operation.gross_duration_seconds,
                "pause_seconds": operation.total_pause_seconds,
                "net_duration_seconds": operation.net_duration_seconds,
            },
            previous_status=previous,
            new_status=operation.status,
        )
        self.db.flush()
        return operation

    def release_dock(
        self,
        assignment_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        reason: str | None,
    ) -> InboundDockAssignmentModel:
        assignment = self.assignments.get(assignment_id, organization_id, lock=True)
        operation = self.db.scalar(
            select(UnloadingOperationModel).where(
                UnloadingOperationModel.dock_assignment_id == assignment.id,
                UnloadingOperationModel.organization_id == organization_id,
            ).with_for_update()
        )
        if operation is None or operation.status not in {UnloadingStatus.COMPLETED.value, UnloadingStatus.ABORTED.value}:
            raise invalid("UNLOADING_DOCK_RELEASE_BLOCKED", "Solo una operación completada o abortada puede liberar el muelle.")
        if operation.status == UnloadingStatus.ABORTED.value and not reason:
            raise invalid("UNLOADING_ABORT_RELEASE_REASON_REQUIRED", "Liberar una descarga abortada requiere motivo.")
        now = server_now()
        if operation.completed_at and now < operation.completed_at:
            raise invalid("UNLOADING_TIME_SEQUENCE_INVALID", "La liberación no puede preceder a la finalización.")
        DockOccupancyService(self.db).close(assignment, now)
        previous = assignment.status
        assignment.status = DockAssignmentStatus.DOCK_RELEASED.value
        assignment.released_at = now
        assignment.released_by_user_id = principal.user_id
        assignment.row_version += 1
        queue = self.db.get(InboundDockQueueEntryModel, assignment.queue_entry_id)
        if queue:
            queue.queue_status = QueueStatus.COMPLETED.value
            queue.row_version += 1
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.DOCK_RELEASED.value,
            audit_code="logistics.inbound_dock_assignment.released",
            reason=reason,
            previous_status=previous,
            new_status=assignment.status,
        )
        self.db.flush()
        return assignment


class UnloadingPauseService(UnloadingOperationService):
    """Named façade for pause/resume commands."""


class UnloadingTimeCorrectionService:
    _FIELD_MAP = {
        "UNLOADING_STARTED_AT": (UnloadingOperationModel, "started_at"),
        "UNLOADING_COMPLETED_AT": (UnloadingOperationModel, "completed_at"),
        "DOCK_ARRIVED_AT": (InboundDockAssignmentModel, "dock_arrived_at"),
        "DOCK_RELEASED_AT": (InboundDockAssignmentModel, "released_at"),
    }

    def __init__(self, db: Session):
        self.db = db
        self.events = UnloadingOperationalEventService(db)

    def request(
        self,
        operation: UnloadingOperationModel,
        principal: LogisticsPrincipal,
        field_code: str,
        proposed_timestamp: datetime,
        reason: str,
        evidence_file_id: UUID | None,
    ) -> DockOperationalTimeCorrectionModel:
        target = self._FIELD_MAP.get(field_code)
        if target is None:
            raise invalid("UNLOADING_TIME_CORRECTION_FIELD_INVALID", "Campo de tiempo no corregible.")
        resource = operation if target[0] is UnloadingOperationModel else self.db.get(InboundDockAssignmentModel, operation.dock_assignment_id)
        original = getattr(resource, target[1]) if resource else None
        if original is None:
            raise invalid("UNLOADING_TIME_CORRECTION_NOT_ALLOWED", "No existe timestamp original; no se puede sobrescribir ni inventar.")
        row = DockOperationalTimeCorrectionModel(
            id=uuid4(),
            organization_id=operation.organization_id,
            resource_type="UNLOADING_OPERATION" if resource is operation else "DOCK_ASSIGNMENT",
            resource_id=resource.id,
            field_code=field_code,
            original_timestamp=original,
            proposed_timestamp=proposed_timestamp,
            reason=reason,
            evidence_file_id=evidence_file_id,
            status="REQUESTED",
            requested_by=principal.user_id,
            requested_at=server_now(),
        )
        self.db.add(row)
        self.db.flush()
        self.events.append(
            principal=principal,
            organization_id=operation.organization_id,
            warehouse_id=operation.warehouse_id,
            gate_check_in_id=operation.gate_check_in_id,
            dock_id=operation.dock_id,
            assignment_id=operation.dock_assignment_id,
            operation_id=operation.id,
            event_type=DockOperationalEventType.TIME_CORRECTION_REQUESTED.value,
            audit_code="logistics.unloading_operation.time_correction_requested",
            payload={"correction_id": str(row.id), "field_code": field_code},
            reason=reason,
        )
        return row

    def decide(
        self,
        correction_id: UUID,
        operation: UnloadingOperationModel,
        principal: LogisticsPrincipal,
        approve: bool,
        reason: str,
    ) -> DockOperationalTimeCorrectionModel:
        row = self.db.scalar(
            select(DockOperationalTimeCorrectionModel).where(
                DockOperationalTimeCorrectionModel.id == correction_id,
                DockOperationalTimeCorrectionModel.organization_id == operation.organization_id,
            ).with_for_update()
        )
        if row is None or row.status != "REQUESTED":
            raise invalid("UNLOADING_TIME_CORRECTION_NOT_ALLOWED", "La corrección no está pendiente.")
        if row.requested_by == principal.user_id:
            raise invalid("SEPARATION_OF_DUTIES_REQUIRED", "Quien solicita no puede revisar su propia corrección.")
        row.status = "APPROVED" if approve else "REJECTED"
        row.reviewed_by = principal.user_id
        row.decided_at = server_now()
        row.reason = f"{row.reason}\nDECISION: {reason}"
        if approve:
            self.events.append(
                principal=principal,
                organization_id=operation.organization_id,
                warehouse_id=operation.warehouse_id,
                gate_check_in_id=operation.gate_check_in_id,
                dock_id=operation.dock_id,
                assignment_id=operation.dock_assignment_id,
                operation_id=operation.id,
                event_type=DockOperationalEventType.TIME_CORRECTION_APPROVED.value,
                audit_code="logistics.unloading_operation.time_correction_approved",
                payload={"correction_id": str(row.id), "field_code": row.field_code},
                reason=reason,
            )
        self.db.flush()
        return row


class DockOperationalProjectionService:
    def __init__(self, db: Session):
        self.db = db

    def metrics(self, operation: UnloadingOperationModel) -> dict[str, int | str | None]:
        assignment = self.db.get(InboundDockAssignmentModel, operation.dock_assignment_id)
        gate = self.db.get(GateCheckInModel, operation.gate_check_in_id)
        queue = self.db.get(InboundDockQueueEntryModel, assignment.queue_entry_id) if assignment else None
        values = DockOperationalMetricsService.calculate(
            gate_arrived_at=gate.arrived_at if gate else None,
            gate_cleared_at=gate.entry_authorized_at if gate else None,
            queued_at=queue.queued_at if queue else None,
            assigned_at=assignment.assigned_at if assignment else None,
            movement_started_at=assignment.movement_started_at if assignment else None,
            dock_arrived_at=assignment.dock_arrived_at if assignment else None,
            unloading_started_at=operation.started_at,
            unloading_completed_at=operation.completed_at,
            dock_released_at=assignment.released_at if assignment else None,
            pause_seconds=operation.total_pause_seconds,
        )
        pairs = [
            (queue.queued_at if queue else None, assignment.assigned_at if assignment else None),
            (assignment.movement_started_at if assignment else None, assignment.dock_arrived_at if assignment else None),
            (assignment.dock_arrived_at if assignment else None, operation.started_at),
            (operation.started_at, operation.completed_at),
            (operation.completed_at, assignment.released_at if assignment else None),
        ]
        if any(start and end and end < start for start, end in pairs):
            values["data_quality_status"] = OperationalTimeQualityStatus.EVENT_ORDER_INVALID.value
        corrections = int(
            self.db.scalar(
                select(func.count()).select_from(DockOperationalTimeCorrectionModel).where(
                    DockOperationalTimeCorrectionModel.organization_id == operation.organization_id,
                    DockOperationalTimeCorrectionModel.resource_id.in_({operation.id, operation.dock_assignment_id}),
                    DockOperationalTimeCorrectionModel.status == "APPROVED",
                )
            )
            or 0
        )
        if corrections and values["data_quality_status"] != OperationalTimeQualityStatus.EVENT_ORDER_INVALID.value:
            values["data_quality_status"] = OperationalTimeQualityStatus.CORRECTED.value
        return values

    def refresh(self, operation: UnloadingOperationModel) -> DockOperationMetricsProjectionModel:
        assignment = self.db.get(InboundDockAssignmentModel, operation.dock_assignment_id)
        gate = self.db.get(GateCheckInModel, operation.gate_check_in_id)
        values = self.metrics(operation)
        row = self.db.scalar(
            select(DockOperationMetricsProjectionModel).where(
                DockOperationMetricsProjectionModel.unloading_operation_id == operation.id
            ).with_for_update()
        )
        if row is None:
            row = DockOperationMetricsProjectionModel(
                id=uuid4(),
                warehouse_id=operation.warehouse_id,
                dock_id=operation.dock_id,
                gate_check_in_id=operation.gate_check_in_id,
                assignment_id=operation.dock_assignment_id,
                unloading_operation_id=operation.id,
            )
            self.db.add(row)
        for field in (
            "gate_processing_seconds", "dock_assignment_wait_seconds", "gate_to_dock_seconds",
            "dock_wait_before_unloading_seconds", "unloading_gross_seconds", "unloading_pause_seconds",
            "unloading_net_seconds", "dock_release_delay_seconds", "dock_occupancy_seconds",
        ):
            setattr(row, field, values[field])
        row.arrival_date = gate.arrived_at.date() if gate and gate.arrived_at else None
        row.arrival_hour_local = None
        row.planned_slot_start = assignment.planned_start if assignment else None
        row.planned_slot_end = assignment.planned_end if assignment else None
        row.pause_count = int(
            self.db.scalar(select(func.count()).select_from(UnloadingPauseModel).where(UnloadingPauseModel.unloading_operation_id == operation.id)) or 0
        )
        row.reassignment_count = 1 if assignment and assignment.reassigned_from_assignment_id else 0
        row.data_quality_status = str(values["data_quality_status"])
        row.completed = operation.status == UnloadingStatus.COMPLETED.value
        row.released = bool(assignment and assignment.released_at)
        row.calculated_at = server_now()
        self.db.flush()
        return row


class DockOperationIntegrityService:
    def __init__(self, db: Session):
        self.db = db

    def verify(self, operation: UnloadingOperationModel) -> dict[str, object]:
        assignment = self.db.get(InboundDockAssignmentModel, operation.dock_assignment_id)
        readiness = list(
            self.db.scalars(
                select(UnloadingReadinessCheckResultModel)
                .where(UnloadingReadinessCheckResultModel.unloading_operation_id == operation.id)
                .order_by(UnloadingReadinessCheckResultModel.check_code)
            )
        )
        responsibles = list(
            self.db.scalars(
                select(UnloadingResponsibleAssignmentModel)
                .where(UnloadingResponsibleAssignmentModel.unloading_operation_id == operation.id)
                .order_by(UnloadingResponsibleAssignmentModel.assigned_at)
            )
        )
        pauses = list(
            self.db.scalars(
                select(UnloadingPauseModel)
                .where(UnloadingPauseModel.unloading_operation_id == operation.id)
                .order_by(UnloadingPauseModel.pause_number)
            )
        )
        seal = self.db.scalar(select(UnloadingSealOpeningEventModel).where(UnloadingSealOpeningEventModel.unloading_operation_id == operation.id))
        chain_valid, chain_alerts, chain_hash = UnloadingOperationalEventService(self.db).verify_chain(operation.gate_check_in_id)
        hashes = {
            "assignment_hash": assignment.assignment_hash if assignment else None,
            "readiness_hash": sha256_payload([(row.check_code, row.result, row.override_status) for row in readiness]),
            "responsibility_manifest_hash": sha256_payload([(row.responsibility_type, row.responsible_snapshot, row.status) for row in responsibles]),
            "seal_opening_hash": sha256_payload((seal.opening_status, seal.opened_at, seal.anomaly_detected)) if seal else None,
            "operational_events_hash": chain_hash,
            "pause_manifest_hash": sha256_payload([(row.pause_number, row.started_at, row.ended_at, row.duration_seconds, row.status) for row in pauses]),
            "time_source_hash": sha256_payload((operation.started_at, operation.completed_at, assignment.dock_arrived_at if assignment else None, assignment.released_at if assignment else None)),
            "completion_hash": sha256_payload((operation.status, operation.gross_duration_seconds, operation.total_pause_seconds, operation.net_duration_seconds)),
        }
        return {
            "operation_id": operation.id,
            "valid": chain_valid,
            "manifest_hashes": hashes,
            "alerts": chain_alerts,
            "verified_at": server_now(),
        }


class ReceivingScanPreparationService:
    """Read-only Phase 039 contract; never creates reception or inventory data."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, operation: UnloadingOperationModel) -> dict[str, object]:
        if operation.status != UnloadingStatus.COMPLETED.value or operation.completed_at is None or operation.started_at is None:
            raise invalid("RECEIVING_PREPARATION_NOT_AVAILABLE", "La preparación de escaneo solo está disponible al completar la descarga.")
        assignment = self.db.get(InboundDockAssignmentModel, operation.dock_assignment_id)
        gate = self.db.get(GateCheckInModel, operation.gate_check_in_id)
        preparation = DockAssignmentPreparationService(self.db).get_preparation(operation.gate_check_in_id, operation.organization_id)
        revision = None
        if operation.arrival_notice_id:
            notice = self.db.get(ArrivalNoticeModel, operation.arrival_notice_id)
            if notice and notice.active_revision_id:
                revision = self.db.get(ArrivalNoticeRevisionModel, notice.active_revision_id)
        po_refs = []
        lines = []
        documents = []
        if revision:
            po_refs = [
                {"purchase_order_id": str(row.purchase_order_id), "purchase_order_code": row.purchase_order_code}
                for row in self.db.scalars(
                    select(ArrivalNoticePurchaseOrderReferenceModel).where(
                        ArrivalNoticePurchaseOrderReferenceModel.arrival_notice_revision_id == revision.id
                    )
                )
            ]
            lines = [
                {
                    "line_number": row.line_number,
                    "purchase_order_line_id": str(row.purchase_order_line_id),
                    "sku": row.sku_snapshot,
                    "product_name": row.product_name_snapshot,
                    "expected_quantity": str(row.expected_quantity),
                    "expected_unit_id": str(row.expected_unit_id),
                    "expected_base_quantity": str(row.expected_base_quantity),
                    "base_unit_id": str(row.base_unit_id),
                }
                for row in self.db.scalars(
                    select(ArrivalNoticeExpectedLineModel).where(
                        ArrivalNoticeExpectedLineModel.arrival_notice_revision_id == revision.id
                    )
                )
            ]
            documents = [
                {
                    "document_kind": row.document_kind,
                    "reference": row.normalized_reference,
                    "verification_status": row.verification_status,
                }
                for row in self.db.scalars(
                    select(ArrivalNoticeTransportDocumentModel).where(
                        ArrivalNoticeTransportDocumentModel.revision_id == revision.id
                    )
                )
            ]
        responsibles = [
            {"responsibility_type": row.responsibility_type, "snapshot": row.responsible_snapshot, "status": row.status}
            for row in self.db.scalars(
                select(UnloadingResponsibleAssignmentModel).where(
                    UnloadingResponsibleAssignmentModel.unloading_operation_id == operation.id
                )
            )
        ]
        seal = self.db.scalar(select(UnloadingSealOpeningEventModel).where(UnloadingSealOpeningEventModel.unloading_operation_id == operation.id))
        metrics = DockOperationalProjectionService(self.db).metrics(operation)
        return {
            "unloading_operation_id": operation.id,
            "dock_assignment_id": operation.dock_assignment_id,
            "gate_check_in_id": operation.gate_check_in_id,
            "cpv_code": preparation.get("cpv_code"),
            "appointment_id": operation.appointment_id,
            "cit_code": preparation.get("cit_code"),
            "warehouse_id": operation.warehouse_id,
            "dock_id": operation.dock_id,
            "supplier_summary": preparation.get("supplier_summary"),
            "carrier_summary": preparation.get("carrier_summary"),
            "vehicle_summary": {"vehicle_id": preparation.get("vehicle_id")},
            "observed_plate": assignment.observed_plate_snapshot if assignment else "",
            "purchase_order_references": po_refs,
            "expected_lines": lines,
            "transport_documents": documents,
            "seal_opening_summary": {
                "opening_status": seal.opening_status,
                "anomaly_detected": seal.anomaly_detected,
                "opened_at": seal.opened_at.isoformat(),
            } if seal else None,
            "unloading_started_at": operation.started_at,
            "unloading_completed_at": operation.completed_at,
            "unloading_status": operation.status,
            "responsible_summary": responsibles,
            "operational_warnings": [],
            "data_quality_status": metrics["data_quality_status"],
            "receiving_capabilities_future": ["PHASE_039_SCAN_HANDOVER"],
        }


UnloadingOperationalEventService = UnloadingOperationalEventService
