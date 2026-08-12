"""Phase 016 Document Engine Adapter for Gate Control (CPV issuance)."""

from __future__ import annotations

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.logistics.documents.application.lifecycle_service import DocumentLifecycleService
from app.modules.logistics.documents.rendering.inbound_schemas import InboundCpvContext
from app.modules.logistics.gate_control.domain.enums import SealStatus
from app.modules.logistics.gate_control.domain.models import GateControlRecordModel, WarehouseGateModel


class GateControlDocumentAdapter:
    """Adapter invoking Phase 016 Document Engine to issue Control de Puerta Vehicular (CPV)."""

    def __init__(self, db: Session):
        self.db = db
        self.lifecycle_service = DocumentLifecycleService(db)

    def issue_cpv_document(
        self,
        record: GateControlRecordModel,
        gate: Optional[WarehouseGateModel],
        actor_user_id: UUID,
        appointment_code: Optional[str] = None,
        carrier_name: Optional[str] = None,
        driver_name: Optional[str] = None,
    ) -> UUID:
        """Constructs CPV context, creates draft document instance, and issues official document."""
        arrival_str = (
            record.arrival_at.strftime("%Y-%m-%d %H:%M:%S")
            if record.arrival_at else ""
        )
        gate_code_name = f"{gate.code} - {gate.name}" if gate else "PUERTA PRINCIPAL"
        warehouse_id = gate.warehouse_id if gate else record.organization_id

        # Build structured CPV rendering context
        cpv_context = InboundCpvContext(
            gate_event_type="INGRESO",
            arrival_at=arrival_str,
            gate=gate_code_name,
            gate_operator=str(actor_user_id),
            access_decision="AUTORIZADO",
            appointment_reference=appointment_code or record.record_code,
            plate=record.plate_observed,
            vehicle_type="Vehículo Carga",
            driver_name=driver_name or "Conductor Registrado",
            driver_dni_raw=record.driver_dni_raw,
            driver_license_raw=record.driver_license_raw,
            carrier_name=carrier_name or "Transportista General",
            seal_number=str(record.seal_status),
            seal_status="COINCIDE" if str(record.seal_status) == str(SealStatus.INTACT) else str(record.seal_status),
        )

        # 1. Create Draft Document Instance
        document_draft = self.lifecycle_service.create_draft(
            organization_id=record.organization_id,
            branch_id=None,
            warehouse_id=warehouse_id,
            doc_type_code="CPV",
            source_resource_type="GATE_CONTROL_RECORD",
            source_resource_id=record.id,
            source_operation_id=None,
            title="Control de Puerta Vehicular",
            structured_data=cpv_context.model_dump(),
            sensitivity="INTERNAL",
            actor_id=actor_user_id,
        )

        # 2. Issue Document Instance
        idempotency_key = f"gate_record:{record.id}:cpv_issue"
        issued_document = self.lifecycle_service.issue_document(
            document_id=document_draft.id,
            idempotency_key=idempotency_key,
            actor_id=actor_user_id,
        )

        return issued_document.id
