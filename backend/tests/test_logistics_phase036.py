"""Phase 036 regression tests for inbound notices and reception scheduling."""

from __future__ import annotations

from datetime import date, time, timedelta
from decimal import Decimal
from time import perf_counter
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select

from app.main import app
from app.models.branch import Branch
from app.models.organization import Organization
from app.models.user import User
from app.models.warehouse import Warehouse
from app.modules.logistics.inbound.arrival_notices.domain.errors.exceptions import (
    ArrivalNoticeNotFound,
    ArrivalNoticeQuantityExceeded,
    ArrivalNoticeStatusInvalid,
    IdempotencyConflict,
)
from app.modules.logistics.inbound.arrival_notices.domain.policies.state_machine import (
    ensure_arrival_notice_transition,
)
from app.modules.logistics.inbound.arrival_notices.application.services.arrival_notice_service import (
    ArrivalNoticeService,
)
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeExpectedLineModel,
    ArrivalNoticeModel,
    ArrivalNoticePurchaseOrderReferenceModel,
    ArrivalNoticeRevisionModel,
    InboundExpectedQuantityAllocationModel,
)
from app.modules.logistics.inbound.arrival_notices.presentation.schemas.schemas import (
    ArrivalNoticeCreate,
    ArrivalNoticeExpectedLineCreate,
)
from app.modules.logistics.inbound.reception_calendar.application.services.calendar_service import (
    ReceptionCalendarService,
)
from app.modules.logistics.inbound.reception_calendar.application.services.appointment_service import (
    ReceptionAppointmentService,
)
from app.modules.logistics.inbound.reception_calendar.infrastructure.persistence.models import (
    ReceptionAppointmentHoldModel,
    ReceptionAppointmentModel,
    WarehouseReceptionCalendarModel,
)
from app.modules.logistics.inbound.reception_calendar.presentation.schemas.schemas import (
    ReceptionAvailabilityRequest,
    ReceptionCalendarCreate,
    ReceptionOperatingWindowCreate,
)
from app.modules.logistics.inbound.arrival_notices.infrastructure.jobs.run_phase036_jobs import (
    JOBS as PHASE_036_JOBS,
)
from app.modules.logistics.partners.models import (
    BusinessPartnerModel,
    BusinessPartnerRoleModel,
)
from app.modules.logistics.procurement.purchase_orders.infrastructure.persistence.models import (
    PurchaseOrderLineModel,
    PurchaseOrderModel,
    PurchaseOrderRevisionModel,
)
from app.modules.logistics.rbac.permission_catalog import (
    PERMISSIONS,
    ROLE_PERMISSION_MATRIX,
)
from app.modules.logistics.units.models import (
    MeasurementDimensionModel,
    UnitOfMeasureModel,
)


def test_decimal_contract_rejects_float_nan_and_infinity():
    common = {
        "purchase_order_reference_id": uuid4(),
        "purchase_order_line_id": uuid4(),
        "expected_unit_id": uuid4(),
    }
    with pytest.raises(ValidationError):
        ArrivalNoticeExpectedLineCreate(expected_quantity=1.25, **common)
    with pytest.raises(ValidationError):
        ArrivalNoticeExpectedLineCreate(expected_quantity="NaN", **common)
    with pytest.raises(ValidationError):
        ArrivalNoticeExpectedLineCreate(expected_quantity="Infinity", **common)
    accepted = ArrivalNoticeExpectedLineCreate(
        expected_quantity="1.2500000000", **common
    )
    assert accepted.expected_quantity == Decimal("1.2500000000")


def test_arrival_notice_state_machine_blocks_invalid_shortcuts():
    ensure_arrival_notice_transition("DRAFT", "SUBMITTED")
    with pytest.raises(ArrivalNoticeStatusInvalid):
        ensure_arrival_notice_transition("DRAFT", "CONFIRMED")
    with pytest.raises(ArrivalNoticeStatusInvalid):
        ensure_arrival_notice_transition("CANCELLED", "DRAFT")


def test_phase036_models_registered_with_allocation_uniqueness():
    assert ArrivalNoticeModel.__tablename__ == "arrival_notices"
    assert ArrivalNoticeRevisionModel.__tablename__ == "arrival_notice_revisions"
    assert ArrivalNoticeExpectedLineModel.__tablename__ == "arrival_notice_expected_lines"
    assert (
        InboundExpectedQuantityAllocationModel.__tablename__
        == "inbound_expected_quantity_allocations"
    )
    constraints = {
        constraint.name
        for constraint in InboundExpectedQuantityAllocationModel.__table__.constraints
    }
    assert "uq_inbound_allocation_expected_line" in constraints


