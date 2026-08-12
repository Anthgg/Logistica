"""Application Services for Phase 037 (Gate Control Core Domain)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional, Sequence
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.modules.logistics.drivers.infrastructure.persistence.models import DriverLicenseModel
from app.modules.logistics.gate_control.application.schemas import (
    GateCheckInRequest,
    GateCheckOutRequest,
    GateControlRecordResponse,
    GateDecisionRequest,
    GatePreparationResponse,
    WarehouseGateCreate,
    WarehouseGateResponse,
    WarehouseGateUpdate,
)
from app.modules.logistics.gate_control.domain.enums import (
    AccessDecision,
    GateEventType,
    GateRecordStatus,
    GateStatus,
    SealStatus,
)
from app.modules.logistics.gate_control.domain.exceptions import (
    DriverLicenseExpiredError,
    GateNotFoundError,
    GateRecordNotFoundError,
    InvalidGateStateError,
    PlateMismatchWarning,
    SealStatusInvalidError,
)
from app.modules.logistics.gate_control.domain.models import (
    GateControlHistoryModel,
    GateControlRecordModel,
    WarehouseGateModel,
)
from app.modules.logistics.gate_control.infrastructure.adapters import (
    GateControlDocumentAdapter,
)
from app.modules.logistics.gate_control.infrastructure.repositories import (
    GateControlRecordRepository,
    WarehouseGateRepository,
)
from app.modules.logistics.inbound.reception_calendar.application.services.appointment_service import (
    ReceptionAppointmentService,
)


def generate_gate_record_code() -> str:
    """Generate a unique record code for gate control events."""
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    short_uuid = str(uuid4())[:6].upper()
    return f"GCR-{now_str}-{short_uuid}"


class GatePreparationService:
    """Service to retrieve expected appointment context from Phase 036."""

    def __init__(self, db: Session):
        self.db = db
        self.appointment_service = ReceptionAppointmentService(db)

    def get_gate_preparation(
        self, appointment_id: UUID, organization_id: UUID
    ) -> GatePreparationResponse:
        """Fetch preparation details for gate check-in from reception appointment."""
        prep = self.appointment_service.gate_preparation(appointment_id, organization_id)
        supplier = prep.get("supplier") or {}
        carrier = prep.get("carrier") or {}
        driver = prep.get("driver") or {}

        return GatePreparationResponse(
            appointment_id=prep["appointment_id"],
            appointment_code=prep.get("appointment_code"),
            arrival_notice_id=prep["arrival_notice_id"],
            warehouse_id=prep["warehouse_id"],
            expected_plate=prep.get("expected_plate"),
            expected_seal_reference=prep.get("expected_seal_reference"),
            expected_driver_dni=prep.get("expected_driver_dni") or driver.get("dni_number"),
            expected_vehicle_id=prep.get("expected_vehicle_id"),
            carrier_partner_id=carrier.get("carrier_id") or carrier.get("carrier_partner_id"),
            carrier_name=carrier.get("name") or carrier.get("carrier_name"),
            appointment_status=prep.get("appointment_status", "UNKNOWN"),
            guide_references=prep.get("guide_references", []),
            verification_warnings=prep.get("verification_warnings", []),
        )


class GateControlService:
    """Core application service managing warehouse gates and access records."""

    def __init__(self, db: Session, doc_adapter: Optional[GateControlDocumentAdapter] = None):
        self.db = db
        self.gate_repo = WarehouseGateRepository(db)
        self.record_repo = GateControlRecordRepository(db)
        self.prep_service = GatePreparationService(db)
        self.doc_adapter = doc_adapter or GateControlDocumentAdapter(db)

    # --- Warehouse Gate Management ---

    def create_gate(
        self, organization_id: UUID, payload: WarehouseGateCreate
    ) -> WarehouseGateResponse:
        """Register a new warehouse gate."""
        code_clean = payload.code.strip().upper()
        existing = self.gate_repo.get_by_code(organization_id, code_clean)
        if existing:
            raise InvalidGateStateError(f"Ya existe una puerta con el código '{code_clean}'.")

        gate = WarehouseGateModel(
            organization_id=organization_id,
            code=code_clean,
            name=payload.name.strip(),
            warehouse_id=payload.warehouse_id,
            gate_type=str(payload.gate_type),
            status=str(payload.status),
            notes=payload.notes,
            is_active=payload.is_active,
        )
        saved = self.gate_repo.create(gate)
        self.db.commit()
        return WarehouseGateResponse.model_validate(saved)

    def get_gate(self, gate_id: UUID, organization_id: UUID) -> WarehouseGateResponse:
        """Retrieve warehouse gate by ID."""
        gate = self.gate_repo.get_by_id(gate_id, organization_id)
        if not gate:
            raise GateNotFoundError(str(gate_id))
        return WarehouseGateResponse.model_validate(gate)

    def list_gates(
        self, organization_id: UUID, is_active: Optional[bool] = None
    ) -> Sequence[WarehouseGateResponse]:
        """List warehouse gates for an organization."""
        gates = self.gate_repo.list_by_organization(organization_id, is_active=is_active)
        return [WarehouseGateResponse.model_validate(g) for g in gates]

    # --- Gate Preparation & Check-In Operations ---

    def prepare_gate_checkin(
        self, appointment_id: UUID, organization_id: UUID
    ) -> GatePreparationResponse:
        """Retrieve preparation details from linked reception appointment."""
        return self.prep_service.get_gate_preparation(appointment_id, organization_id)

    def process_checkin(
        self, request: GateCheckInRequest, organization_id: UUID, guard_user_id: UUID
    ) -> GateControlRecordResponse:
        """Process vehicle arrival and check-in at a warehouse gate."""
        gate = self.gate_repo.get_by_id(request.gate_id, organization_id)
        if not gate:
            raise GateNotFoundError(str(request.gate_id))
        if str(gate.status) != str(GateStatus.ACTIVE) or not gate.is_active:
            raise InvalidGateStateError(
                f"La puerta '{gate.code}' se encuentra en estado '{gate.status}' y no permite registros."
            )

        norm_plate = request.plate_observed.strip().upper().replace("-", "").replace(" ", "")
        record_code = generate_gate_record_code()
        arrival_now = datetime.now(timezone.utc)

        record = GateControlRecordModel(
            organization_id=organization_id,
            record_code=record_code,
            gate_id=request.gate_id,
            reception_appointment_id=request.reception_appointment_id,
            vehicle_id=request.vehicle_id,
            driver_id=request.driver_id,
            guard_user_id=guard_user_id,
            event_type=str(GateEventType.CHECK_IN),
            arrival_at=arrival_now,
            access_decision=str(AccessDecision.PENDING),
            plate_observed=norm_plate,
            seal_status=str(request.seal_status),
            driver_dni_raw=request.driver_dni_raw,
            driver_license_raw=request.driver_license_raw,
            status=str(GateRecordStatus.DRAFT),
        )

        created_record = self.record_repo.create(record)

        history = GateControlHistoryModel(
            record_id=created_record.id,
            previous_status=None,
            new_status=str(GateRecordStatus.DRAFT),
            changed_by_user_id=guard_user_id,
            change_reason="Llegada de vehículo registrada en garita.",
        )
        self.record_repo.add_history(history)
        self.db.commit()

        loaded = self.record_repo.get_by_id(created_record.id, organization_id)
        return GateControlRecordResponse.from_model(loaded)

    def authorize_entry(
        self, request: GateDecisionRequest, organization_id: UUID, guard_user_id: UUID
    ) -> GateControlRecordResponse:
        """Evaluate security compliance and authorize entry for a gate record."""
        record = self.record_repo.get_by_id(request.record_id, organization_id)
        if not record:
            raise GateRecordNotFoundError(str(request.record_id))

        if str(record.status) not in (str(GateRecordStatus.DRAFT), str(GateRecordStatus.CHECKED_IN)):
            raise InvalidGateStateError(
                f"El registro está en estado '{record.status}' y no puede ser autorizado."
            )

        if str(request.decision) != str(AccessDecision.APPROVED):
            raise InvalidGateStateError(
                f"Decisión inválida '{request.decision}' para autorización de ingreso."
            )

        # 1. Validation: Cargo Seal Condition
        seal_str = str(record.seal_status)
        if seal_str in (str(SealStatus.BROKEN), str(SealStatus.TAMPERED), str(SealStatus.MISMATCH)):
            raise SealStatusInvalidError(seal_str)

        # 2. Validation: Expected Plate Matching (if appointment linked)
        appointment_code = None
        carrier_name = None
        if record.reception_appointment_id:
            prep = self.prep_service.get_gate_preparation(
                record.reception_appointment_id, organization_id
            )
            appointment_code = prep.appointment_code
            carrier_name = prep.carrier_name
            if prep.expected_plate:
                norm_expected = prep.expected_plate.strip().upper().replace("-", "").replace(" ", "")
                norm_observed = record.plate_observed.strip().upper().replace("-", "").replace(" ", "")
                if norm_expected != norm_observed:
                    raise PlateMismatchWarning(
                        expected_plate=prep.expected_plate, observed_plate=record.plate_observed
                    )

        # 3. Validation: Driver License Expiration Check
        if record.driver_license_raw or record.driver_id:
            lic_query = self.db.query(DriverLicenseModel).filter(
                DriverLicenseModel.organization_id == organization_id
            )
            if record.driver_license_raw:
                norm_lic = record.driver_license_raw.strip().upper().replace("-", "").replace(" ", "")
                lic_query = lic_query.filter(
                    DriverLicenseModel.normalized_license_number == norm_lic
                )
            elif record.driver_id:
                lic_query = lic_query.filter(DriverLicenseModel.driver_id == record.driver_id)

            lic = lic_query.first()
            if lic and lic.expires_at:
                expires_date = (
                    lic.expires_at.date() if isinstance(lic.expires_at, datetime) else lic.expires_at
                )
                if expires_date < date.today():
                    raise DriverLicenseExpiredError(
                        driver_identifier=record.driver_license_raw or str(record.driver_id),
                        expiry_date=expires_date.strftime("%Y-%m-%d"),
                    )

        # 4. State & Decision Updates
        prev_status = str(record.status)
        record.access_decision = str(AccessDecision.APPROVED)
        record.status = str(GateRecordStatus.CHECKED_IN)
        record.check_in_at = datetime.now(timezone.utc)

        # 5. Phase 016 CPV Document Generation via Adapter
        gate = self.gate_repo.get_by_id(record.gate_id, organization_id)
        cpv_document_id = self.doc_adapter.issue_cpv_document(
            record=record,
            gate=gate,
            actor_user_id=guard_user_id,
            appointment_code=appointment_code,
            carrier_name=carrier_name,
        )
        record.document_instance_id = cpv_document_id

        # 6. Audit History Record
        history = GateControlHistoryModel(
            record_id=record.id,
            previous_status=prev_status,
            new_status=str(GateRecordStatus.CHECKED_IN),
            changed_by_user_id=guard_user_id,
            change_reason="Ingreso de vehículo autorizado por agente de seguridad. CPV emitido.",
        )
        self.record_repo.add_history(history)
        self.record_repo.update(record, expected_version=request.expected_version)
        self.db.commit()

        loaded = self.record_repo.get_by_id(record.id, organization_id)
        return GateControlRecordResponse.from_model(loaded)

    def deny_entry(
        self, request: GateDecisionRequest, organization_id: UUID, guard_user_id: UUID
    ) -> GateControlRecordResponse:
        """Deny vehicle entry at gate with mandatory rejection reason."""
        record = self.record_repo.get_by_id(request.record_id, organization_id)
        if not record:
            raise GateRecordNotFoundError(str(request.record_id))

        if str(record.status) in (
            str(GateRecordStatus.CHECKED_OUT),
            str(GateRecordStatus.REJECTED),
            str(GateRecordStatus.CANCELLED),
        ):
            raise InvalidGateStateError(f"No se puede denegar un registro en estado '{record.status}'.")

        if not request.rejection_reason or not request.rejection_reason.strip():
            raise InvalidGateStateError("Debe proporcionar un motivo de rechazo explícito.")

        prev_status = str(record.status)
        record.access_decision = str(AccessDecision.DENIED)
        record.status = str(GateRecordStatus.REJECTED)
        record.rejection_reason = request.rejection_reason.strip()

        history = GateControlHistoryModel(
            record_id=record.id,
            previous_status=prev_status,
            new_status=str(GateRecordStatus.REJECTED),
            changed_by_user_id=guard_user_id,
            change_reason=f"Ingreso denegado: {request.rejection_reason.strip()}",
        )
        self.record_repo.add_history(history)
        self.record_repo.update(record, expected_version=request.expected_version)
        self.db.commit()

        loaded = self.record_repo.get_by_id(record.id, organization_id)
        return GateControlRecordResponse.from_model(loaded)

    def process_checkout(
        self, request: GateCheckOutRequest, organization_id: UUID, guard_user_id: UUID
    ) -> GateControlRecordResponse:
        """Record vehicle check-out and departure."""
        record = self.record_repo.get_by_id(request.record_id, organization_id)
        if not record:
            raise GateRecordNotFoundError(str(request.record_id))

        if str(record.status) != str(GateRecordStatus.CHECKED_IN) or str(record.access_decision) != str(AccessDecision.APPROVED):
            raise InvalidGateStateError(
                f"Solo se puede registrar salida de un vehículo en estado CHECKED_IN autorizado (estado actual: {record.status}, decisión: {record.access_decision})."
            )

        prev_status = str(record.status)
        record.status = str(GateRecordStatus.CHECKED_OUT)
        record.check_out_at = request.check_out_at or datetime.now(timezone.utc)

        history = GateControlHistoryModel(
            record_id=record.id,
            previous_status=prev_status,
            new_status=str(GateRecordStatus.CHECKED_OUT),
            changed_by_user_id=guard_user_id,
            change_reason=request.notes or "Salida de vehículo registrada.",
        )
        self.record_repo.add_history(history)
        self.record_repo.update(record, expected_version=request.expected_version)
        self.db.commit()

        loaded = self.record_repo.get_by_id(record.id, organization_id)
        return GateControlRecordResponse.from_model(loaded)
