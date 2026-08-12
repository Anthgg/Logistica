"""CPV document lifecycle integration for Phase 037 gate check-ins."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.modules.logistics.documents.application.lifecycle_service import (
    DocumentLifecycleService,
)
from app.modules.logistics.documents.models import (
    DocumentInstanceModel,
    DocumentSnapshotModel,
)
from app.modules.logistics.inbound.gate_control.application.services import (
    GateCheckInSnapshotProvider,
)
from app.modules.logistics.inbound.gate_control.domain.errors import (
    GateCheckInNotFoundError,
)
from app.modules.logistics.inbound.gate_control.domain.value_objects import (
    GateCheckInStatus,
)
from app.modules.logistics.inbound.gate_control.infrastructure.persistence.models import (
    GateCheckInModel,
    WarehouseGateModel,
)


class GateCheckInDocumentService:
    """Creates, issues and resolves the immutable CPV for a gate check-in."""

    _ALLOWED_FOR_ISSUE = {
        GateCheckInStatus.ENTRY_AUTHORIZED.value,
        GateCheckInStatus.ENTRY_AUTHORIZED_WITH_OBSERVATIONS.value,
        GateCheckInStatus.ENTRY_DENIED.value,
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.documents = DocumentLifecycleService(db)
        self.snapshots = GateCheckInSnapshotProvider(db)

    def _get_check_in(
        self,
        check_in_id: UUID,
        organization_id: UUID,
        *,
        lock: bool = False,
    ) -> GateCheckInModel:
        stmt = select(GateCheckInModel).where(
            GateCheckInModel.id == check_in_id,
            GateCheckInModel.organization_id == organization_id,
        )
        if lock:
            stmt = stmt.with_for_update()
        check_in = self.db.scalars(stmt).first()
        if check_in is None:
            raise GateCheckInNotFoundError(str(check_in_id))
        return check_in

    def _resolve_linked_document(
        self,
        check_in: GateCheckInModel,
        *,
        repair_orphan: bool,
    ) -> DocumentInstanceModel | None:
        if not check_in.document_instance_id:
            return None

        document = self.db.get(DocumentInstanceModel, check_in.document_instance_id)
        if document is None:
            # Early Phase 037 builds persisted a random placeholder UUID instead of
            # a DocumentInstance. Repair that legacy link only during issuance.
            if repair_orphan:
                check_in.document_instance_id = None
                self.db.flush()
                return None
            raise ApplicationError(
                "GATE_DOCUMENT_NOT_FOUND",
                "El CPV vinculado no existe. Vuelva a emitir el documento.",
                404,
            )

        link_is_valid = (
            document.organization_id == check_in.organization_id
            and document.source_resource_type == "GATE_CHECK_IN"
            and document.source_resource_id == check_in.id
        )
        if not link_is_valid:
            raise ApplicationError(
                "GATE_DOCUMENT_LINK_INVALID",
                "El CPV vinculado no corresponde a este check-in.",
                409,
            )
        return document

    @staticmethod
    def _pick(source: Any, *keys: str) -> Any:
        if not isinstance(source, dict):
            return None
        for key in keys:
            value = source.get(key)
            if value not in (None, ""):
                return value
        return None

    def _build_render_payload(
        self,
        check_in: GateCheckInModel,
        snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        vehicle = snapshot.get("vehicle_inspection") or {}
        driver = snapshot.get("driver_inspection") or {}
        seal = snapshot.get("seal_inspection") or {}
        observed_transport = snapshot.get("observed_transport") or {}
        expected_transport = snapshot.get("expected_transport") or {}
        carrier = snapshot.get("carrier") or {}
        guard = snapshot.get("guard") or {}

        gate = self.db.get(WarehouseGateModel, check_in.gate_id)
        gate_label = "Puerta de almacén"
        if gate:
            gate_label = " - ".join(
                part for part in (getattr(gate, "code", None), getattr(gate, "name", None))
                if part
            ) or gate_label

        decision_labels = {
            GateCheckInStatus.ENTRY_AUTHORIZED.value: "AUTORIZADO",
            GateCheckInStatus.ENTRY_AUTHORIZED_WITH_OBSERVATIONS.value: (
                "AUTORIZADO CON OBSERVACIONES"
            ),
            GateCheckInStatus.ENTRY_DENIED.value: "DENEGADO",
        }

        # The CPV template consumes a flat rendering context. The complete Phase
        # 037 snapshot is also embedded so the issued artifact remains traceable.
        return {
            "gate_event_type": "INGRESO",
            "arrival_at": snapshot.get("arrived_at"),
            "gate": gate_label,
            "gate_operator": self._pick(
                guard, "display_name", "full_name", "name", "email"
            ) or str(check_in.guard_user_id),
            "access_decision": decision_labels.get(check_in.status, check_in.status),
            "appointment_reference": (
                check_in.appointment_code_snapshot
                or check_in.check_in_code
                or str(check_in.id)
            ),
            "plate": (
                self._pick(vehicle, "observed_plate", "expected_plate")
                or self._pick(observed_transport, "plate", "vehicle_plate")
                or self._pick(expected_transport, "plate", "vehicle_plate")
                or "—"
            ),
            "vehicle_type": (
                self._pick(
                    observed_transport,
                    "vehicle_type",
                    "vehicle_type_name",
                    "type",
                )
                or self._pick(
                    expected_transport,
                    "vehicle_type",
                    "vehicle_type_name",
                    "type",
                )
                or "Vehículo de carga"
            ),
            "driver_name": self._pick(
                driver, "observed_name_snapshot", "driver_name", "name"
            ) or "Conductor no consignado",
            # Phase 037 stores only redacted identifiers in the immutable snapshot.
            "driver_dni_masked": self._pick(
                driver, "observed_document_number_redacted"
            ) or "No consignado",
            "driver_license_masked": self._pick(
                driver, "license_number_redacted"
            ) or "No consignado",
            "carrier_name": self._pick(
                carrier,
                "display_name",
                "legal_name",
                "business_name",
                "trade_name",
                "name",
                "razon_social",
            ) or "Transportista no consignado",
            "seal_number": self._pick(
                seal, "observed_seal_number", "expected_seal_number"
            ) or "No aplica",
            "seal_status": self._pick(
                seal, "seal_match_status", "physical_status", "inspection_result"
            ) or "NO APLICA",
            "gate_check_in_snapshot": snapshot,
        }

    def ensure_draft(
        self,
        check_in_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
    ) -> DocumentInstanceModel:
        check_in = self._get_check_in(check_in_id, organization_id, lock=True)
        document = self._resolve_linked_document(check_in, repair_orphan=True)
        if document is not None:
            return document

        if check_in.status not in self._ALLOWED_FOR_ISSUE:
            raise ApplicationError(
                "GATE_DOCUMENT_NOT_READY",
                "El CPV solo puede emitirse una vez tomada la decisión de ingreso.",
                422,
            )

        snapshot = self.snapshots.build(check_in)
        document = self.documents.create_draft(
            organization_id=check_in.organization_id,
            branch_id=check_in.branch_id,
            warehouse_id=check_in.warehouse_id,
            doc_type_code="CPV",
            source_resource_type="GATE_CHECK_IN",
            source_resource_id=check_in.id,
            source_operation_id=None,
            title="Control de Puerta Vehicular",
            structured_data=self._build_render_payload(check_in, snapshot),
            sensitivity="RESTRICTED",
            actor_id=actor_user_id,
        )
        check_in.document_instance_id = document.id
        check_in.row_version += 1
        self.db.flush()
        return document

    def issue(
        self,
        check_in_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        idempotency_key: str | None,
    ) -> tuple[DocumentInstanceModel, str | None]:
        document = self.ensure_draft(
            check_in_id, organization_id, actor_user_id
        )
        if document.status == "ISSUED":
            issued = document
        else:
            issued = self.documents.issue_document(
                document.id,
                idempotency_key=(
                    idempotency_key or f"gate-check-in:{check_in_id}:cpv"
                ),
                actor_id=actor_user_id,
            )
        return issued, self.snapshot_hash(issued)

    def snapshot_hash(self, document: DocumentInstanceModel) -> str | None:
        if not document.current_snapshot_id:
            return None
        snapshot = self.db.get(DocumentSnapshotModel, document.current_snapshot_id)
        if snapshot is None or not isinstance(snapshot.canonical_payload, dict):
            return None
        gate_snapshot = snapshot.canonical_payload.get("gate_check_in_snapshot")
        if isinstance(gate_snapshot, dict):
            return gate_snapshot.get("content_hash")
        return snapshot.canonical_payload.get("content_hash")

    def get_document(
        self,
        check_in_id: UUID,
        organization_id: UUID,
    ) -> DocumentInstanceModel:
        check_in = self._get_check_in(check_in_id, organization_id)
        document = self._resolve_linked_document(check_in, repair_orphan=False)
        if document is None:
            raise ApplicationError(
                "GATE_DOCUMENT_NOT_ISSUED",
                "El CPV aún no ha sido emitido.",
                404,
            )
        return document


__all__ = ["GateCheckInDocumentService"]
