"""Application service for Phase 036 arrival notices and expected allocations."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.warehouse import Warehouse
from app.modules.logistics.drivers.infrastructure.persistence.models import (
    DriverLicenseModel,
    DriverModel,
)
from app.modules.logistics.files.infrastructure.persistence.models import FileAssetModel
from app.modules.logistics.inbound.arrival_notices.application.services.common import (
    content_hash,
    enqueue_event,
    get_notice_for_org,
    get_partner_with_role,
    get_warehouse_for_org,
    json_safe,
    normalize_document_reference,
    normalize_plate,
    partner_snapshot,
    utc_now,
    write_audit,
)
from app.modules.logistics.inbound.arrival_notices.application.services.idempotency import (
    get_idempotent_response,
    save_idempotent_response,
)
from app.modules.logistics.inbound.arrival_notices.application.services.snapshot_provider import (
    ArrivalNoticeSnapshotProvider,
)
from app.modules.logistics.inbound.arrival_notices.domain.errors.exceptions import (
    ArrivalNoticeDriverInvalid,
    ArrivalNoticeDriverLicenseExpired,
    ArrivalNoticeGuideRequired,
    ArrivalNoticeNotEditable,
    ArrivalNoticeNotFound,
    ArrivalNoticePurchaseOrderInvalid,
    ArrivalNoticeQuantityExceeded,
    ArrivalNoticeRevisionConflict,
    ArrivalNoticeSupplierMismatch,
    ArrivalNoticeTransportDocumentInvalid,
    ArrivalNoticeTransportIncomplete,
    ArrivalNoticeUnitInvalid,
    ArrivalNoticeVehicleInvalid,
    ArrivalNoticeVehicleVerificationExpired,
)
from app.modules.logistics.inbound.arrival_notices.domain.policies.state_machine import (
    ensure_arrival_notice_transition,
)
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeDriverReferenceModel,
    ArrivalNoticeExpectedLineModel,
    ArrivalNoticeModel,
    ArrivalNoticePurchaseOrderReferenceModel,
    ArrivalNoticeRevisionModel,
    ArrivalNoticeTransportDocumentModel,
    ArrivalNoticeVehicleReferenceModel,
    InboundExpectedQuantityAllocationModel,
)
from app.modules.logistics.partners.models import BusinessPartnerModel
from app.modules.logistics.procurement.purchase_orders.infrastructure.persistence.models import (
    PurchaseOrderLineModel,
    PurchaseOrderModel,
    PurchaseOrderRevisionModel,
)
from app.modules.logistics.units.conversion_engine import UnitConversionEngine
from app.modules.logistics.units.models import MeasurementDimensionModel, UnitOfMeasureModel
from app.modules.logistics.units.path_resolver import ConversionPathResolver
from app.modules.logistics.vehicle_verifications.infrastructure.persistence.models import (
    VehicleVerificationModel,
)
from app.modules.logistics.vehicles.infrastructure.persistence.models import VehicleModel

EDITABLE_REVISION_STATUSES = {"EDITABLE"}
ELIGIBLE_PURCHASE_ORDER_STATUSES = {"ISSUED", "SENT", "ACKNOWLEDGED"}
ACTIVE_ALLOCATION_STATUSES = {"HELD", "ACTIVE"}
GUIDE_KINDS = {"REMISSION_GUIDE", "CARRIER_GUIDE"}


class ArrivalNoticeService:
    def __init__(self, db: Session):
        self.db = db
        self.snapshot_provider = ArrivalNoticeSnapshotProvider(db)

    # ------------------------------------------------------------------
    # Lookup and validation helpers
    # ------------------------------------------------------------------
    def get(self, notice_id: UUID, organization_id: UUID, *, lock: bool = False):
        return get_notice_for_org(self.db, notice_id, organization_id, lock=lock)

    def get_revision(
        self,
        revision_id: UUID,
        organization_id: UUID,
        *,
        lock: bool = False,
    ) -> ArrivalNoticeRevisionModel:
        stmt = (
            select(ArrivalNoticeRevisionModel)
            .join(
                ArrivalNoticeModel,
                ArrivalNoticeModel.id == ArrivalNoticeRevisionModel.arrival_notice_id,
            )
            .where(
                ArrivalNoticeRevisionModel.id == revision_id,
                ArrivalNoticeModel.organization_id == organization_id,
            )
        )
        if lock:
            stmt = stmt.with_for_update()
        revision = self.db.scalar(stmt)
        if revision is None:
            raise ArrivalNoticeNotFound("La revisión del aviso no existe.")
        return revision

    @staticmethod
    def _ensure_editable_revision(revision: ArrivalNoticeRevisionModel) -> None:
        if revision.status not in EDITABLE_REVISION_STATUSES:
            raise ArrivalNoticeNotEditable("La revisión está congelada y no admite cambios.")

    def _validate_mass_unit(
        self,
        unit_id: UUID,
        organization_id: UUID,
    ) -> tuple[UnitOfMeasureModel, MeasurementDimensionModel]:
        unit = self.db.get(UnitOfMeasureModel, unit_id)
        if (
            unit is None
            or unit.status != "ACTIVE"
            or (
                unit.organization_id is not None
                and str(unit.organization_id) != str(organization_id)
            )
        ):
            raise ArrivalNoticeUnitInvalid("La unidad de peso no es válida.")
        dimension = self.db.get(MeasurementDimensionModel, unit.dimension_id)
        if dimension is None or dimension.code.upper() != "MASS":
            raise ArrivalNoticeUnitInvalid("La unidad de peso debe pertenecer a MASS.")
        return unit, dimension

    def _convert_quantity(
        self,
        *,
        quantity: Decimal,
        source_unit_id: UUID,
        target_unit_id: UUID,
        organization_id: UUID,
        product_id: UUID | None,
    ) -> tuple[Decimal, Decimal | None, UUID | None]:
        source = self.db.get(UnitOfMeasureModel, source_unit_id)
        target = self.db.get(UnitOfMeasureModel, target_unit_id)
        if source is None or target is None or source.dimension_id != target.dimension_id:
            raise ArrivalNoticeUnitInvalid("La unidad no es compatible con la línea de OC.")
        if source.id == target.id:
            return quantity, Decimal("1"), None
        resolver = ConversionPathResolver(self.db)
        try:
            factor, path, applied_rules = resolver.resolve_path(
                source_unit_id,
                target_unit_id,
                organization_id=organization_id,
                product_id=product_id,
            )
        except Exception as exc:
            raise ArrivalNoticeUnitInvalid(
                "No existe una regla autorizada para convertir la unidad."
            ) from exc
        result = UnitConversionEngine.convert(
            quantity=quantity,
            source_code=source.code,
            target_code=target.code,
            effective_factor=factor,
            path=path,
            precision=target.decimal_precision,
            rounding_policy="HALF_UP",
            integer_only_target=target.integer_only,
        )
        conversion_rule_id = (
            UUID(str(applied_rules[-1]["rule_id"]))
            if applied_rules and applied_rules[-1].get("rule_id")
            else None
        )
        return Decimal(result["rounded_result"]), factor, conversion_rule_id

    def _normalize_weight(
        self,
        weight: Decimal,
        unit_id: UUID,
        organization_id: UUID,
    ) -> tuple[Decimal, UUID]:
        unit, dimension = self._validate_mass_unit(unit_id, organization_id)
        target_id = dimension.canonical_unit_id or unit.id
        normalized, _, _ = self._convert_quantity(
            quantity=weight,
            source_unit_id=unit.id,
            target_unit_id=target_id,
            organization_id=organization_id,
            product_id=None,
        )
        return normalized, target_id

    def _purchase_orders(
        self,
        purchase_order_ids: list[UUID],
        organization_id: UUID,
        supplier_id: UUID,
        warehouse_id: UUID,
    ) -> list[tuple[PurchaseOrderModel, PurchaseOrderRevisionModel]]:
        if len(set(purchase_order_ids)) != len(purchase_order_ids):
            raise ArrivalNoticePurchaseOrderInvalid("No se permiten OC repetidas.")
        orders = list(
            self.db.scalars(
                select(PurchaseOrderModel)
                .where(
                    PurchaseOrderModel.id.in_(purchase_order_ids),
                    PurchaseOrderModel.organization_id == organization_id,
                )
                .with_for_update()
            )
        )
        if len(orders) != len(purchase_order_ids):
            raise ArrivalNoticePurchaseOrderInvalid(
                "Una o más OC no existen dentro de la organización."
            )
        result: list[tuple[PurchaseOrderModel, PurchaseOrderRevisionModel]] = []
        for order in orders:
            if order.status not in ELIGIBLE_PURCHASE_ORDER_STATUSES:
                raise ArrivalNoticePurchaseOrderInvalid(
                    f"La OC {order.purchase_order_code or order.id} no está emitida."
                )
            if str(order.supplier_business_partner_id) != str(supplier_id):
                raise ArrivalNoticeSupplierMismatch(
                    "Todas las OC deben corresponder al mismo proveedor."
                )
            if (
                order.destination_warehouse_id is not None
                and str(order.destination_warehouse_id) != str(warehouse_id)
            ):
                raise ArrivalNoticePurchaseOrderInvalid(
                    f"La OC {order.purchase_order_code or order.id} no permite entrega en el almacén."
                )
            revision_id = order.issued_revision_id or order.approved_revision_id or order.active_revision_id
            revision = self.db.get(PurchaseOrderRevisionModel, revision_id)
            if revision is None:
                raise ArrivalNoticePurchaseOrderInvalid(
                    f"La OC {order.purchase_order_code or order.id} no tiene revisión emitida."
                )
            result.append((order, revision))
        return result

    # ------------------------------------------------------------------
    # Aggregate lifecycle
    # ------------------------------------------------------------------
    def create_notice(
        self,
        *,
        organization_id: UUID,
        actor_user_id: UUID,
        session_id: UUID | None,
        correlation_id: str | None,
        data: dict,
    ) -> ArrivalNoticeModel:
        data = dict(data)
        idempotency_key = data.pop("idempotency_key", None)
        request_payload = dict(data)
        cached = get_idempotent_response(
            self.db,
            organization_id,
            "arrival_notice.create",
            idempotency_key,
            request_payload,
        )
        if cached:
            return self.get(UUID(cached["resource_id"]), organization_id)

        warehouse = get_warehouse_for_org(self.db, data["warehouse_id"], organization_id)
        if str(warehouse.branch_id) != str(data["branch_id"]):
            raise ArrivalNoticePurchaseOrderInvalid("El almacén no pertenece a la sede indicada.")
        supplier, _ = get_partner_with_role(
            self.db,
            data["supplier_business_partner_id"],
            organization_id,
            "SUPPLIER",
        )
        carrier = None
        if data.get("carrier_business_partner_id"):
            carrier, _ = get_partner_with_role(
                self.db,
                data["carrier_business_partner_id"],
                organization_id,
                "CARRIER",
            )
        orders = self._purchase_orders(
            data.pop("purchase_order_ids"),
            organization_id,
            supplier.id,
            warehouse.id,
        )
        normalized_weight, normalized_weight_unit_id = self._normalize_weight(
            data["expected_gross_weight"],
            data["weight_unit_id"],
            organization_id,
        )
        supplier_data = partner_snapshot(supplier)
        carrier_data = partner_snapshot(carrier) if carrier else None
        notice = ArrivalNoticeModel(
            organization_id=organization_id,
            supplier_snapshot=supplier_data,
            carrier_snapshot=carrier_data,
            normalized_gross_weight=normalized_weight,
            normalized_weight_unit_id=normalized_weight_unit_id,
            special_handling_summary=[
                item.value if hasattr(item, "value") else str(item)
                for item in data.pop("special_requirements", [])
            ],
            created_by=actor_user_id,
            updated_by=actor_user_id,
            total_purchase_orders=len(orders),
            **data,
        )
        for enum_field in ("submission_channel", "source_type", "transport_mode"):
            value = getattr(notice, enum_field)
            if hasattr(value, "value"):
                setattr(notice, enum_field, value.value)
        self.db.add(notice)
        self.db.flush()

        warehouse_snapshot = {
            "id": str(warehouse.id),
            "code": warehouse.code,
            "name": warehouse.name,
            "address": warehouse.address,
            "branch_id": str(warehouse.branch_id),
            "captured_at": utc_now().isoformat(),
        }
        revision = ArrivalNoticeRevisionModel(
            arrival_notice_id=notice.id,
            revision_number=1,
            status="EDITABLE",
            supplier_snapshot=supplier_data,
            carrier_snapshot=carrier_data,
            warehouse_snapshot=warehouse_snapshot,
            special_requirements=notice.special_handling_summary,
            comments=notice.comments,
            expected_load_summary={
                "pallets": notice.expected_pallet_count,
                "packages": notice.expected_package_count,
                "loose_items": notice.expected_loose_item_count,
                "gross_weight": format(notice.expected_gross_weight, "f"),
                "weight_unit_id": str(notice.weight_unit_id),
            },
            created_by=actor_user_id,
        )
        self.db.add(revision)
        self.db.flush()

        po_snapshots = []
        for order, po_revision in orders:
            po_hash = po_revision.content_hash or content_hash(
                {
                    "purchase_order_id": order.id,
                    "revision_id": po_revision.id,
                    "code": order.purchase_order_code,
                    "supplier_id": order.supplier_business_partner_id,
                    "currency_code": order.currency_code,
                    "destination_warehouse_id": order.destination_warehouse_id,
                }
            )
            ref = ArrivalNoticePurchaseOrderReferenceModel(
                arrival_notice_revision_id=revision.id,
                purchase_order_id=order.id,
                purchase_order_revision_id=po_revision.id,
                purchase_order_code=order.purchase_order_code or str(order.id),
                supplier_business_partner_id=order.supplier_business_partner_id,
                currency_code=order.currency_code,
                source_snapshot_hash=po_hash,
                status="ACTIVE",
            )
            self.db.add(ref)
            po_snapshots.append(
                {
                    "purchase_order_id": str(order.id),
                    "purchase_order_revision_id": str(po_revision.id),
                    "purchase_order_code": order.purchase_order_code,
                    "status": order.status,
                    "supplier_business_partner_id": str(order.supplier_business_partner_id),
                    "currency_code": order.currency_code,
                    "destination_warehouse_id": (
                        str(order.destination_warehouse_id)
                        if order.destination_warehouse_id
                        else None
                    ),
                    "content_hash": po_hash,
                }
            )
        revision.purchase_order_snapshots = po_snapshots
        notice.active_revision_id = revision.id
        self.db.flush()

        write_audit(
            self.db,
            event_code="logistics.arrival_notice.created",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=notice.branch_id,
            warehouse_id=notice.warehouse_id,
            resource_type="arrival_notice",
            resource_id=notice.id,
            session_id=session_id,
            correlation_id=correlation_id,
            new_data={"status": notice.status, "revision_id": revision.id},
            metadata={"purchase_order_ids": [order.id for order, _ in orders]},
        )
        save_idempotent_response(
            self.db,
            organization_id,
            actor_user_id,
            "arrival_notice.create",
            idempotency_key,
            request_payload,
            {"resource_id": str(notice.id)},
        )
        return notice

    def update_notice(
        self,
        notice_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        data: dict,
        *,
        session_id: UUID | None = None,
        correlation_id: str | None = None,
    ) -> ArrivalNoticeModel:
        notice = self.get(notice_id, organization_id, lock=True)
        if notice.status not in {"DRAFT", "REQUIRES_CHANGES"}:
            raise ArrivalNoticeNotEditable("Solo un aviso editable puede modificarse.")
        row_version = data.pop("row_version")
        if notice.row_version != row_version:
            raise ArrivalNoticeRevisionConflict("La versión enviada está desactualizada.")
        revision = self.get_revision(notice.active_revision_id, organization_id, lock=True)
        self._ensure_editable_revision(revision)
        previous = {
            "row_version": notice.row_version,
            "expected_arrival_date": notice.expected_arrival_date,
            "transport_mode": notice.transport_mode,
        }
        if "carrier_business_partner_id" in data:
            carrier_id = data["carrier_business_partner_id"]
            if carrier_id:
                carrier, _ = get_partner_with_role(
                    self.db, carrier_id, organization_id, "CARRIER"
                )
                notice.carrier_snapshot = partner_snapshot(carrier)
                revision.carrier_snapshot = notice.carrier_snapshot
            else:
                notice.carrier_snapshot = None
                revision.carrier_snapshot = None
        if "weight_unit_id" in data or "expected_gross_weight" in data:
            weight = data.get("expected_gross_weight", notice.expected_gross_weight)
            unit_id = data.get("weight_unit_id", notice.weight_unit_id)
            normalized, normalized_unit = self._normalize_weight(
                weight, unit_id, organization_id
            )
            notice.normalized_gross_weight = normalized
            notice.normalized_weight_unit_id = normalized_unit
        if "special_requirements" in data:
            special = data.pop("special_requirements")
            notice.special_handling_summary = [
                item.value if hasattr(item, "value") else str(item) for item in special
            ]
            revision.special_requirements = notice.special_handling_summary
        for key, value in data.items():
            if hasattr(value, "value"):
                value = value.value
            setattr(notice, key, value)
        notice.updated_by = actor_user_id
        notice.row_version += 1
        revision.comments = notice.comments
        revision.expected_load_summary = {
            "pallets": notice.expected_pallet_count,
            "packages": notice.expected_package_count,
            "loose_items": notice.expected_loose_item_count,
            "gross_weight": format(notice.expected_gross_weight, "f"),
            "weight_unit_id": str(notice.weight_unit_id),
        }
        self.db.flush()
        write_audit(
            self.db,
            event_code="logistics.arrival_notice.updated",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=notice.branch_id,
            warehouse_id=notice.warehouse_id,
            resource_type="arrival_notice",
            resource_id=notice.id,
            session_id=session_id,
            correlation_id=correlation_id,
            previous_data=previous,
            new_data={
                "row_version": notice.row_version,
                "expected_arrival_date": notice.expected_arrival_date,
                "transport_mode": notice.transport_mode,
            },
        )
        return notice

    def create_revision(
        self,
        notice_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        change_summary: str,
        idempotency_key: str | None,
    ) -> ArrivalNoticeRevisionModel:
        notice = self.get(notice_id, organization_id, lock=True)
        payload = {"notice_id": notice_id, "change_summary": change_summary}
        cached = get_idempotent_response(
            self.db,
            organization_id,
            "arrival_notice.revision.create",
            idempotency_key,
            payload,
        )
        if cached:
            return self.get_revision(UUID(cached["resource_id"]), organization_id)
        if notice.status != "REQUIRES_CHANGES":
            raise ArrivalNoticeNotEditable(
                "Una nueva revisión solo procede cuando se solicitaron cambios."
            )
        old = self.get_revision(notice.active_revision_id, organization_id, lock=True)
        old.status = "SUPERSEDED"
        revision = ArrivalNoticeRevisionModel(
            arrival_notice_id=notice.id,
            revision_number=notice.current_revision_number + 1,
            status="EDITABLE",
            supplier_snapshot=old.supplier_snapshot,
            carrier_snapshot=old.carrier_snapshot,
            warehouse_snapshot=old.warehouse_snapshot,
            purchase_order_snapshots=old.purchase_order_snapshots,
            transport_snapshot=old.transport_snapshot,
            document_references_snapshot=old.document_references_snapshot,
            expected_load_summary=old.expected_load_summary,
            proposed_window=old.proposed_window,
            special_requirements=old.special_requirements,
            comments=old.comments,
            created_from_revision_id=old.id,
            change_summary=change_summary,
            created_by=actor_user_id,
        )
        self.db.add(revision)
        self.db.flush()
        ref_map: dict[UUID, UUID] = {}
        old_refs = list(
            self.db.scalars(
                select(ArrivalNoticePurchaseOrderReferenceModel).where(
                    ArrivalNoticePurchaseOrderReferenceModel.arrival_notice_revision_id
                    == old.id
                )
            )
        )
        for ref in old_refs:
            clone = ArrivalNoticePurchaseOrderReferenceModel(
                arrival_notice_revision_id=revision.id,
                purchase_order_id=ref.purchase_order_id,
                purchase_order_revision_id=ref.purchase_order_revision_id,
                purchase_order_code=ref.purchase_order_code,
                supplier_business_partner_id=ref.supplier_business_partner_id,
                currency_code=ref.currency_code,
                source_snapshot_hash=ref.source_snapshot_hash,
                status="ACTIVE",
            )
            self.db.add(clone)
            self.db.flush()
            ref_map[ref.id] = clone.id
        old_lines = list(
            self.db.scalars(
                select(ArrivalNoticeExpectedLineModel).where(
                    ArrivalNoticeExpectedLineModel.arrival_notice_revision_id == old.id,
                    ArrivalNoticeExpectedLineModel.status == "EXPECTED",
                )
            )
        )
        for line in old_lines:
            clone = ArrivalNoticeExpectedLineModel(
                arrival_notice_revision_id=revision.id,
                purchase_order_reference_id=ref_map[line.purchase_order_reference_id],
                purchase_order_line_id=line.purchase_order_line_id,
                purchase_order_schedule_line_id=line.purchase_order_schedule_line_id,
                line_number=line.line_number,
                product_id=line.product_id,
                product_version_id=line.product_version_id,
                sku_snapshot=line.sku_snapshot,
                product_name_snapshot=line.product_name_snapshot,
                expected_quantity=line.expected_quantity,
                expected_unit_id=line.expected_unit_id,
                expected_base_quantity=line.expected_base_quantity,
                base_unit_id=line.base_unit_id,
                conversion_rule_id=line.conversion_rule_id,
                conversion_factor_snapshot=line.conversion_factor_snapshot,
                expected_package_count=line.expected_package_count,
                expected_pallet_count=line.expected_pallet_count,
                supplier_lot_reference=line.supplier_lot_reference,
                supplier_expiration_reference=line.supplier_expiration_reference,
                notes=line.notes,
                status="EXPECTED",
            )
            self.db.add(clone)
            self.db.flush()
            allocation = self.db.scalar(
                select(InboundExpectedQuantityAllocationModel)
                .where(
                    InboundExpectedQuantityAllocationModel.expected_line_id == line.id,
                    InboundExpectedQuantityAllocationModel.status.in_(
                        ACTIVE_ALLOCATION_STATUSES
                    ),
                )
                .with_for_update()
            )
            if allocation:
                allocation.status = "RELEASED"
                allocation.released_at = utc_now()
                allocation.release_reason = "SUPERSEDED_REVISION"
                self.db.add(
                    InboundExpectedQuantityAllocationModel(
                        organization_id=organization_id,
                        arrival_notice_id=notice.id,
                        expected_line_id=clone.id,
                        purchase_order_line_id=clone.purchase_order_line_id,
                        purchase_order_schedule_line_id=clone.purchase_order_schedule_line_id,
                        allocated_quantity=clone.expected_quantity,
                        allocated_unit_id=clone.expected_unit_id,
                        allocated_base_quantity=clone.expected_base_quantity,
                        status="HELD",
                    )
                )
        notice.current_revision_number = revision.revision_number
        notice.active_revision_id = revision.id
        notice.status = "DRAFT"
        notice.row_version += 1
        self.db.flush()
        write_audit(
            self.db,
            event_code="logistics.arrival_notice.revision_created",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=notice.branch_id,
            warehouse_id=notice.warehouse_id,
            resource_type="arrival_notice",
            resource_id=notice.id,
            new_data={"revision_id": revision.id, "revision_number": revision.revision_number},
            reason=change_summary,
        )
        save_idempotent_response(
            self.db,
            organization_id,
            actor_user_id,
            "arrival_notice.revision.create",
            idempotency_key,
            payload,
            {"resource_id": str(revision.id)},
        )
        return revision

    # ------------------------------------------------------------------
    # Expected lines and allocations
    # ------------------------------------------------------------------
    def add_line(
        self,
        revision_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        data: dict,
    ) -> ArrivalNoticeExpectedLineModel:
        idempotency_key = data.pop("idempotency_key", None)
        cached = get_idempotent_response(
            self.db,
            organization_id,
            "arrival_notice.line.create",
            idempotency_key,
            data,
        )
        if cached:
            line = self.db.get(ArrivalNoticeExpectedLineModel, UUID(cached["resource_id"]))
            if line is None:
                raise ArrivalNoticeNotFound("La línea esperada ya no existe.")
            return line
        revision = self.get_revision(revision_id, organization_id, lock=True)
        self._ensure_editable_revision(revision)
        notice = self.get(revision.arrival_notice_id, organization_id, lock=True)
        po_ref = self.db.scalar(
            select(ArrivalNoticePurchaseOrderReferenceModel).where(
                ArrivalNoticePurchaseOrderReferenceModel.id
                == data["purchase_order_reference_id"],
                ArrivalNoticePurchaseOrderReferenceModel.arrival_notice_revision_id
                == revision.id,
            )
        )
        if po_ref is None:
            raise ArrivalNoticePurchaseOrderInvalid(
                "La referencia de OC no pertenece a la revisión."
            )
        po_line = self.db.scalar(
            select(PurchaseOrderLineModel)
            .where(
                PurchaseOrderLineModel.id == data["purchase_order_line_id"],
                PurchaseOrderLineModel.purchase_order_revision_id
                == po_ref.purchase_order_revision_id,
                PurchaseOrderLineModel.status == "ACTIVE",
            )
            .with_for_update()
        )
        if po_line is None:
            raise ArrivalNoticePurchaseOrderInvalid(
                "La línea no pertenece a la revisión emitida de la OC."
            )
        target_unit_id = po_line.base_unit_id or po_line.ordered_unit_id
        if target_unit_id is None or po_line.ordered_unit_id is None:
            raise ArrivalNoticeUnitInvalid(
                "La línea de OC no tiene unidades configuradas de forma reutilizable."
            )
        base_quantity, factor, rule_id = self._convert_quantity(
            quantity=data["expected_quantity"],
            source_unit_id=data["expected_unit_id"],
            target_unit_id=target_unit_id,
            organization_id=organization_id,
            product_id=po_line.product_id,
        )
        ordered_base_quantity = po_line.base_quantity or po_line.ordered_quantity
        allocated = self.db.scalar(
            select(
                func.coalesce(
                    func.sum(InboundExpectedQuantityAllocationModel.allocated_base_quantity),
                    0,
                )
            ).where(
                InboundExpectedQuantityAllocationModel.purchase_order_line_id == po_line.id,
                InboundExpectedQuantityAllocationModel.status.in_(ACTIVE_ALLOCATION_STATUSES),
            )
        )
        if Decimal(allocated) + base_quantity > Decimal(ordered_base_quantity):
            raise ArrivalNoticeQuantityExceeded(
                "La cantidad esperada supera la cantidad disponible de la OC.",
                details={
                    "ordered_base_quantity": format(
                        Decimal(ordered_base_quantity), "f"
                    ),
                    "already_allocated_base_quantity": format(Decimal(allocated), "f"),
                    "requested_base_quantity": format(base_quantity, "f"),
                },
            )
        line = ArrivalNoticeExpectedLineModel(
            arrival_notice_revision_id=revision.id,
            purchase_order_reference_id=po_ref.id,
            purchase_order_line_id=po_line.id,
            purchase_order_schedule_line_id=data.get("purchase_order_schedule_line_id"),
            line_number=po_line.line_number,
            product_id=po_line.product_id,
            product_version_id=po_line.product_version_id,
            sku_snapshot=po_line.sku_snapshot,
            product_name_snapshot=po_line.product_name_snapshot,
            expected_quantity=data["expected_quantity"],
            expected_unit_id=data["expected_unit_id"],
            expected_base_quantity=base_quantity,
            base_unit_id=target_unit_id,
            conversion_rule_id=rule_id,
            conversion_factor_snapshot=factor,
            expected_package_count=data.get("expected_package_count"),
            expected_pallet_count=data.get("expected_pallet_count"),
            supplier_lot_reference=data.get("supplier_lot_reference"),
            supplier_expiration_reference=data.get("supplier_expiration_reference"),
            notes=data.get("notes"),
            status="EXPECTED",
        )
        self.db.add(line)
        self.db.flush()
        allocation = InboundExpectedQuantityAllocationModel(
            organization_id=organization_id,
            arrival_notice_id=notice.id,
            expected_line_id=line.id,
            purchase_order_line_id=po_line.id,
            purchase_order_schedule_line_id=line.purchase_order_schedule_line_id,
            allocated_quantity=line.expected_quantity,
            allocated_unit_id=line.expected_unit_id,
            allocated_base_quantity=line.expected_base_quantity,
            status="HELD",
        )
        self.db.add(allocation)
        notice.total_lines += 1
        notice.row_version += 1
        self.db.flush()
        write_audit(
            self.db,
            event_code="logistics.arrival_notice.line_created",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=notice.branch_id,
            warehouse_id=notice.warehouse_id,
            resource_type="arrival_notice",
            resource_id=notice.id,
            new_data={
                "line_id": line.id,
                "purchase_order_line_id": po_line.id,
                "expected_quantity": line.expected_quantity,
                "expected_base_quantity": line.expected_base_quantity,
            },
        )
        save_idempotent_response(
            self.db,
            organization_id,
            actor_user_id,
            "arrival_notice.line.create",
            idempotency_key,
            data,
            {"resource_id": str(line.id)},
        )
        return line

    def update_line(
        self,
        line_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        data: dict,
    ) -> ArrivalNoticeExpectedLineModel:
        line = self.db.scalar(
            select(ArrivalNoticeExpectedLineModel)
            .join(
                ArrivalNoticeRevisionModel,
                ArrivalNoticeRevisionModel.id
                == ArrivalNoticeExpectedLineModel.arrival_notice_revision_id,
            )
            .join(
                ArrivalNoticeModel,
                ArrivalNoticeModel.id == ArrivalNoticeRevisionModel.arrival_notice_id,
            )
            .where(
                ArrivalNoticeExpectedLineModel.id == line_id,
                ArrivalNoticeModel.organization_id == organization_id,
            )
            .with_for_update()
        )
        if line is None:
            raise ArrivalNoticeNotFound("La línea esperada no existe.")
        revision = self.get_revision(
            line.arrival_notice_revision_id, organization_id, lock=True
        )
        self._ensure_editable_revision(revision)
        if "expected_quantity" in data or "expected_unit_id" in data:
            po_line = self.db.scalar(
                select(PurchaseOrderLineModel)
                .where(PurchaseOrderLineModel.id == line.purchase_order_line_id)
                .with_for_update()
            )
            target_unit_id = po_line.base_unit_id or po_line.ordered_unit_id
            quantity = data.get("expected_quantity", line.expected_quantity)
            unit_id = data.get("expected_unit_id", line.expected_unit_id)
            new_base, factor, rule_id = self._convert_quantity(
                quantity=quantity,
                source_unit_id=unit_id,
                target_unit_id=target_unit_id,
                organization_id=organization_id,
                product_id=po_line.product_id,
            )
            allocation = self.db.scalar(
                select(InboundExpectedQuantityAllocationModel)
                .where(
                    InboundExpectedQuantityAllocationModel.expected_line_id == line.id
                )
                .with_for_update()
            )
            other_allocated = self.db.scalar(
                select(
                    func.coalesce(
                        func.sum(
                            InboundExpectedQuantityAllocationModel.allocated_base_quantity
                        ),
                        0,
                    )
                ).where(
                    InboundExpectedQuantityAllocationModel.purchase_order_line_id
                    == po_line.id,
                    InboundExpectedQuantityAllocationModel.status.in_(
                        ACTIVE_ALLOCATION_STATUSES
                    ),
                    InboundExpectedQuantityAllocationModel.id != allocation.id,
                )
            )
            ordered_base = po_line.base_quantity or po_line.ordered_quantity
            if Decimal(other_allocated) + new_base > Decimal(ordered_base):
                raise ArrivalNoticeQuantityExceeded(
                    "La actualización excede la cantidad disponible de la OC."
                )
            line.expected_quantity = quantity
            line.expected_unit_id = unit_id
            line.expected_base_quantity = new_base
            line.conversion_factor_snapshot = factor
            line.conversion_rule_id = rule_id
            allocation.allocated_quantity = quantity
            allocation.allocated_unit_id = unit_id
            allocation.allocated_base_quantity = new_base
        for key in (
            "expected_package_count",
            "expected_pallet_count",
            "supplier_lot_reference",
            "supplier_expiration_reference",
            "notes",
        ):
            if key in data:
                setattr(line, key, data[key])
        notice = self.get(revision.arrival_notice_id, organization_id, lock=True)
        notice.row_version += 1
        self.db.flush()
        write_audit(
            self.db,
            event_code="logistics.arrival_notice.updated",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=notice.branch_id,
            warehouse_id=notice.warehouse_id,
            resource_type="arrival_notice",
            resource_id=notice.id,
            new_data={"line_id": line.id, "expected_quantity": line.expected_quantity},
        )
        return line

    def cancel_line(
        self,
        line_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        reason: str,
    ) -> ArrivalNoticeExpectedLineModel:
        line = self.db.get(ArrivalNoticeExpectedLineModel, line_id)
        if line is None:
            raise ArrivalNoticeNotFound("La línea esperada no existe.")
        revision = self.get_revision(
            line.arrival_notice_revision_id, organization_id, lock=True
        )
        self._ensure_editable_revision(revision)
        line.status = "CANCELLED"
        allocation = self.db.scalar(
            select(InboundExpectedQuantityAllocationModel)
            .where(InboundExpectedQuantityAllocationModel.expected_line_id == line.id)
            .with_for_update()
        )
        if allocation and allocation.status in ACTIVE_ALLOCATION_STATUSES:
            allocation.status = "RELEASED"
            allocation.released_at = utc_now()
            allocation.release_reason = reason
        notice = self.get(revision.arrival_notice_id, organization_id, lock=True)
        notice.total_lines = max(0, notice.total_lines - 1)
        notice.row_version += 1
        self.db.flush()
        return line

    # ------------------------------------------------------------------
    # Transport references and readiness
    # ------------------------------------------------------------------
    def set_vehicle_reference(
        self,
        revision_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        data: dict,
    ) -> ArrivalNoticeVehicleReferenceModel:
        revision = self.get_revision(revision_id, organization_id, lock=True)
        self._ensure_editable_revision(revision)
        plate = normalize_plate(data["plate"])
        if len(plate) < 5:
            raise ArrivalNoticeVehicleInvalid("La placa normalizada no tiene formato válido.")
        vehicle = None
        snapshot = None
        verification_summary: dict = {"status": "NOT_VERIFIED"}
        verification_date = None
        verification_expiration = None
        if data.get("vehicle_id"):
            vehicle = self.db.scalar(
                select(VehicleModel).where(
                    VehicleModel.id == data["vehicle_id"],
                    VehicleModel.organization_id == organization_id,
                )
            )
            if vehicle is None:
                raise ArrivalNoticeVehicleInvalid("El vehículo no pertenece a la organización.")
            if vehicle.normalized_plate != plate:
                raise ArrivalNoticeVehicleInvalid(
                    "La placa indicada no coincide con el vehículo seleccionado."
                )
            snapshot = {
                "id": str(vehicle.id),
                "vehicle_code": vehicle.vehicle_code,
                "display_plate": vehicle.display_plate,
                "normalized_plate": vehicle.normalized_plate,
                "vehicle_type": vehicle.vehicle_type,
                "body_type": vehicle.body_type,
                "lifecycle_status": vehicle.lifecycle_status,
                "operational_status": vehicle.operational_status,
                "compliance_status": vehicle.compliance_status,
                "captured_at": utc_now().isoformat(),
            }
            verification = self.db.scalar(
                select(VehicleVerificationModel)
                .where(
                    VehicleVerificationModel.vehicle_id == vehicle.id,
                    VehicleVerificationModel.organization_id == organization_id,
                    VehicleVerificationModel.status == "COMPLETED",
                )
                .order_by(VehicleVerificationModel.completed_at.desc())
            )
            if verification:
                verification_summary = {
                    "verification_id": str(verification.id),
                    "result_status": verification.result_status,
                    "confidence_level": verification.confidence_level,
                    "conflict_status": verification.conflict_status,
                }
                verification_date = verification.completed_at
                verification_expiration = verification.expires_at or verification.stale_at
        elif data["source_type"].value == "VEHICLE_MASTER":
            raise ArrivalNoticeVehicleInvalid(
                "VEHICLE_MASTER requiere un vehicle_id existente."
            )
        existing = self.db.scalar(
            select(ArrivalNoticeVehicleReferenceModel).where(
                ArrivalNoticeVehicleReferenceModel.revision_id == revision.id
            )
        )
        if existing:
            self.db.delete(existing)
            self.db.flush()
        reference = ArrivalNoticeVehicleReferenceModel(
            revision_id=revision.id,
            vehicle_id=vehicle.id if vehicle else None,
            plate_snapshot=data["plate"].upper().strip(),
            normalized_plate=plate,
            vehicle_snapshot=snapshot,
            source_type=data["source_type"].value,
            verification_summary=verification_summary,
            verification_date=verification_date,
            verification_expiration=verification_expiration,
            exception_reason=data.get("exception_reason"),
        )
        self.db.add(reference)
        revision.transport_snapshot = {
            **(revision.transport_snapshot or {}),
            "vehicle_reference": json_safe(snapshot or {"normalized_plate": plate}),
        }
        notice = self.get(revision.arrival_notice_id, organization_id, lock=True)
        notice.row_version += 1
        self.db.flush()
        write_audit(
            self.db,
            event_code=(
                "logistics.arrival_notice.vehicle_override"
                if vehicle is None
                else "logistics.arrival_notice.vehicle_selected"
            ),
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=notice.branch_id,
            warehouse_id=notice.warehouse_id,
            resource_type="arrival_notice",
            resource_id=notice.id,
            new_data={"vehicle_id": reference.vehicle_id, "plate": plate},
            reason=reference.exception_reason,
        )
        return reference

    def set_driver_reference(
        self,
        revision_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        data: dict,
    ) -> ArrivalNoticeDriverReferenceModel:
        revision = self.get_revision(revision_id, organization_id, lock=True)
        self._ensure_editable_revision(revision)
        driver = None
        license_model = None
        if data.get("driver_id"):
            driver = self.db.scalar(
                select(DriverModel).where(
                    DriverModel.id == data["driver_id"],
                    DriverModel.organization_id == organization_id,
                )
            )
            if driver is None:
                raise ArrivalNoticeDriverInvalid(
                    "El conductor no pertenece a la organización."
                )
            license_model = self.db.scalar(
                select(DriverLicenseModel)
                .where(
                    DriverLicenseModel.driver_id == driver.id,
                    DriverLicenseModel.organization_id == organization_id,
                    DriverLicenseModel.status == "ACTIVE",
                )
                .order_by(
                    DriverLicenseModel.primary_license.desc(),
                    DriverLicenseModel.expires_at.desc(),
                )
            )
        elif data["source_type"].value == "DRIVER_MASTER":
            raise ArrivalNoticeDriverInvalid(
                "DRIVER_MASTER requiere un driver_id existente."
            )
        full_name = driver.display_name if driver else data.get("full_name")
        if not full_name:
            raise ArrivalNoticeDriverInvalid(
                "La excepción manual requiere el nombre declarado del conductor."
            )
        existing = self.db.scalar(
            select(ArrivalNoticeDriverReferenceModel).where(
                ArrivalNoticeDriverReferenceModel.revision_id == revision.id
            )
        )
        if existing:
            self.db.delete(existing)
            self.db.flush()
        reference = ArrivalNoticeDriverReferenceModel(
            revision_id=revision.id,
            driver_id=driver.id if driver else None,
            full_name_snapshot=full_name,
            document_type_snapshot=None,
            document_number_redacted_snapshot=None,
            license_number_redacted_snapshot=(
                license_model.masked_license_number if license_model else None
            ),
            license_category_snapshot=None,
            license_expiration_snapshot=(
                license_model.expires_at if license_model else None
            ),
            contact_snapshot=None,
            source_type=data["source_type"].value,
            exception_reason=data.get("exception_reason"),
        )
        self.db.add(reference)
        revision.transport_snapshot = {
            **(revision.transport_snapshot or {}),
            "driver_reference": {
                "driver_id": str(reference.driver_id) if reference.driver_id else None,
                "full_name": reference.full_name_snapshot,
                "license_number_redacted": reference.license_number_redacted_snapshot,
                "license_expiration": (
                    str(reference.license_expiration_snapshot)
                    if reference.license_expiration_snapshot
                    else None
                ),
            },
        }
        notice = self.get(revision.arrival_notice_id, organization_id, lock=True)
        notice.row_version += 1
        self.db.flush()
        write_audit(
            self.db,
            event_code=(
                "logistics.arrival_notice.driver_override"
                if driver is None
                else "logistics.arrival_notice.driver_selected"
            ),
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=notice.branch_id,
            warehouse_id=notice.warehouse_id,
            resource_type="arrival_notice",
            resource_id=notice.id,
            new_data={"driver_id": reference.driver_id},
            reason=reference.exception_reason,
        )
        return reference

    def add_transport_document(
        self,
        revision_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        data: dict,
    ) -> ArrivalNoticeTransportDocumentModel:
        idempotency_key = data.pop("idempotency_key", None)
        cached = get_idempotent_response(
            self.db,
            organization_id,
            "arrival_notice.transport_document.create",
            idempotency_key,
            data,
        )
        if cached:
            document = self.db.get(
                ArrivalNoticeTransportDocumentModel, UUID(cached["resource_id"])
            )
            if document:
                return document
        revision = self.get_revision(revision_id, organization_id, lock=True)
        self._ensure_editable_revision(revision)
        if data.get("issuer_business_partner_id"):
            issuer = self.db.scalar(
                select(BusinessPartnerModel).where(
                    BusinessPartnerModel.id == data["issuer_business_partner_id"],
                    BusinessPartnerModel.organization_id == organization_id,
                )
            )
            if issuer is None:
                raise ArrivalNoticeTransportDocumentInvalid(
                    "El emisor del documento no pertenece a la organización."
                )
        if data.get("file_asset_id"):
            asset = self.db.scalar(
                select(FileAssetModel).where(
                    FileAssetModel.id == data["file_asset_id"],
                    FileAssetModel.organization_id == organization_id,
                )
            )
            if asset is None:
                raise ArrivalNoticeTransportDocumentInvalid(
                    "El archivo no pertenece a la organización."
                )
        kind = data["document_kind"].value
        normalized = normalize_document_reference(data.get("series"), data["number"])
        document = ArrivalNoticeTransportDocumentModel(
            revision_id=revision.id,
            document_kind=kind,
            issuer_business_partner_id=data.get("issuer_business_partner_id"),
            issuer_tax_identifier_snapshot=data.get("issuer_tax_identifier"),
            series=data.get("series"),
            number=data["number"],
            normalized_reference=normalized,
            issue_date=data.get("issue_date"),
            document_date=data.get("document_date"),
            transport_reference=data.get("transport_reference"),
            verification_status="NOT_VERIFIED",
            file_asset_id=data.get("file_asset_id"),
            notes=data.get("notes"),
        )
        self.db.add(document)
        self.db.flush()
        notice = self.get(revision.arrival_notice_id, organization_id, lock=True)
        notice.row_version += 1
        write_audit(
            self.db,
            event_code=(
                "logistics.arrival_notice.guide_registered"
                if kind in GUIDE_KINDS
                else "logistics.arrival_notice.transport_document_added"
            ),
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=notice.branch_id,
            warehouse_id=notice.warehouse_id,
            resource_type="arrival_notice",
            resource_id=notice.id,
            new_data={
                "transport_document_id": document.id,
                "document_kind": kind,
                "verification_status": document.verification_status,
            },
        )
        save_idempotent_response(
            self.db,
            organization_id,
            actor_user_id,
            "arrival_notice.transport_document.create",
            idempotency_key,
            data,
            {"resource_id": str(document.id)},
        )
        return document

    def verify_document_format(
        self,
        document_id: UUID,
        organization_id: UUID,
    ) -> ArrivalNoticeTransportDocumentModel:
        document = self._transport_document_for_org(document_id, organization_id)
        if not document.normalized_reference or len(document.normalized_reference) < 3:
            raise ArrivalNoticeTransportDocumentInvalid(
                "La referencia documental no cumple el formato mínimo."
            )
        document.verification_status = "FORMAT_VALID"
        document.verification_source = "LOCAL_FORMAT_RULES"
        document.verified_at = utc_now()
        self.db.flush()
        return document

    def associate_document_file(
        self,
        document_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        file_asset_id: UUID,
    ) -> ArrivalNoticeTransportDocumentModel:
        document = self._transport_document_for_org(document_id, organization_id)
        asset = self.db.scalar(
            select(FileAssetModel).where(
                FileAssetModel.id == file_asset_id,
                FileAssetModel.organization_id == organization_id,
            )
        )
        if asset is None:
            raise ArrivalNoticeTransportDocumentInvalid(
                "El archivo no pertenece a la organización."
            )
        document.file_asset_id = asset.id
        self.db.flush()
        revision = self.get_revision(document.revision_id, organization_id)
        notice = self.get(revision.arrival_notice_id, organization_id)
        write_audit(
            self.db,
            event_code="logistics.arrival_notice.file_associated",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=notice.branch_id,
            warehouse_id=notice.warehouse_id,
            resource_type="arrival_notice",
            resource_id=notice.id,
            new_data={"transport_document_id": document.id, "file_asset_id": asset.id},
        )
        return document

    def _transport_document_for_org(
        self, document_id: UUID, organization_id: UUID
    ) -> ArrivalNoticeTransportDocumentModel:
        document = self.db.scalar(
            select(ArrivalNoticeTransportDocumentModel)
            .join(
                ArrivalNoticeRevisionModel,
                ArrivalNoticeRevisionModel.id
                == ArrivalNoticeTransportDocumentModel.revision_id,
            )
            .join(
                ArrivalNoticeModel,
                ArrivalNoticeModel.id == ArrivalNoticeRevisionModel.arrival_notice_id,
            )
            .where(
                ArrivalNoticeTransportDocumentModel.id == document_id,
                ArrivalNoticeModel.organization_id == organization_id,
            )
        )
        if document is None:
            raise ArrivalNoticeNotFound("El documento de transporte no existe.")
        return document

    def transport_readiness(
        self,
        notice_id: UUID,
        organization_id: UUID,
        *,
        for_confirmation: bool = False,
    ) -> dict:
        notice = self.get(notice_id, organization_id)
        revision = self.get_revision(notice.active_revision_id, organization_id)
        vehicle_ref = self.db.scalar(
            select(ArrivalNoticeVehicleReferenceModel).where(
                ArrivalNoticeVehicleReferenceModel.revision_id == revision.id
            )
        )
        driver_ref = self.db.scalar(
            select(ArrivalNoticeDriverReferenceModel).where(
                ArrivalNoticeDriverReferenceModel.revision_id == revision.id
            )
        )
        documents = list(
            self.db.scalars(
                select(ArrivalNoticeTransportDocumentModel).where(
                    ArrivalNoticeTransportDocumentModel.revision_id == revision.id,
                    ArrivalNoticeTransportDocumentModel.status == "ACTIVE",
                )
            )
        )
        blocking: list[str] = []
        warnings: list[str] = []
        vehicle_status = "MISSING"
        if vehicle_ref:
            vehicle_status = "READY"
            if vehicle_ref.vehicle_id:
                vehicle = self.db.get(VehicleModel, vehicle_ref.vehicle_id)
                if (
                    vehicle is None
                    or vehicle.lifecycle_status != "ACTIVE"
                    or vehicle.operational_status in {"BLOCKED", "SUSPENDED", "UNAVAILABLE"}
                ):
                    vehicle_status = "BLOCKED"
                    blocking.append("VEHICLE_NOT_OPERATIONAL")
                if (
                    vehicle_ref.verification_expiration
                    and vehicle_ref.verification_expiration <= utc_now()
                ):
                    vehicle_status = "EXPIRED"
                    blocking.append("VEHICLE_VERIFICATION_EXPIRED")
            else:
                vehicle_status = "MANUAL_EXCEPTION"
                warnings.append("VEHICLE_MANUAL_EXCEPTION")
        elif notice.transport_mode != "TO_BE_CONFIRMED":
            blocking.append("VEHICLE_REQUIRED")

        driver_status = "MISSING"
        if driver_ref:
            driver_status = "READY"
            if driver_ref.driver_id:
                driver = self.db.get(DriverModel, driver_ref.driver_id)
                if (
                    driver is None
                    or driver.lifecycle_status != "ACTIVE"
                    or driver.eligibility_status in {"BLOCKED", "INELIGIBLE"}
                ):
                    driver_status = "BLOCKED"
                    blocking.append("DRIVER_NOT_ELIGIBLE")
                if (
                    driver_ref.license_expiration_snapshot
                    and driver_ref.license_expiration_snapshot < date.today()
                ):
                    driver_status = "EXPIRED"
                    blocking.append("DRIVER_LICENSE_EXPIRED")
            else:
                driver_status = "MANUAL_EXCEPTION"
                warnings.append("DRIVER_MANUAL_EXCEPTION")
        elif notice.transport_mode != "TO_BE_CONFIRMED":
            blocking.append("DRIVER_REQUIRED")

        guide_present = any(document.document_kind in GUIDE_KINDS for document in documents)
        document_status = "READY" if guide_present else "GUIDE_MISSING"
        if not guide_present:
            blocking.append("GUIDE_REQUIRED")
        if for_confirmation and notice.transport_mode == "TO_BE_CONFIRMED":
            blocking.append("TRANSPORT_MODE_TO_BE_CONFIRMED")
        return {
            "ready": not blocking,
            "vehicle_status": vehicle_status,
            "driver_status": driver_status,
            "document_status": document_status,
            "blocking_reasons": blocking,
            "warnings": warnings,
        }

    # ------------------------------------------------------------------
    # Validation and explicit status commands
    # ------------------------------------------------------------------
    def validate_notice(
        self, notice_id: UUID, organization_id: UUID, *, for_confirmation: bool = False
    ) -> dict:
        notice = self.get(notice_id, organization_id)
        revision = self.get_revision(notice.active_revision_id, organization_id)
        errors: list[dict] = []
        warnings: list[dict] = []
        po_count = self.db.scalar(
            select(func.count())
            .select_from(ArrivalNoticePurchaseOrderReferenceModel)
            .where(
                ArrivalNoticePurchaseOrderReferenceModel.arrival_notice_revision_id
                == revision.id,
                ArrivalNoticePurchaseOrderReferenceModel.status == "ACTIVE",
            )
        )
        line_count = self.db.scalar(
            select(func.count())
            .select_from(ArrivalNoticeExpectedLineModel)
            .where(
                ArrivalNoticeExpectedLineModel.arrival_notice_revision_id == revision.id,
                ArrivalNoticeExpectedLineModel.status == "EXPECTED",
            )
        )
        if not po_count:
            errors.append({"code": "PURCHASE_ORDER_REQUIRED"})
        if not line_count:
            errors.append({"code": "EXPECTED_LINE_REQUIRED"})
        readiness = self.transport_readiness(
            notice_id, organization_id, for_confirmation=for_confirmation
        )
        for code in readiness["warnings"]:
            warnings.append({"code": code})
        if for_confirmation:
            errors.extend({"code": code} for code in readiness["blocking_reasons"])
        else:
            warnings.extend({"code": code} for code in readiness["blocking_reasons"])
        return {"valid": not errors, "errors": errors, "warnings": warnings}

    def submit(
        self,
        notice_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        idempotency_key: str | None,
    ) -> ArrivalNoticeModel:
        payload = {"notice_id": notice_id}
        cached = get_idempotent_response(
            self.db,
            organization_id,
            "arrival_notice.submit",
            idempotency_key,
            payload,
        )
        if cached:
            return self.get(UUID(cached["resource_id"]), organization_id)
        notice = self.get(notice_id, organization_id, lock=True)
        if notice.status not in {"DRAFT", "REQUIRES_CHANGES"}:
            raise ArrivalNoticeNotEditable("El aviso no está listo para envío.")
        validation = self.validate_notice(notice.id, organization_id)
        if not validation["valid"]:
            raise ArrivalNoticeTransportIncomplete(
                "El aviso tiene errores de validación.",
                details={"errors": validation["errors"]},
            )
        revision = self.get_revision(notice.active_revision_id, organization_id, lock=True)
        self._ensure_editable_revision(revision)
        snapshot = self.snapshot_provider.build(notice, revision)
        revision.content_hash = snapshot["content_hash"]
        revision.status = "SUBMITTED"
        revision.submitted_at = utc_now()
        revision.frozen_at = utc_now()
        allocations = list(
            self.db.scalars(
                select(InboundExpectedQuantityAllocationModel)
                .join(
                    ArrivalNoticeExpectedLineModel,
                    ArrivalNoticeExpectedLineModel.id
                    == InboundExpectedQuantityAllocationModel.expected_line_id,
                )
                .where(
                    ArrivalNoticeExpectedLineModel.arrival_notice_revision_id == revision.id,
                    InboundExpectedQuantityAllocationModel.status == "HELD",
                )
                .with_for_update()
            )
        )
        for allocation in allocations:
            allocation.status = "ACTIVE"
        ensure_arrival_notice_transition(notice.status, "SUBMITTED")
        notice.status = "SUBMITTED"
        notice.submitted_at = utc_now()
        notice.submitted_by = actor_user_id
        notice.row_version += 1
        enqueue_event(
            self.db,
            organization_id=organization_id,
            aggregate_type="ARRIVAL_NOTICE",
            aggregate_id=notice.id,
            event_type="ArrivalNoticeSubmitted",
            payload={"arrival_notice_id": notice.id, "revision_id": revision.id},
            deduplication_key=f"arrival-notice-submitted:{notice.id}:{revision.id}",
        )
        self.db.flush()
        write_audit(
            self.db,
            event_code="logistics.arrival_notice.submitted",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=notice.branch_id,
            warehouse_id=notice.warehouse_id,
            resource_type="arrival_notice",
            resource_id=notice.id,
            previous_data={"status": "DRAFT"},
            new_data={"status": notice.status, "revision_id": revision.id},
        )
        save_idempotent_response(
            self.db,
            organization_id,
            actor_user_id,
            "arrival_notice.submit",
            idempotency_key,
            payload,
            {"resource_id": str(notice.id)},
        )
        return notice

    def transition(
        self,
        notice_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        target_status: str,
        *,
        reason: str | None = None,
    ) -> ArrivalNoticeModel:
        notice = self.get(notice_id, organization_id, lock=True)
        previous = notice.status
        ensure_arrival_notice_transition(previous, target_status)
        if target_status == "READY_FOR_SCHEDULING":
            validation = self.validate_notice(
                notice.id, organization_id, for_confirmation=True
            )
            if not validation["valid"]:
                raise ArrivalNoticeTransportIncomplete(
                    "El aviso no está listo para programar.",
                    details={"errors": validation["errors"]},
                )
        notice.status = target_status
        notice.updated_by = actor_user_id
        notice.row_version += 1
        event_code = {
            "UNDER_REVIEW": "logistics.arrival_notice.review_started",
            "REQUIRES_CHANGES": "logistics.arrival_notice.changes_requested",
            "READY_FOR_SCHEDULING": "logistics.arrival_notice.ready_for_scheduling",
        }.get(target_status, "logistics.arrival_notice.updated")
        if target_status == "REQUIRES_CHANGES":
            enqueue_event(
                self.db,
                organization_id=organization_id,
                aggregate_type="ARRIVAL_NOTICE",
                aggregate_id=notice.id,
                event_type="ArrivalNoticeRequiresChanges",
                payload={"arrival_notice_id": notice.id, "reason": reason},
                deduplication_key=f"arrival-notice-changes:{notice.id}:{notice.row_version}",
            )
        self.db.flush()
        write_audit(
            self.db,
            event_code=event_code,
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=notice.branch_id,
            warehouse_id=notice.warehouse_id,
            resource_type="arrival_notice",
            resource_id=notice.id,
            previous_data={"status": previous},
            new_data={"status": target_status},
            reason=reason,
        )
        return notice

    def cancel_notice(
        self,
        notice_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        reason: str,
        idempotency_key: str | None,
    ) -> ArrivalNoticeModel:
        payload = {"notice_id": notice_id, "reason": reason}
        cached = get_idempotent_response(
            self.db,
            organization_id,
            "arrival_notice.cancel",
            idempotency_key,
            payload,
        )
        if cached:
            return self.get(UUID(cached["resource_id"]), organization_id)
        notice = self.get(notice_id, organization_id, lock=True)
        if notice.status == "CANCELLED":
            return notice
        ensure_arrival_notice_transition(notice.status, "CANCELLED")
        previous = notice.status
        notice.status = "CANCELLED"
        notice.cancelled_at = utc_now()
        notice.cancelled_by = actor_user_id
        notice.cancellation_reason = reason
        notice.row_version += 1
        allocations = list(
            self.db.scalars(
                select(InboundExpectedQuantityAllocationModel)
                .where(
                    InboundExpectedQuantityAllocationModel.arrival_notice_id == notice.id,
                    InboundExpectedQuantityAllocationModel.status.in_(
                        ACTIVE_ALLOCATION_STATUSES
                    ),
                )
                .with_for_update()
            )
        )
        for allocation in allocations:
            allocation.status = "RELEASED"
            allocation.released_at = utc_now()
            allocation.release_reason = "ARRIVAL_NOTICE_CANCELLED"
        enqueue_event(
            self.db,
            organization_id=organization_id,
            aggregate_type="ARRIVAL_NOTICE",
            aggregate_id=notice.id,
            event_type="ArrivalNoticeCancelled",
            payload={"arrival_notice_id": notice.id, "reason": reason},
            deduplication_key=f"arrival-notice-cancelled:{notice.id}",
        )
        self.db.flush()
        write_audit(
            self.db,
            event_code="logistics.arrival_notice.cancelled",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=notice.branch_id,
            warehouse_id=notice.warehouse_id,
            resource_type="arrival_notice",
            resource_id=notice.id,
            previous_data={"status": previous},
            new_data={"status": notice.status},
            reason=reason,
        )
        save_idempotent_response(
            self.db,
            organization_id,
            actor_user_id,
            "arrival_notice.cancel",
            idempotency_key,
            payload,
            {"resource_id": str(notice.id)},
        )
        return notice

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def copy_notice(
        self,
        notice_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        idempotency_key: str | None,
    ) -> ArrivalNoticeModel:
        source = self.get(notice_id, organization_id)
        source_revision = self.get_revision(
            source.active_revision_id, organization_id
        )
        purchase_order_ids = list(
            self.db.scalars(
                select(ArrivalNoticePurchaseOrderReferenceModel.purchase_order_id).where(
                    ArrivalNoticePurchaseOrderReferenceModel.arrival_notice_revision_id
                    == source_revision.id,
                    ArrivalNoticePurchaseOrderReferenceModel.status == "ACTIVE",
                )
            )
        )
        copied = self.create_notice(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            session_id=None,
            correlation_id=None,
            data={
                "branch_id": source.branch_id,
                "warehouse_id": source.warehouse_id,
                "supplier_business_partner_id": source.supplier_business_partner_id,
                "carrier_business_partner_id": source.carrier_business_partner_id,
                "submission_channel": "INTERNAL",
                "external_reference": (
                    f"COPY-{source.external_reference}"
                    if source.external_reference
                    else None
                ),
                "source_type": source.source_type,
                "purchase_order_ids": purchase_order_ids,
                "expected_arrival_date": source.expected_arrival_date,
                "expected_arrival_timezone": source.expected_arrival_timezone,
                "expected_pallet_count": source.expected_pallet_count,
                "expected_package_count": source.expected_package_count,
                "expected_loose_item_count": source.expected_loose_item_count,
                "expected_gross_weight": source.expected_gross_weight,
                "weight_unit_id": source.weight_unit_id,
                "transport_mode": source.transport_mode,
                "special_requirements": list(source.special_handling_summary or []),
                "comments": source.comments,
                "idempotency_key": idempotency_key,
            },
        )
        target_revision = self.get_revision(
            copied.active_revision_id, organization_id
        )
        target_refs = {
            ref.purchase_order_id: ref
            for ref in self.db.scalars(
                select(ArrivalNoticePurchaseOrderReferenceModel).where(
                    ArrivalNoticePurchaseOrderReferenceModel.arrival_notice_revision_id
                    == target_revision.id
                )
            )
        }
        source_refs = {
            ref.id: ref
            for ref in self.db.scalars(
                select(ArrivalNoticePurchaseOrderReferenceModel).where(
                    ArrivalNoticePurchaseOrderReferenceModel.arrival_notice_revision_id
                    == source_revision.id
                )
            )
        }
        source_lines = list(
            self.db.scalars(
                select(ArrivalNoticeExpectedLineModel).where(
                    ArrivalNoticeExpectedLineModel.arrival_notice_revision_id
                    == source_revision.id,
                    ArrivalNoticeExpectedLineModel.status == "EXPECTED",
                )
            )
        )
        for line in source_lines:
            source_ref = source_refs[line.purchase_order_reference_id]
            target_ref = target_refs[source_ref.purchase_order_id]
            self.add_line(
                target_revision.id,
                organization_id,
                actor_user_id,
                {
                    "purchase_order_reference_id": target_ref.id,
                    "purchase_order_line_id": line.purchase_order_line_id,
                    "purchase_order_schedule_line_id": line.purchase_order_schedule_line_id,
                    "expected_quantity": line.expected_quantity,
                    "expected_unit_id": line.expected_unit_id,
                    "expected_package_count": line.expected_package_count,
                    "expected_pallet_count": line.expected_pallet_count,
                    "supplier_lot_reference": line.supplier_lot_reference,
                    "supplier_expiration_reference": line.supplier_expiration_reference,
                    "notes": line.notes,
                },
            )
        return copied

    def list_notices(
        self,
        organization_id: UUID,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        supplier_id: UUID | None = None,
        carrier_id: UUID | None = None,
        warehouse_id: UUID | None = None,
        branch_id: UUID | None = None,
        status: str | None = None,
        appointment_status: str | None = None,
        expected_from: date | None = None,
        expected_to: date | None = None,
        submission_channel: str | None = None,
        created_by: UUID | None = None,
        sort_by: str = "updated_at",
        sort_direction: str = "desc",
    ) -> tuple[list[ArrivalNoticeModel], int]:
        filters = [ArrivalNoticeModel.organization_id == organization_id]
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    ArrivalNoticeModel.external_reference.ilike(pattern),
                    ArrivalNoticeModel.comments.ilike(pattern),
                )
            )
        if supplier_id:
            filters.append(
                ArrivalNoticeModel.supplier_business_partner_id == supplier_id
            )
        if carrier_id:
            filters.append(
                ArrivalNoticeModel.carrier_business_partner_id == carrier_id
            )
        if warehouse_id:
            filters.append(ArrivalNoticeModel.warehouse_id == warehouse_id)
        if branch_id:
            filters.append(ArrivalNoticeModel.branch_id == branch_id)
        if status:
            filters.append(ArrivalNoticeModel.status == status)
        if appointment_status:
            filters.append(ArrivalNoticeModel.appointment_status == appointment_status)
        if expected_from:
            filters.append(ArrivalNoticeModel.expected_arrival_date >= expected_from)
        if expected_to:
            filters.append(ArrivalNoticeModel.expected_arrival_date <= expected_to)
        if submission_channel:
            filters.append(
                ArrivalNoticeModel.submission_channel == submission_channel
            )
        if created_by:
            filters.append(ArrivalNoticeModel.created_by == created_by)
        total = self.db.scalar(
            select(func.count()).select_from(ArrivalNoticeModel).where(*filters)
        )
        sort_columns = {
            "updated_at": ArrivalNoticeModel.updated_at,
            "created_at": ArrivalNoticeModel.created_at,
            "expected_arrival_date": ArrivalNoticeModel.expected_arrival_date,
            "status": ArrivalNoticeModel.status,
        }
        sort_column = sort_columns.get(sort_by, ArrivalNoticeModel.updated_at)
        ordering = sort_column.asc() if sort_direction.lower() == "asc" else sort_column.desc()
        items = list(
            self.db.scalars(
                select(ArrivalNoticeModel)
                .where(*filters)
                .order_by(ordering)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, int(total or 0)

    def source_order_codes(self, revision_id: UUID) -> list[str]:
        return list(
            self.db.scalars(
                select(ArrivalNoticePurchaseOrderReferenceModel.purchase_order_code)
                .where(
                    ArrivalNoticePurchaseOrderReferenceModel.arrival_notice_revision_id
                    == revision_id,
                    ArrivalNoticePurchaseOrderReferenceModel.status == "ACTIVE",
                )
                .order_by(ArrivalNoticePurchaseOrderReferenceModel.purchase_order_code)
            )
        )

    def capabilities(self, notice: ArrivalNoticeModel) -> list[str]:
        capabilities = ["read", "read_history"]
        if notice.status in {"DRAFT", "REQUIRES_CHANGES"}:
            capabilities.extend(["update", "submit", "cancel"])
        if notice.status == "SUBMITTED":
            capabilities.extend(["mark_under_review", "request_changes", "mark_ready", "cancel"])
        if notice.status == "UNDER_REVIEW":
            capabilities.extend(["request_changes", "mark_ready", "cancel"])
        if notice.status == "READY_FOR_SCHEDULING":
            capabilities.extend(["create_hold", "create_appointment", "cancel"])
        if notice.status in {"SCHEDULED", "CONFIRMED"}:
            capabilities.extend(["reschedule", "cancel", "download_cit"])
        return list(dict.fromkeys(capabilities))