def test_phase036_permissions_include_step_up_and_role_grants():
    catalog = {item["code"]: item for item in PERMISSIONS}
    assert catalog["logistics.arrival_notices.submit"]["requires_step_up"] is True
    assert (
        catalog["logistics.reception_appointments.confirm"]["requires_step_up"]
        is True
    )
    assert (
        catalog["logistics.reception_calendars.override_capacity"]["risk_level"]
        == "critical"
    )
    assert "logistics.arrival_notices.read" in ROLE_PERMISSION_MATRIX[
        "LOGISTICS_AUDITOR"
    ]
    assert "logistics.reception_appointments.confirm" in ROLE_PERMISSION_MATRIX[
        "RECEIVING"
    ]


def test_openapi_exposes_phase036_without_physical_reception_routes():
    paths = app.openapi()["paths"]
    required = {
        "/api/logistics/arrival-notices",
        "/api/logistics/reception-calendars/{calendar_id}/availability",
        "/api/logistics/reception-appointment-holds",
        "/api/logistics/reception-appointments/{appointment_id}/confirm",
        "/api/logistics/reception-appointments/{appointment_id}/issue",
    }
    assert required.issubset(paths)
    phase_paths = {
        path
        for path in paths
        if "arrival-notice" in path or "reception-appointment" in path
    }
    assert all("/check-in" not in path for path in phase_paths)
    assert all("/unloading" not in path for path in phase_paths)
    assert all("/dock" not in path for path in phase_paths)


def test_phase036_endpoint_rejects_unauthenticated_access():
    response = TestClient(app).get("/api/logistics/arrival-notices")
    assert response.status_code == 401


def test_calendar_availability_uses_windows_and_exact_decimal_capacity(database):
    actor_id = uuid4()
    organization = Organization(
        id=uuid4(),
        code=f"P36-{uuid4().hex[:8]}",
        name="Organización Fase 036",
        country_code="PE",
    )
    actor = User(
        id=actor_id,
        email=f"phase036-{uuid4().hex[:8]}@example.com",
        password_hash="not-used",
        full_name="Planificador de recepción",
        role="admin",
        is_active=True,
    )
    branch = Branch(
        id=uuid4(),
        organization_id=organization.id,
        code=f"B-{uuid4().hex[:6]}",
        name="Sede de prueba",
        timezone="UTC",
    )
    warehouse = Warehouse(
        id=uuid4(),
        organization_id=organization.id,
        branch_id=branch.id,
        code=f"W-{uuid4().hex[:6]}",
        name="Almacén de recepción",
        receiving_enabled=True,
        is_active=True,
    )
    dimension = MeasurementDimensionModel(
        id=uuid4(), code=f"MASS-{uuid4().hex[:6]}", name="Masa"
    )
    kilogram = UnitOfMeasureModel(
        id=uuid4(),
        organization_id=organization.id,
        dimension_id=dimension.id,
        code="KG",
        normalized_code=f"KG-{uuid4().hex[:6]}",
        name="Kilogramo",
        symbol="kg",
        is_canonical=True,
    )
    database.add_all(
        [organization, actor, branch, warehouse, dimension, kilogram]
    )
    database.flush()

    service = ReceptionCalendarService(database)
    calendar = service.create(
        organization.id,
        actor.id,
        ReceptionCalendarCreate(
            warehouse_id=warehouse.id,
            name="Calendario principal",
            timezone="UTC",
            minimum_advance_minutes=0,
            maximum_advance_days=30,
            default_max_concurrent_appointments=2,
            default_max_weight_per_slot="1000.0000000000",
            weight_unit_id=kilogram.id,
        ),
    )
    target_day = date.today() + timedelta(days=2)
    service.add_window(
        calendar.id,
        organization.id,
        actor.id,
        ReceptionOperatingWindowCreate(
            day_of_week=target_day.weekday(),
            start_local_time=time(9, 0),
            end_local_time=time(11, 0),
            effective_from=target_day,
        ),
    )
    service.transition(calendar.id, organization.id, actor.id, "ACTIVE")
    started_at = perf_counter()
    slots, version = service.availability(
        calendar.id,
        organization.id,
        ReceptionAvailabilityRequest(
            starts_on=target_day,
            ends_on=target_day,
            timezone="UTC",
            expected_pallet_count=1,
            expected_package_count=10,
            expected_weight="250.1250000000",
            weight_unit_id=kilogram.id,
        ),
    )
    elapsed = perf_counter() - started_at
    assert len(slots) == 2
    assert all(slot["availability_status"] == "AVAILABLE" for slot in slots)
    assert all(
        slot["remaining_weight_capacity"] == Decimal("1000.0000000000")
        for slot in slots
    )
    assert len(version) == 64
    assert elapsed < 2.0


