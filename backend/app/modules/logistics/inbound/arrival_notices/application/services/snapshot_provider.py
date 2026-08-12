"""Immutable Phase 036 snapshot builder.

Only captured snapshots and Phase 036 rows are used.  Reprints therefore do not
depend on mutable supplier, vehicle, driver or purchase-order master data.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.arrival_notices.application.services.common import (
    content_hash,
    json_safe,
    utc_now,
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
from app.modules.logistics.inbound.reception_calendar.infrastructure.persistence.models import (
    ReceptionAppointmentModel,
    WarehouseReceptionCalendarModel,
)


class ArrivalNoticeSnapshotProvider:
    def __init__(self, db: Session):
        self.db = db

    def build(
        self,
        notice: ArrivalNoticeModel,
        revision: ArrivalNoticeRevisionModel,
        appointment: ReceptionAppointmentModel | None = None,
    ) -> dict:
        po_refs = list(
            self.db.scalars(
                select(ArrivalNoticePurchaseOrderReferenceModel)
                .where(
                    ArrivalNoticePurchaseOrderReferenceModel.arrival_notice_revision_id
                    == revision.id
                )
                .order_by(ArrivalNoticePurchaseOrderReferenceModel.purchase_order_code)
            )
        )
        lines = list(
            self.db.scalars(
                select(ArrivalNoticeExpectedLineModel)
                .where(ArrivalNoticeExpectedLineModel.arrival_notice_revision_id == revision.id)
                .order_by(ArrivalNoticeExpectedLineModel.line_number)
            )
        )
        line_ids = [line.id for line in lines]
        allocations = (
            list(
                self.db.scalars(
                    select(InboundExpectedQuantityAllocationModel).where(
                        InboundExpectedQuantityAllocationModel.expected_line_id.in_(line_ids)
                    )
                )
            )
            if line_ids
            else []
        )
        vehicle = self.db.scalar(
            select(ArrivalNoticeVehicleReferenceModel).where(
                ArrivalNoticeVehicleReferenceModel.revision_id == revision.id
            )
        )
        driver = self.db.scalar(
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
        calendar = (
            self.db.get(WarehouseReceptionCalendarModel, appointment.calendar_id)
            if appointment
            else None
        )
        payload = {
            "schema_version": "phase-036.1",
            "arrival_notice": {
                "id": notice.id,
                "organization_id": notice.organization_id,
                "branch_id": notice.branch_id,
                "warehouse_id": notice.warehouse_id,
                "status": notice.status,
                "appointment_status": notice.appointment_status,
                "expected_arrival_date": notice.expected_arrival_date,
                "expected_arrival_timezone": notice.expected_arrival_timezone,
                "expected_pallet_count": notice.expected_pallet_count,
                "expected_package_count": notice.expected_package_count,
                "expected_loose_item_count": notice.expected_loose_item_count,
                "expected_gross_weight": notice.expected_gross_weight,
                "weight_unit_id": notice.weight_unit_id,
                "transport_mode": notice.transport_mode,
                "special_requirements": notice.special_handling_summary,
                "comments": notice.comments,
            },
            "revision": {
                "id": revision.id,
                "revision_number": revision.revision_number,
                "supplier": revision.supplier_snapshot,
                "carrier": revision.carrier_snapshot,
                "warehouse": revision.warehouse_snapshot,
                "transport": revision.transport_snapshot,
                "special_requirements": revision.special_requirements,
                "comments": revision.comments,
            },
            "purchase_orders": [
                {
                    "id": ref.purchase_order_id,
                    "revision_id": ref.purchase_order_revision_id,
                    "code": ref.purchase_order_code,
                    "currency_code": ref.currency_code,
                    "source_snapshot_hash": ref.source_snapshot_hash,
                }
                for ref in po_refs
            ],
            "expected_lines": [
                {
                    "id": line.id,
                    "purchase_order_line_id": line.purchase_order_line_id,
                    "line_number": line.line_number,
                    "product_id": line.product_id,
                    "product_version_id": line.product_version_id,
                    "sku": line.sku_snapshot,
                    "product_name": line.product_name_snapshot,
                    "expected_quantity": line.expected_quantity,
                    "expected_unit_id": line.expected_unit_id,
                    "expected_base_quantity": line.expected_base_quantity,
                    "base_unit_id": line.base_unit_id,
                    "expected_package_count": line.expected_package_count,
                    "expected_pallet_count": line.expected_pallet_count,
                    "supplier_lot_reference": line.supplier_lot_reference,
                    "supplier_expiration_reference": line.supplier_expiration_reference,
                }
                for line in lines
            ],
            "allocations": [
                {
                    "id": allocation.id,
                    "purchase_order_line_id": allocation.purchase_order_line_id,
                    "allocated_quantity": allocation.allocated_quantity,
                    "allocated_unit_id": allocation.allocated_unit_id,
                    "allocated_base_quantity": allocation.allocated_base_quantity,
                    "status": allocation.status,
                }
                for allocation in allocations
            ],
            "vehicle": (
                {
                    "vehicle_id": vehicle.vehicle_id,
                    "plate": vehicle.plate_snapshot,
                    "normalized_plate": vehicle.normalized_plate,
                    "snapshot": vehicle.vehicle_snapshot,
                    "verification_summary": vehicle.verification_summary,
                    "verification_expiration": vehicle.verification_expiration,
                    "source_type": vehicle.source_type,
                }
                if vehicle
                else None
            ),
            "driver": (
                {
                    "driver_id": driver.driver_id,
                    "full_name": driver.full_name_snapshot,
                    "document_number_redacted": driver.document_number_redacted_snapshot,
                    "license_number_redacted": driver.license_number_redacted_snapshot,
                    "license_category": driver.license_category_snapshot,
                    "license_expiration": driver.license_expiration_snapshot,
                    "source_type": driver.source_type,
                }
                if driver
                else None
            ),
            "transport_documents": [
                {
                    "id": document.id,
                    "kind": document.document_kind,
                    "series": document.series,
                    "number": document.number,
                    "normalized_reference": document.normalized_reference,
                    "verification_status": document.verification_status,
                    "file_asset_id": document.file_asset_id,
                }
                for document in documents
            ],
            "appointment": (
                {
                    "id": appointment.id,
                    "appointment_code": appointment.appointment_code,
                    "status": appointment.status,
                    "slot_start": appointment.slot_start,
                    "slot_end": appointment.slot_end,
                    "timezone": appointment.timezone,
                    "confirmed_at": appointment.confirmed_at,
                    "confirmed_by": appointment.confirmed_by,
                }
                if appointment
                else None
            ),
            "calendar": (
                {
                    "id": calendar.id,
                    "name": calendar.name,
                    "timezone": calendar.timezone,
                    "slot_duration_minutes": calendar.slot_duration_minutes,
                }
                if calendar
                else None
            ),
            "captured_at": utc_now().isoformat(),
        }
        safe = json_safe(payload)
        safe["content_hash"] = content_hash(safe)
        return safe


snapshot_provider_class = ArrivalNoticeSnapshotProvider
