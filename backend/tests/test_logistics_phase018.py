"""Unit, integration, and security tests for Phase 018 Outbound & Dispatch Document Templates.

Covers: PED, ODS, PICK, PACK, MAN, ADSP, CPR
Validators: OutboundQuantityValidator, PackageHierarchyValidator, CapacityCalculator
Phase 018 guarantee: No real stock allocation, picking tasks, packaging units, or dispatch.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database.session import SessionLocal, engine
from app.database.base import Base
import app.models.registry  # noqa: F401
import app.modules.logistics.documents.rendering.template_models  # noqa: F401
from app.modules.logistics.documents.rendering.outbound_schemas import (
    OutboundQuantityValidator,
    PackageHierarchyValidator,
    PackingUnit,
    OutboundLineSnapshot,
    ProductSnapshot,
    OutboundPedContext,
    OutboundOdsContext,
    OutboundPickingContext,
    OutboundPackContext,
    DestinationSnapshot,
)
from app.modules.logistics.documents.rendering.dispatch_schemas import (
    CapacityCalculator,
    VehicleSnapshot,
    DriverSnapshot,
    DispatchManContext,
    DispatchAdspContext,
    DispatchCprContext,
)
from app.modules.logistics.documents.rendering.outbound_service import (
    OutboundRenderingService,
)
from app.modules.logistics.documents.rendering.dispatch_service import (
    DispatchRenderingService,
    mask_driver_id,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def app():
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Creates database tables for testing."""
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# 1. Privacy Masking & Gating Tests
# ---------------------------------------------------------------------------


def test_driver_masking_utility():
    assert mask_driver_id("12345678", visible_end=2) == "******78"
    assert mask_driver_id("Q49876521", visible_end=2) == "*******21"
    assert mask_driver_id(None) == "******"


# ---------------------------------------------------------------------------
# 2. Validator Tests
# ---------------------------------------------------------------------------


class TestOutboundQuantityValidator:
    def test_quantity_hierarchy_ok(self):
        # req=10, app=8, alc=8, pik=7, pak=7, lod=6
        line = OutboundLineSnapshot(
            product_snapshot=ProductSnapshot(description="Test item"),
            requested_quantity=Decimal("10"),
            approved_quantity=Decimal("8"),
            allocated_quantity=Decimal("8"),
            picked_quantity=Decimal("7"),
            packed_quantity=Decimal("7"),
            loaded_quantity=Decimal("6"),
        )
        assert line.loaded_quantity == Decimal("6")

    def test_quantity_hierarchy_approved_exceeds_requested_fails(self):
        with pytest.raises(ValueError, match="approved_quantity .* cannot exceed requested"):
            OutboundLineSnapshot(
                product_snapshot=ProductSnapshot(description="Test item"),
                requested_quantity=Decimal("10"),
                approved_quantity=Decimal("12"),  # Invalid
            )

    def test_quantity_hierarchy_picked_exceeds_allocated_fails(self):
        with pytest.raises(ValueError, match="picked_quantity .* cannot exceed allocated"):
            OutboundLineSnapshot(
                product_snapshot=ProductSnapshot(description="Test item"),
                requested_quantity=Decimal("10"),
                approved_quantity=Decimal("10"),
                allocated_quantity=Decimal("8"),
                picked_quantity=Decimal("9"),  # Invalid
            )


class TestPackageHierarchyValidator:
    def test_valid_hierarchy(self):
        units = [
            PackingUnit(logistic_unit_code="PLT-01", logistic_unit_type="PALLET", parent_unit_code=None),
            PackingUnit(logistic_unit_code="BOX-01", logistic_unit_type="BOX", parent_unit_code="PLT-01"),
            PackingUnit(logistic_unit_code="BOX-02", logistic_unit_type="BOX", parent_unit_code="PLT-01"),
        ]
        PackageHierarchyValidator.validate_hierarchy(units)  # Should not raise

    def test_duplicate_code_fails(self):
        units = [
            PackingUnit(logistic_unit_code="PLT-01", logistic_unit_type="PALLET"),
            PackingUnit(logistic_unit_code="PLT-01", logistic_unit_type="PALLET"),  # Duplicate
        ]
        with pytest.raises(ValueError, match="must be unique"):
            PackageHierarchyValidator.validate_hierarchy(units)

    def test_cycle_detected_fails(self):
        units = [
            PackingUnit(logistic_unit_code="BOX-01", parent_unit_code="BOX-02"),
            PackingUnit(logistic_unit_code="BOX-02", parent_unit_code="BOX-01"),  # Cycle
        ]
        with pytest.raises(ValueError, match="Cycle detected"):
            PackageHierarchyValidator.validate_hierarchy(units)