def test_phase036_has_no_physical_inventory_models():
    forbidden = {
        "arrival_records",
        "gate_check_ins",
        "dock_assignments",
        "unloading_operations",
        "physical_pallets",
        "inventory_receipts",
    }
    phase_tables = {
        ArrivalNoticeModel.__tablename__,
        ReceptionAppointmentHoldModel.__tablename__,
        ReceptionAppointmentModel.__tablename__,
        WarehouseReceptionCalendarModel.__tablename__,
    }
    assert forbidden.isdisjoint(phase_tables)


def test_arrival_notice_allocates_issued_po_and_freezes_on_submit(database):
    organization = Organization(
        id=uuid4(),
        code=f"P36-FLOW-{uuid4().hex[:6]}",
        name="Organización flujo Fase 036",
        country_code="PE",
    )
    actor = User(
        id=uuid4(),
        email=f"phase036-flow-{uuid4().hex[:8]}@example.com",
        password_hash="not-used",
        full_name="Planificador de inbound",
        role="admin",
        is_active=True,
    )
    branch = Branch(
        id=uuid4(),
        organization_id=organization.id,
        code=f"BF-{uuid4().hex[:6]}",
        name="Sede inbound",
        timezone="UTC",
    )
    warehouse = Warehouse(
        id=uuid4(),
        organization_id=organization.id,
        branch_id=branch.id,
        code=f"WF-{uuid4().hex[:6]}",
        name="Almacén inbound",
        receiving_enabled=True,
        is_active=True,
    )
    unit_id = uuid4()
    dimension = MeasurementDimensionModel(
        id=uuid4(),
        code="MASS",
        name="Masa flujo",
    )
    kilogram = UnitOfMeasureModel(
        id=unit_id,
        organization_id=organization.id,
        dimension_id=dimension.id,
        code=f"KGF-{uuid4().hex[:4]}",
        normalized_code=f"KGF-{uuid4().hex[:8]}",
        name="Kilogramo flujo",
        symbol="kg",
        is_canonical=True,
    )
    supplier = BusinessPartnerModel(
        id=uuid4(),
        organization_id=organization.id,
        partner_code=f"SUP-{uuid4().hex[:6]}",
        normalized_partner_code=f"SUP-{uuid4().hex[:8]}",
        legal_name="Proveedor Fase 036",
        person_type="LEGAL_ENTITY",
        country_code="PE",
        status="ACTIVE",
        lifecycle_status="ACTIVE",
    )
    supplier_role = BusinessPartnerRoleModel(
        id=uuid4(),
        business_partner_id=supplier.id,
        role_type="SUPPLIER",
        status="ACTIVE",
    )
    order = PurchaseOrderModel(
        id=uuid4(),
        organization_id=organization.id,
        branch_id=branch.id,
        purchase_order_code=f"OC-{uuid4().hex[:8]}",
        normalized_purchase_order_code=f"OC-{uuid4().hex[:8]}",
        supplier_business_partner_id=supplier.id,
        supplier_role_id=supplier_role.id,
        source_decision_id=uuid4(),
        currency_code="PEN",
        status="ISSUED",
        approval_status="APPROVED",
        issuance_status="ISSUED",
        destination_warehouse_id=warehouse.id,
        buyer_user_id=actor.id,
        created_by=actor.id,
    )
    order_revision = PurchaseOrderRevisionModel(
        id=uuid4(),
        purchase_order_id=order.id,
        revision_number=1,
        status="FROZEN",
        currency_code="PEN",
        content_hash="a" * 64,
        created_by=actor.id,
    )
    order_line = PurchaseOrderLineModel(
        id=uuid4(),
        purchase_order_revision_id=order_revision.id,
        line_number=1,
        product_name_snapshot="Producto de prueba",
        ordered_quantity=Decimal("100.0000000000"),
        ordered_unit_id=kilogram.id,
        ordered_unit_code=kilogram.code,
        base_quantity=Decimal("100.0000000000"),
        base_unit_id=kilogram.id,
        base_unit_code=kilogram.code,
        unit_price=Decimal("10.000000"),
        currency_code="PEN",
        discount_amount=Decimal("0"),
        tax_amount=Decimal("0"),
        freight_amount=Decimal("0"),
        other_charges_amount=Decimal("0"),
        line_subtotal=Decimal("1000"),
        line_total=Decimal("1000"),
        destination_warehouse_id=warehouse.id,
        status="ACTIVE",
    )
    order.active_revision_id = order_revision.id
    order.approved_revision_id = order_revision.id
    order.issued_revision_id = order_revision.id
    database.add_all(
        [
            organization,
            actor,
            branch,
            warehouse,
            dimension,
            kilogram,
            supplier,
            supplier_role,
            order,
            order_revision,
            order_line,
        ]
    )
    database.flush()
    dimension.canonical_unit_id = kilogram.id
    database.flush()

    service = ArrivalNoticeService(database)
    notice_payload = ArrivalNoticeCreate(
        branch_id=branch.id,
        warehouse_id=warehouse.id,
        supplier_business_partner_id=supplier.id,
        purchase_order_ids=[order.id],
        expected_arrival_date=date.today() + timedelta(days=3),
        expected_arrival_timezone="UTC",
        expected_package_count=10,
        expected_gross_weight="60.0000000000",
        weight_unit_id=kilogram.id,
        idempotency_key=f"notice-{uuid4()}",
    ).model_dump()
    notice = service.create_notice(
        organization_id=organization.id,
        actor_user_id=actor.id,
        session_id=None,
        correlation_id="phase036-flow",
        data=notice_payload,
    )
    replayed = service.create_notice(
        organization_id=organization.id,
        actor_user_id=actor.id,
        session_id=None,
        correlation_id="phase036-flow-replay",
        data=notice_payload,
    )
    assert replayed.id == notice.id
    with pytest.raises(IdempotencyConflict):
        service.create_notice(
            organization_id=organization.id,
            actor_user_id=actor.id,
            session_id=None,
            correlation_id="phase036-flow-conflict",
            data={**notice_payload, "comments": "Payload distinto"},
        )
    reference = database.scalar(
        select(ArrivalNoticePurchaseOrderReferenceModel).where(
            ArrivalNoticePurchaseOrderReferenceModel.arrival_notice_revision_id
            == notice.active_revision_id
        )
    )
    assert reference is not None

    line_payload = ArrivalNoticeExpectedLineCreate(
        purchase_order_reference_id=reference.id,
        purchase_order_line_id=order_line.id,
        expected_quantity="60.0000000000",
        expected_unit_id=kilogram.id,
        expected_package_count=10,
        idempotency_key=f"line-{uuid4()}",
    ).model_dump()
    line = service.add_line(
        notice.active_revision_id,
        organization.id,
        actor.id,
        line_payload,
    )
    allocation = database.scalar(
        select(InboundExpectedQuantityAllocationModel).where(
            InboundExpectedQuantityAllocationModel.expected_line_id == line.id
        )
    )
    assert allocation is not None
    assert allocation.status == "HELD"
    assert allocation.allocated_base_quantity == Decimal("60.0000000000")

    with pytest.raises(ArrivalNoticeQuantityExceeded):
        service.add_line(
            notice.active_revision_id,
            organization.id,
            actor.id,
            ArrivalNoticeExpectedLineCreate(
                purchase_order_reference_id=reference.id,
                purchase_order_line_id=order_line.id,
                expected_quantity="41.0000000000",
                expected_unit_id=kilogram.id,
                idempotency_key=f"line-{uuid4()}",
            ).model_dump(),
        )

    submitted = service.submit(
        notice.id,
        organization.id,
        actor.id,
        f"submit-{uuid4()}",
    )
    database.refresh(allocation)
    revision = database.get(ArrivalNoticeRevisionModel, notice.active_revision_id)
    assert submitted.status == "SUBMITTED"
    assert revision is not None
    assert revision.status == "SUBMITTED"
    assert len(revision.content_hash) == 64
    assert allocation.status == "ACTIVE"
    with pytest.raises(ArrivalNoticeNotFound):
        service.get(notice.id, uuid4())


