import sys
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.registry import *
from app.modules.logistics.vehicle_verifications.domain.value_objects.enums import *
from app.modules.logistics.vehicle_verifications.domain.errors.exceptions import *
from app.modules.logistics.vehicle_verifications.infrastructure.persistence.models import *
from app.modules.logistics.vehicle_verifications.domain.services.services import *
from app.modules.logistics.vehicle_verifications.application.services.source_service import VehicleVerificationSourceService
from app.modules.logistics.vehicle_verifications.application.services.verification_service import VehicleVerificationService
from app.modules.logistics.vehicle_verifications.application.services.assisted_verification_service import AssistedVehicleVerificationService
from app.modules.logistics.vehicle_verifications.application.services.apply_verification_service import ApplyVehicleVerificationService
from app.modules.logistics.vehicles.application.services.vehicle_service import VehicleService
from app.modules.logistics.vehicles.domain.value_objects.enums import VehicleType, BodyType
from app.modules.logistics.vehicles.infrastructure.persistence.models import VehicleMakeModel, VehicleModelModel
from app.modules.logistics.company_profile.models import OrganizationProfileModel

def run_tests():
    engine = create_engine("sqlite:///:memory:")

    # Handle SQLite compilations
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy import JSON
    from sqlalchemy.sql.functions import char_length

    @compiles(JSONB, "sqlite")
    def compile_jsonb_sqlite(type_, compiler, **kw):
        return "JSON"

    @compiles(char_length, "sqlite")
    def compile_char_length_sqlite(element, compiler, **kw):
        return f"LENGTH({compiler.process(element.clauses.clauses[0])})"

    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def connect_sqlite(dbapi_connection, connection_record):
        dbapi_connection.create_function("char_length", 1, lambda val: len(val) if val is not None else 0)

    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    print("Running Phase 028 SQLite tests...")

    org_id = uuid4()
    actor_id = uuid4()
    approver_id = uuid4()

    # Create Org
    org = OrganizationProfileModel(
        id=org_id,
        organization_id=org_id,
        legal_name="LOGISTICA TEST PERU S.A.C.",
        trade_name="LOGISTICA TEST",
        ruc="20601234567",
        country_code="PE",
        profile_status="ACTIVE",
    )
    session.add(org)
    session.commit()

    # 1. Seed & List Sources
    source_service = VehicleVerificationSourceService(session)
    sources = source_service.seed_default_sources()
    print(f"[OK] Seeded {len(sources)} sources.")
    assert len(sources) >= 4

    listed = source_service.list_sources(enabled_only=True)
    codes = [s.code for s in listed]
    assert "SUNARP_REGISTRY" in codes
    assert "AUTHORIZED_PROVIDER_FAKE" in codes
    print("[OK] Sources listed successfully.")

    make = VehicleMakeModel(id=uuid4(), organization_id=org_id, code="VOLVO", name="VOLVO", normalized_name="VOLVO", status="ACTIVE")
    model = VehicleModelModel(id=uuid4(), make_id=make.id, code="FH540", name="FH540", normalized_name="FH540", status="ACTIVE")
    session.add_all([make, model])
    session.commit()

    veh_service = VehicleService(session)
    vehicle = veh_service.create_vehicle(
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
    print(f"[OK] Created Vehicle {vehicle.display_plate} (ID: {vehicle.id}).")

    # 3. Provider Verification Flow
    verif_service = VehicleVerificationService(session)
    verif = verif_service.request_verification(
        organization_id=org_id,
        vehicle_id=vehicle.id,
        domain="TECHNICAL_INSPECTION",
        source_code="AUTHORIZED_PROVIDER_FAKE",
        actor_id=actor_id,
    )
    assert verif.status == "COMPLETED"
    assert verif.result_status == "VALID"
    print("[OK] Executed Provider Verification (Fake Provider).")

    # 4. Conflict & Compliance Check
    verif_reg = verif_service.request_verification(
        organization_id=org_id,
        vehicle_id=vehicle.id,
        domain="REGISTRY_IDENTITY",
        source_code="AUTHORIZED_PROVIDER_FAKE",
        actor_id=actor_id,
    )
    assert verif_reg.conflict_status == "HAS_CONFLICTS"

    compliance = verif_service.get_verification_compliance(vehicle.id, org_id)
    assert compliance["display_plate"] == "ABC-123"
    assert compliance["has_open_conflicts"] is True
    print("[OK] Conflict detection & compliance calculation verified.")

    # 5. Assisted Verification Flow & Separation of Duties
    sunarp_source = source_service.get_source_by_code("SUNARP_REGISTRY")
    assisted_service = AssistedVehicleVerificationService(session)

    assisted = assisted_service.create_assisted_verification(
        organization_id=org_id,
        vehicle_id=vehicle.id,
        domain="REGISTRY_IDENTITY",
        source_id=sunarp_source.id,
        verification_reason="Verificación manual por copia literal de SUNARP",
        observed_plate="ABC-123",
        actor_id=actor_id,
        observed_make="VOLVO",
        observed_model="FH540",
        observed_year=2020,
    )
    assert assisted.approval_status == "SUBMITTED"

    try:
        assisted_service.approve_assisted_verification(
            assisted_id=assisted.id,
            organization_id=org_id,
            approver_id=actor_id,
            enforce_separation_of_duties=True,
        )
        print("[FAIL] Separation of duties check failed!")
        sys.exit(1)
    except AssistedVehicleVerificationSeparationOfDutiesError:
        print("[OK] Separation of duties enforced (Creator cannot approve).")

    approved_verif = assisted_service.approve_assisted_verification(
        assisted_id=assisted.id,
        organization_id=org_id,
        approver_id=approver_id,
        enforce_separation_of_duties=True,
    )
    assert approved_verif.status == "COMPLETED"
    assert approved_verif.approved_by_user_id == approver_id
    print("[OK] Approved Assisted Verification with separate user.")

    # 6. Apply Verified Fields -> New Vehicle Version
    initial_ver_id = vehicle.active_version_id
    apply_service = ApplyVehicleVerificationService(session)
    new_version = apply_service.apply_verified_fields(
        verification_id=verif_reg.id,
        organization_id=org_id,
        selected_fields=["manufacturing_year"],
        reason="Actualización de año con verificación SUNARP",
        actor_id=actor_id,
    )
    assert new_version.id != initial_ver_id
    assert vehicle.manufacturing_year == 2022
    assert vehicle.active_version_id == new_version.id
    print("[OK] Applied verified fields & generated new VehicleVersion snapshot.")

    print("\nALL PHASE 028 TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