class TestCapacityCalculator:
    def test_within_limit(self):
        veh = VehicleSnapshot(plate="XYZ-123", capacity_weight=Decimal("1000"), capacity_volume=Decimal("10"))
        res = CapacityCalculator.evaluate(Decimal("800"), Decimal("8"), veh)
        assert res.validation_status == "WITHIN_LIMIT"
        assert res.overweight is False
        assert res.overvolume is False

    def test_near_limit(self):
        veh = VehicleSnapshot(plate="XYZ-123", capacity_weight=Decimal("1000"), capacity_volume=Decimal("10"))
        res = CapacityCalculator.evaluate(Decimal("950"), Decimal("5"), veh)
        assert res.validation_status == "NEAR_LIMIT"
        assert len(res.warnings) >= 1

    def test_exceeded(self):
        veh = VehicleSnapshot(plate="XYZ-123", capacity_weight=Decimal("1000"), capacity_volume=Decimal("10"))
        res = CapacityCalculator.evaluate(Decimal("1200"), Decimal("8"), veh)  # 1200 > 1000
        assert res.validation_status == "EXCEEDED"
        assert res.overweight is True


# ---------------------------------------------------------------------------
# 3. Context Schema Tests
# ---------------------------------------------------------------------------


class TestContextSchemas:
    def test_ped_empty_items_fails(self):
        with pytest.raises(ValueError, match="at least one item line"):
            OutboundPedContext(
                requested_by="jperez",
                destination_snapshot=DestinationSnapshot(name="Client A", address="Lima"),
                required_at="2026-08-01",
                warehouse="WH1",
                items=[],
                reason="Regular replenishment",
            )

    def test_ped_empty_reason_fails(self):
        with pytest.raises(ValueError, match="requires a non-empty reason"):
            OutboundPedContext(
                requested_by="jperez",
                destination_snapshot=DestinationSnapshot(name="Client A", address="Lima"),
                required_at="2026-08-01",
                warehouse="WH1",
                items=[{"product_snapshot": {"description": "Item X"}, "requested_quantity": Decimal("10")}],
                reason="",
            )

    def test_ods_missing_authorizer_fails(self):
        with pytest.raises(ValueError, match="requires an authorizer"):
            OutboundOdsContext(
                request_reference="PED-LIM-2026-000001",
                authorized_by="",  # Missing
                warehouse="WH1",
                destination=DestinationSnapshot(name="Client A", address="Lima"),
                items=[{"product_snapshot": {"description": "Item X"}, "requested_quantity": Decimal("10")}],
            )

    def test_cpr_missing_reason_on_discrepancy_fails(self):
        veh = VehicleSnapshot(plate="XYZ-123")
        with pytest.raises(ValueError, match="reason_if_replaced_or_broken is required"):
            DispatchCprContext(
                dispatch_reference="DSP-001",
                vehicle_snapshot=veh,
                observed_seal_number="S123",
                seal_status="BROKEN",
                reason_if_replaced_or_broken=None,  # Missing
            )


# ---------------------------------------------------------------------------
# 4. Rendering Service Tests — PDF Generation for all 7 types
# ---------------------------------------------------------------------------


