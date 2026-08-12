"""Unit & Integration Tests for Phase 028 — Vehicle Verifications."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database.base import utc_now
from app.main import app
from app.modules.logistics.vehicle_verifications.application.services.apply_verification_service import ApplyVehicleVerificationService
from app.modules.logistics.vehicle_verifications.application.services.assisted_verification_service import AssistedVehicleVerificationService
from app.modules.logistics.vehicle_verifications.application.services.source_service import VehicleVerificationSourceService
from app.modules.logistics.vehicle_verifications.application.services.verification_service import VehicleVerificationService
from app.modules.logistics.vehicle_verifications.domain.errors.exceptions import (
    AssistedVehicleVerificationSeparationOfDutiesError,
    VehicleVerificationSourceNotAuthorized,
)
from app.modules.logistics.vehicles.application.services.vehicle_service import VehicleService
from app.modules.logistics.vehicles.domain.value_objects.enums import (
    BodyType,
    VehicleType,
)
from app.modules.logistics.vehicles.infrastructure.persistence.models import (
    VehicleMakeModel,
    VehicleModelModel,
)




@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def actor_id():
    return uuid4()


@pytest.fixture
def approver_id():
    return uuid4()


@pytest.fixture
def sample_vehicle(database, org_id, actor_id):
    make = VehicleMakeModel(id=uuid4(), organization_id=org_id, code="VOLVO", name="VOLVO", normalized_name="VOLVO", status="ACTIVE")
    model = VehicleModelModel(id=uuid4(), make_id=make.id, code="FH540", name="FH540", normalized_name="FH540", status="ACTIVE")
    database.add_all([make, model])
    database.commit()

    service = VehicleService(database)
    return service.create_vehicle(
        organization_id=org_id,
        display_plate="ABC-123",
        make_id=make.id,
        model_id=model.id,
        vehicle_type=VehicleType.HEAVY_TRUCK.value,
        body_type=BodyType.CONTAINER_CHASSIS.value,
        manufacturing_year=2020,
        vin="19V12345678902345",
        actor_id=actor_id,
    )




def test_seed_and_list_sources(database):
    service = VehicleVerificationSourceService(database)
    sources = service.seed_default_sources()
    assert len(sources) >= 4

    listed = service.list_sources(enabled_only=True)
    codes = [s.code for s in listed]
    assert "SUNARP_REGISTRY" in codes
    assert "MTC_TRANSPORT" in codes
    assert "SBS_SOAT" in codes
    assert "AUTHORIZED_PROVIDER_FAKE" in codes


def test_request_and_execute_provider_verification(database, org_id, actor_id, sample_vehicle):
    source_service = VehicleVerificationSourceService(database)
    source_service.seed_default_sources()

    verif_service = VehicleVerificationService(database)
    verif = verif_service.request_verification(
        organization_id=org_id,
        vehicle_id=sample_vehicle.id,
        domain="TECHNICAL_INSPECTION",
        source_code="AUTHORIZED_PROVIDER_FAKE",
        actor_id=actor_id,
    )

    assert verif.status == "COMPLETED"
    assert verif.result_status == "VALID"
    assert verif.confidence_level == "HIGH"
    assert verif.original_response_hash is not None


def test_conflict_detection_and_compliance(database, org_id, actor_id, sample_vehicle):
    source_service = VehicleVerificationSourceService(database)
    source_service.seed_default_sources()

    verif_service = VehicleVerificationService(database)
    verif = verif_service.request_verification(
        organization_id=org_id,
        vehicle_id=sample_vehicle.id,
        domain="REGISTRY_IDENTITY",
        source_code="AUTHORIZED_PROVIDER_FAKE",
        actor_id=actor_id,
    )

    # Fake provider returns VOLVO FH540 2022 vs master 2020 -> conflicts expected
    assert verif.conflict_status == "HAS_CONFLICTS"

    compliance = verif_service.get_verification_compliance(sample_vehicle.id, org_id)
    assert compliance["vehicle_id"] == str(sample_vehicle.id)
    assert compliance["display_plate"] == "ABC-123"
    assert compliance["has_open_conflicts"] is True


def test_assisted_verification_flow_and_separation_of_duties(database, org_id, actor_id, approver_id, sample_vehicle):
    source_service = VehicleVerificationSourceService(database)
    sources = source_service.seed_default_sources()
    sunarp_source = [s for s in sources if s.code == "SUNARP_REGISTRY"][0]

    assisted_service = AssistedVehicleVerificationService(database)
    assisted = assisted_service.create_assisted_verification(
        organization_id=org_id,
        vehicle_id=sample_vehicle.id,
        domain="REGISTRY_IDENTITY",
        source_id=sunarp_source.id,
        verification_reason="Verificación manual de tarjeta de propiedad",
        observed_plate="ABC-123",
        actor_id=actor_id,
        observed_make="VOLVO",
        observed_model="FH540",
        observed_year=2020,
    )

    assert assisted.approval_status == "SUBMITTED"

    # Test Separation of Duties (creator trying to approve)
    with pytest.raises(AssistedVehicleVerificationSeparationOfDutiesError):
        assisted_service.approve_assisted_verification(
            assisted_id=assisted.id,
            organization_id=org_id,
            approver_id=actor_id,
            enforce_separation_of_duties=True,
        )

    # Approve with separate approver
    verif = assisted_service.approve_assisted_verification(
        assisted_id=assisted.id,
        organization_id=org_id,
        approver_id=approver_id,
        enforce_separation_of_duties=True,
    )

    assert verif.status == "COMPLETED"
    assert verif.approved_by_user_id == approver_id


def test_apply_verified_fields_creates_new_version(database, org_id, actor_id, sample_vehicle):
    source_service = VehicleVerificationSourceService(database)
    source_service.seed_default_sources()

    verif_service = VehicleVerificationService(database)
    verif = verif_service.request_verification(
        organization_id=org_id,
        vehicle_id=sample_vehicle.id,
        domain="REGISTRY_IDENTITY",
        source_code="AUTHORIZED_PROVIDER_FAKE",
        actor_id=actor_id,
    )

    apply_service = ApplyVehicleVerificationService(database)
    initial_version_id = sample_vehicle.active_version_id

    new_version = apply_service.apply_verified_fields(
        verification_id=verif.id,
        organization_id=org_id,
        selected_fields=["manufacturing_year"],
        reason="Actualización con datos verificados SUNARP",
        actor_id=actor_id,
    )

    assert new_version.id != initial_version_id
    assert sample_vehicle.manufacturing_year == 2022
    assert sample_vehicle.active_version_id == new_version.id


def test_api_vehicle_verifications_endpoints(database):
    from app.database.session import get_db

    def _override_get_db():
        yield database

    app.dependency_overrides[get_db] = _override_get_db
    try:
        client = TestClient(app)

        # Seed sources
        resp = client.post("/api/logistics/vehicle-verification-sources/seed")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 4

        # List sources
        resp = client.get("/api/logistics/vehicle-verification-sources")
        assert resp.status_code == 200
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert len(resp.json()) >= 4
