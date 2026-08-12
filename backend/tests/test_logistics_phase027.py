"""Comprehensive Pytest Suite for Phase 027 — Master Vehicles Management."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.database.base import utc_now
from app.models.organization import Organization
from app.models.user import User
from app.modules.logistics.partners.models import BusinessPartnerModel, BusinessPartnerRoleModel
from app.modules.logistics.units.models import MeasurementDimensionModel, UnitOfMeasureModel
from app.modules.logistics.vehicles.application.services.capacity_service import VehicleCapacityService
from app.modules.logistics.vehicles.application.services.document_service import VehicleDocumentService
from app.modules.logistics.vehicles.application.services.make_model_service import VehicleMakeModelService
from app.modules.logistics.vehicles.application.services.ownership_carrier_service import VehicleOwnershipCarrierService
from app.modules.logistics.vehicles.application.services.vehicle_service import VehicleService
from app.modules.logistics.vehicles.domain.errors.exceptions import (
    VehicleCapacityInvalidError,
    VehicleCarrierBlockedError,
    VehicleCarrierRoleRequiredError,
    VehiclePlateConflictError,
    VehiclePlateInvalidError,
    VehicleVinInvalidError,
)
from app.modules.logistics.vehicles.domain.services.services import (
    VehicleOperationalStatusResolver,
    VehiclePlateService,
    VehicleSnapshotProvider,
    VehicleVinService,
)
from app.modules.logistics.vehicles.domain.value_objects.enums import (
    BodyType,
    VehicleComplianceStatus,
    VehicleLifecycleStatus,
    VehicleOperationalStatus,
    VehicleType,
)
from app.modules.logistics.vehicles.infrastructure.persistence.models import (
    VehicleAliasModel,
    VehicleMakeModel,
    VehicleModel,
    VehicleModelModel,
    VehicleVersionModel,
)


@pytest.fixture
def test_org(database):
    org = Organization(
        id=uuid4(),
        code=f"ORG-{uuid4().hex[:6].upper()}",
        name="Org Test Vehicles",
        country_code="PE",
        status="active",
    )
    database.add(org)
    database.commit()
    database.refresh(org)
    return org


@pytest.fixture
def test_uoms(database):
    dim_mass = database.scalars(select(MeasurementDimensionModel).where(MeasurementDimensionModel.code == "MASS")).first()
    if not dim_mass:
        dim_mass = MeasurementDimensionModel(id=uuid4(), code="MASS", name="Masa")
        database.add(dim_mass)

    u_kg = database.scalars(select(UnitOfMeasureModel).where(UnitOfMeasureModel.code == "KG")).first()
    if not u_kg:
        u_kg = UnitOfMeasureModel(id=uuid4(), dimension_id=dim_mass.id, code="KG", normalized_code="KG", name="Kilogramo", symbol="kg", unit_kind="BASE", status="ACTIVE")
        database.add(u_kg)

    database.commit()
    return {"KG": u_kg}


@pytest.fixture
def test_actor(database):
    actor = User(
        id=uuid4(),
        email=f"vehicle-actor-{uuid4().hex[:8]}@example.com",
        password_hash="not-used-in-this-test",
        full_name="Operador de vehículos",
        role="admin",
        is_active=True,
    )
    database.add(actor)
    database.commit()
    return actor


@pytest.fixture
def test_make_model(database, test_org):
    service = VehicleMakeModelService(database)
    make = service.create_make(organization_id=test_org.id, name="VOLVO", code="VOLVO")
    mod = service.create_model(make_id=make.id, organization_id=test_org.id, name="FH540", code="FH540")
    return make, mod


@pytest.fixture
def test_carrier_partner(database, test_org):
    partner_code = f"BP-{uuid4().hex[:6].upper()}"
    partner = BusinessPartnerModel(
        id=uuid4(),
        organization_id=test_org.id,
        partner_code=partner_code,
        normalized_partner_code=partner_code,
        legal_name="Transportes El Rapido S.A.C.",
        trade_name="El Rapido",
        person_type="LEGAL_ENTITY",
        country_code="PE",
        status="ACTIVE",
    )
    database.add(partner)
    database.commit()

    role = BusinessPartnerRoleModel(
        id=uuid4(),
        business_partner_id=partner.id,
        role_type="CARRIER",
        status="ACTIVE",
    )
    database.add(role)
    database.commit()
    return partner, role


def test_vehicle_plate_and_vin_formatting():
    assert VehiclePlateService.normalize("  abc-123  ") == "ABC123"
    assert VehiclePlateService.format_display("abc123") == "ABC-123"
    assert VehiclePlateService.validate_format("F1A-987") is True
    assert VehiclePlateService.validate_format("X") is False

    assert VehicleVinService.normalize("  1HGCR2F83HA000000  ") == "1HGCR2F83HA000000"
    assert VehicleVinService.mask_vin("1HGCR2F83HA000000") == "***0000"
    assert VehicleVinService.mask_vin(None) is None


def test_vehicle_operational_status_resolver():
    # 1. Retired Vehicle
    op, comp, _ = VehicleOperationalStatusResolver.resolve(
        lifecycle_status=VehicleLifecycleStatus.RETIRED.value,
        is_blocked=False,
        is_maintenance=False,
        has_active_carrier=True,
        has_expired_required_docs=False,
        has_missing_required_docs=False,
    )
    assert op == VehicleOperationalStatus.RETIRED
    assert comp == VehicleComplianceStatus.NON_COMPLIANT

    # 2. Blocked Vehicle
    op, comp, _ = VehicleOperationalStatusResolver.resolve(
        lifecycle_status=VehicleLifecycleStatus.ACTIVE.value,
        is_blocked=True,
        is_maintenance=False,
        has_active_carrier=True,
        has_expired_required_docs=False,
        has_missing_required_docs=False,
    )
    assert op == VehicleOperationalStatus.BLOCKED

    # 3. Documents Expired Vehicle
    op, comp, _ = VehicleOperationalStatusResolver.resolve(
        lifecycle_status=VehicleLifecycleStatus.ACTIVE.value,
        is_blocked=False,
        is_maintenance=False,
        has_active_carrier=True,
        has_expired_required_docs=True,
        has_missing_required_docs=False,
    )
    assert op == VehicleOperationalStatus.DOCUMENTS_EXPIRED
    assert comp == VehicleComplianceStatus.EXPIRED_DOCUMENTS

    # 4. Fully Available Vehicle
    op, comp, _ = VehicleOperationalStatusResolver.resolve(
        lifecycle_status=VehicleLifecycleStatus.ACTIVE.value,
        is_blocked=False,
        is_maintenance=False,
        has_active_carrier=True,
        has_expired_required_docs=False,
        has_missing_required_docs=False,
    )
    assert op == VehicleOperationalStatus.AVAILABLE
    assert comp == VehicleComplianceStatus.COMPLIANT


def test_snapshot_provider_hash_calculation():
    payload1 = VehicleSnapshotProvider.build_snapshot_payload(
        vehicle_code="VEH-000001",
        plate="ABC-123",
        vin="1HGCR2F83HA000000",
        make_name="VOLVO",
        model_name="FH540",
        vehicle_type="HEAVY_TRUCK",
        body_type="CLOSED_BOX",
        capacity_dict={"max_payload": 20000},
        dimensions_dict={},
        owner_dict={},
        carrier_dict={},
    )
    hash1 = VehicleSnapshotProvider.calculate_content_hash(payload1)
    hash2 = VehicleSnapshotProvider.calculate_content_hash(payload1)

    assert hash1 == hash2
    assert len(hash1) == 64
    assert payload1["masked_vin"] == "***0000"


def test_create_make_and_model(database, test_org):
    service = VehicleMakeModelService(database)
    make = service.create_make(test_org.id, "SCANIA", "SCANIA")
    assert make.normalized_name == "SCANIA"

    mod = service.create_model(make.id, test_org.id, "R500", "R500")
    assert mod.make_id == make.id
    assert mod.name == "R500"


def test_vehicle_crud_lifecycle(database, test_org, test_make_model, test_actor):
    make, model = test_make_model
    actor_id = test_actor.id
    v_service = VehicleService(database)

    # 1. Create DRAFT Vehicle
    v = v_service.create_vehicle(
        organization_id=test_org.id,
        display_plate="ABC-123",
        make_id=make.id,
        model_id=model.id,
        actor_id=actor_id,
        vin="1HGCR2F83HA000001",
    )

    assert v.vehicle_code.startswith("VEH-")
    assert v.display_plate == "ABC-123"
    assert v.normalized_plate == "ABC123"
    assert v.lifecycle_status == VehicleLifecycleStatus.DRAFT.value
    assert v.operational_status == VehicleOperationalStatus.UNAVAILABLE.value

    # 2. Activate Vehicle
    v_act = v_service.activate_vehicle(v.id, test_org.id, actor_id)
    assert v_act.lifecycle_status == VehicleLifecycleStatus.ACTIVE.value

    # 3. Block Vehicle
    v_blk = v_service.block_vehicle(v.id, test_org.id, "Revisión técnica observada", actor_id)
    assert v_blk.operational_status == VehicleOperationalStatus.BLOCKED.value

    # 4. Unblock Vehicle
    v_ublk = v_service.unblock_vehicle(v.id, test_org.id, actor_id)
    assert v_ublk.operational_status != VehicleOperationalStatus.BLOCKED.value


def test_duplicate_plate_rejection(database, test_org, test_make_model, test_actor):
    make, model = test_make_model
    actor_id = test_actor.id
    v_service = VehicleService(database)

    v_service.create_vehicle(
        organization_id=test_org.id,
        display_plate="DUP-999",
        make_id=make.id,
        model_id=model.id,
        actor_id=actor_id,
    )

    with pytest.raises(VehiclePlateConflictError):
        v_service.create_vehicle(
            organization_id=test_org.id,
            display_plate="DUP-999",
            make_id=make.id,
            model_id=model.id,
            actor_id=actor_id,
        )


def test_capacity_profile_with_decimal_uom(database, test_org, test_make_model, test_uoms, test_actor):
    make, model = test_make_model
    actor_id = test_actor.id
    v_service = VehicleService(database)
    c_service = VehicleCapacityService(database)

    v = v_service.create_vehicle(
        organization_id=test_org.id,
        display_plate="CAP-100",
        make_id=make.id,
        model_id=model.id,
        actor_id=actor_id,
    )

    u_kg = test_uoms["KG"]

    # Valid Capacity Profile
    prof = c_service.create_capacity_profile(
        vehicle_id=v.id,
        organization_id=test_org.id,
        actor_id=actor_id,
        max_gross_weight=Decimal("30000.0000"),
        max_gross_weight_unit_id=u_kg.id,
        tare_weight=Decimal("10000.0000"),
        tare_weight_unit_id=u_kg.id,
        max_payload=Decimal("20000.0000"),
        max_payload_unit_id=u_kg.id,
        pallet_positions=28,
    )

    assert prof.maximum_gross_weight_value == Decimal("30000.0000")
    assert prof.maximum_payload_value == Decimal("20000.0000")
    assert prof.pallet_position_count == 28

    # Invalid Capacity Profile (Payload > Gross Weight - Tare)
    with pytest.raises(VehicleCapacityInvalidError):
        c_service.create_capacity_profile(
            vehicle_id=v.id,
            organization_id=test_org.id,
            actor_id=actor_id,
            max_gross_weight=Decimal("30000.0000"),
            max_gross_weight_unit_id=u_kg.id,
            tare_weight=Decimal("10000.0000"),
            tare_weight_unit_id=u_kg.id,
            max_payload=Decimal("25000.0000"),  # Exceeds 30000 - 10000 = 20000
            max_payload_unit_id=u_kg.id,
        )


def test_carrier_assignment_validation(database, test_org, test_make_model, test_carrier_partner, test_actor):
    make, model = test_make_model
    partner, role = test_carrier_partner
    actor_id = test_actor.id

    v_service = VehicleService(database)
    oc_service = VehicleOwnershipCarrierService(database)

    v = v_service.create_vehicle(
        organization_id=test_org.id,
        display_plate="CAR-555",
        make_id=make.id,
        model_id=model.id,
        actor_id=actor_id,
    )

    # Valid Carrier Assignment
    ass = oc_service.assign_carrier(
        vehicle_id=v.id,
        organization_id=test_org.id,
        carrier_business_partner_id=partner.id,
        actor_id=actor_id,
    )

    assert ass.carrier_business_partner_id == partner.id
    assert ass.status == "CURRENT"

    # Reject non-CARRIER role partner
    non_carrier_code = f"BP-{uuid4().hex[:6].upper()}"
    non_carrier_partner = BusinessPartnerModel(
        id=uuid4(),
        organization_id=test_org.id,
        partner_code=non_carrier_code,
        normalized_partner_code=non_carrier_code,
        legal_name="Cliente Regular S.A.",
        person_type="LEGAL_ENTITY",
        country_code="PE",
        status="ACTIVE",
    )
    database.add(non_carrier_partner)
    database.commit()

    with pytest.raises(VehicleCarrierRoleRequiredError):
        oc_service.assign_carrier(
            vehicle_id=v.id,
            organization_id=test_org.id,
            carrier_business_partner_id=non_carrier_partner.id,
            actor_id=actor_id,
        )


def test_vehicle_documents_and_expired_compliance(database, test_org, test_make_model, test_actor):
    make, model = test_make_model
    actor_id = test_actor.id

    v_service = VehicleService(database)
    doc_service = VehicleDocumentService(database)

    v = v_service.create_vehicle(
        organization_id=test_org.id,
        display_plate="DOC-888",
        make_id=make.id,
        model_id=model.id,
        actor_id=actor_id,
    )
    v_service.activate_vehicle(v.id, test_org.id, actor_id)

    # Add Expired Document (SOAT)
    yesterday = utc_now() - timedelta(days=1)
    doc = doc_service.add_document(
        vehicle_id=v.id,
        organization_id=test_org.id,
        document_type="SOAT",
        actor_id=actor_id,
        document_number="SOAT-9999",
        expires_at=yesterday,
    )

    assert doc.verification_status == "NOT_VERIFIED"

    # Refresh status
    v_ref = v_service.refresh_operational_status(v)
    assert v_ref.operational_status == VehicleOperationalStatus.DOCUMENTS_EXPIRED.value
    assert v_ref.compliance_status == VehicleComplianceStatus.EXPIRED_DOCUMENTS.value


def test_plate_change_creates_alias_and_snapshot(database, test_org, test_make_model, test_actor):
    make, model = test_make_model
    actor_id = test_actor.id
    v_service = VehicleService(database)

    v = v_service.create_vehicle(
        organization_id=test_org.id,
        display_plate="OLD-111",
        make_id=make.id,
        model_id=model.id,
        actor_id=actor_id,
    )

    v_upd = v_service.change_plate(
        vehicle_id=v.id,
        organization_id=test_org.id,
        new_display_plate="NEW-222",
        reason="Duplicado por extravío de placa",
        actor_id=actor_id,
    )

    assert v_upd.display_plate == "NEW-222"
    assert v_upd.normalized_plate == "NEW222"

    # Check Alias
    alias = database.scalars(
        select(VehicleAliasModel).where(
            VehicleAliasModel.vehicle_id == v.id, VehicleAliasModel.previous_value == "OLD-111"
        )
    ).first()

    assert alias is not None
    assert alias.current_value == "NEW-222"

    # Check Version Snapshot
    ver = database.get(VehicleVersionModel, v_upd.active_version_id)
    assert ver is not None
    assert ver.plate_snapshot == "NEW-222"