def test_appointment_detects_vehicle_and_driver_overlap():
    appointment_id = uuid4()
    other_id = uuid4()
    organization_id = uuid4()
    driver_id = uuid4()
    appointment = SimpleNamespace(
        id=appointment_id,
        organization_id=organization_id,
        slot_start=date.today(),
        slot_end=date.today() + timedelta(days=1),
        vehicle_reference_snapshot={"plate": "ABC-123"},
        driver_reference_snapshot={"driver_id": str(driver_id)},
    )
    other = SimpleNamespace(
        id=other_id,
        vehicle_reference_snapshot={"normalized_plate": "ABC123"},
        driver_reference_snapshot={"driver_id": str(driver_id)},
    )
    database = MagicMock()
    database.scalars.return_value = [other]
    service = ReceptionAppointmentService.__new__(ReceptionAppointmentService)
    service.db = database

    conflicts = service._transport_overlap_conflicts(appointment)
    assert {item["code"] for item in conflicts} == {
        "VEHICLE_SLOT_OVERLAP",
        "DRIVER_SLOT_OVERLAP",
    }
    assert all(item["conflicting_appointment_id"] == str(other_id) for item in conflicts)


def test_phase036_scheduler_exposes_all_persistent_jobs():
    assert {
        "expire-holds",
        "reminders-24h",
        "reminders-2h",
        "mark-elapsed",
        "pending-documents",
        "driver-license-expirations",
        "vehicle-verification-expirations",
        "blackout-affected",
        "retry-outbox",
        "publish-outbox",
        "cleanup-external-sessions",
        "reconcile-allocations",
        "appointment-packages",
    }.issubset(PHASE_036_JOBS)