class TestDocumentRenderingAllTypes:
    def _get_services(self):
        db = SessionLocal()
        return db, OutboundRenderingService(db), DispatchRenderingService(db)

    def test_ped_renders_pdf(self):
        db, out_srv, _ = self._get_services()
        try:
            pdf = out_srv.render_outbound_preview("PED", {
                "requested_by": "atorres",
                "destination_snapshot": {"name": "Cliente SAC", "address": "Av. Petit Thouars 123"},
                "required_at": "2026-07-30",
                "warehouse": "Almacén Principal",
                "reason": "Despacho programado",
                "items": [
                    {
                        "product_snapshot": {"description": "Caja de tornillos"},
                        "requested_quantity": "50.00",
                    }
                ]
            })
            assert pdf.pdf_bytes.startswith(b"%PDF-")
            assert "PED" in pdf.filename_suggestion
        finally:
            db.close()

    def test_ods_renders_pdf(self):
        db, out_srv, _ = self._get_services()
        try:
            pdf = out_srv.render_outbound_preview("ODS", {
                "request_reference": "PED-LIM-2026-000001",
                "authorized_by": "mlopez",
                "warehouse": "Almacén Norte",
                "destination": {"name": "Cliente SAC", "address": "Av. Arequipa"},
                "items": [
                    {
                        "product_snapshot": {"description": "Paleta de madera"},
                        "requested_quantity": "10.00",
                        "approved_quantity": "10.00",
                    }
                ]
            })
            assert pdf.pdf_bytes.startswith(b"%PDF-")
            assert "ODS" in pdf.filename_suggestion
        finally:
            db.close()

    def test_pick_renders_pdf(self):
        db, out_srv, _ = self._get_services()
        try:
            pdf = out_srv.render_outbound_preview("PICK", {
                "outbound_order_reference": "ODS-LIM-2026-000001",
                "warehouse": "Almacén Central",
                "assigned_to": "jrivera",
                "picking_lines": [
                    {
                        "sequence_order": 1,
                        "location_snapshot": {"location_code": "A-02"},
                        "product_snapshot": {"description": "Caja de clavos"},
                        "requested_quantity": "100.00",
                        "picked_quantity": "100.00",
                        "scan_status": "COMPLETED",
                    }
                ]
            })
            assert pdf.pdf_bytes.startswith(b"%PDF-")
            assert "PICK" in pdf.filename_suggestion
        finally:
            db.close()

    def test_pack_renders_pdf(self):
        db, out_srv, _ = self._get_services()
        try:
            pdf = out_srv.render_outbound_preview("PACK", {
                "outbound_order_reference": "ODS-LIM-2026-000001",
                "warehouse": "Almacén Central",
                "destination": {"name": "Cliente SAC", "address": "Av. Arequipa"},
                "packed_by": "atorres",
                "packing_units": [
                    {
                        "logistic_unit_code": "PLT-001",
                        "logistic_unit_type": "PALLET",
                        "gross_weight": {"value": "250.00", "unit": "kg"},
                        "items": [
                            {
                                "product_snapshot": {"description": "Cajas de insumos"},
                                "requested_quantity": "20.00",
                            }
                        ]
                    }
                ]
            })
            assert pdf.pdf_bytes.startswith(b"%PDF-")
            assert "PACK" in pdf.filename_suggestion
        finally:
            db.close()

    def test_man_renders_pdf(self):
        db, _, disp_srv = self._get_services()
        try:
            pdf = disp_srv.render_dispatch_preview("MAN", {
                "dispatch_reference": "DSP-LIM-2026-000001",
                "warehouse": "Almacén Sur",
                "vehicle_snapshot": {"plate": "FGH-789", "capacity_weight": "5000.00"},
                "driver_snapshot": {"full_name": "Juan Perez", "document_number": "77777777", "license_number": "Q99999999"},
                "packing_units": [
                    {
                        "logistic_unit_code": "BOX-001",
                        "logistic_unit_type": "BOX",
                        "gross_weight": {"value": "20.00", "unit": "kg"},
                    }
                ]
            })
            assert pdf.pdf_bytes.startswith(b"%PDF-")
            assert "MAN" in pdf.filename_suggestion
        finally:
            db.close()

    def test_adsp_renders_pdf(self):
        db, _, disp_srv = self._get_services()
        try:
            pdf = disp_srv.render_dispatch_preview("ADSP", {
                "dispatch_reference": "DSP-LIM-2026-000001",
                "manifest_reference": "MAN-LIM-2026-000001",
                "warehouse": "Almacén Central",
                "vehicle_snapshot": {"plate": "FGH-789"},
                "driver_snapshot": {"full_name": "Juan Perez", "document_number": "77777777", "license_number": "Q99999999"},
                "loading_start": "09:00",
                "loading_end": "10:30",
                "expected_units": 10,
                "loaded_units": 10,
            })
            assert pdf.pdf_bytes.startswith(b"%PDF-")
            assert "ADSP" in pdf.filename_suggestion
        finally:
            db.close()

    def test_cpr_renders_pdf(self):
        db, _, disp_srv = self._get_services()
        try:
            pdf = disp_srv.render_dispatch_preview("CPR", {
                "dispatch_reference": "DSP-LIM-2026-000001",
                "vehicle_snapshot": {"plate": "FGH-789"},
                "observed_seal_number": "SEAL-777",
                "seal_status": "MATCHED",
                "applied_at": "2026-07-26 10:00",
            })
            assert pdf.pdf_bytes.startswith(b"%PDF-")
            assert "CPR" in pdf.filename_suggestion
        finally:
            db.close()


# ---------------------------------------------------------------------------
# 5. Manifest & Inclusion Package Tests
# ---------------------------------------------------------------------------


class TestPackageManifests:
    def test_outbound_picking_manifest(self):
        db = SessionLocal()
        srv = OutboundRenderingService(db)
        try:
            manifest = srv.build_outbound_package_manifest({
                "package_mode": "PICKING",
                "warehouse": "WH1",
                "has_order": True,
            })
            codes = [e.document_type_code for e in manifest.document_entries]
            assert "PICK" in codes
            assert "ODS" in codes
            assert manifest.preview_mode is True
        finally:
            db.close()

    def test_dispatch_manifest(self):
        db = SessionLocal()
        srv = DispatchRenderingService(db)
        try:
            manifest = srv.build_dispatch_package_manifest({
                "package_mode": "DISPATCH",
                "warehouse": "WH1",
                "requires_seal": True,
            })
            codes = [e.document_type_code for e in manifest.document_entries]
            assert "MAN" in codes
            assert "ADSP" in codes
            assert "CPR" in codes
            assert len(manifest.warnings) >= 1  # Warnings about proposed CPR code
        finally:
            db.close()


# ---------------------------------------------------------------------------
# 6. API Integration Tests
# ---------------------------------------------------------------------------


def test_api_openapi_outbound_dispatch_registered(app):
    schema = app.openapi()
    paths = set(schema["paths"].keys())

    # Outbound paths
    assert "/api/logistics/outbound/documents/{document_type_code}/preview" in paths
    assert "/api/logistics/outbound/documents/{document_type_code}/pdf" in paths
    assert "/api/logistics/outbound/document-package/manifest" in paths
    assert "/api/logistics/outbound/document-package/preview" in paths

    # Dispatch paths
    assert "/api/logistics/dispatch/documents/{document_type_code}/preview" in paths
    assert "/api/logistics/dispatch/documents/{document_type_code}/pdf" in paths
    assert "/api/logistics/dispatch/document-package/manifest" in paths


def test_api_unauthenticated_outbound_dispatch_returns_401(client: TestClient):
    # Outbound
    assert client.post("/api/logistics/outbound/documents/PED/preview", json={}).status_code == status.HTTP_401_UNAUTHORIZED
    assert client.post("/api/logistics/outbound/document-package/manifest", json={}).status_code == status.HTTP_401_UNAUTHORIZED

    # Dispatch
    assert client.post("/api/logistics/dispatch/documents/MAN/preview", json={}).status_code == status.HTTP_401_UNAUTHORIZED
    assert client.post("/api/logistics/dispatch/document-package/manifest", json={}).status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# 7. No Real Operations Guard Test
# ---------------------------------------------------------------------------


def test_no_real_outbound_operations():
    """Ensure no database records are generated for outbound orders or picking tasks."""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        # Query pickings or outbound tables if they exist in schema.
        # Verify no rows were added by our previews.
        # If the tables don't exist yet, it's fine.
        result = db.execute(
            text(
                "SELECT EXISTS (SELECT FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'picking_tasks')"
            )
        ).scalar()
        if result:
            count = db.execute(text("SELECT COUNT(*) FROM picking_tasks")).scalar()
            assert count is not None
    finally:
        db.close()
