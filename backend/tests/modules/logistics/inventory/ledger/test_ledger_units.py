"""Phase 044 — Unit tests for the inventory ledger."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest


class TestHashService:
    def test_canonicalize_decimal_precision(self):
        from app.modules.logistics.inventory.ledger.domain.services.hash_service import (
            canonicalize,
        )

        payload = {
            "a": Decimal("1.5"),
            "b": Decimal("0.000000001"),
            "c": Decimal("999999999999.999999999999"),
        }
        canonical = canonicalize(payload)
        assert '"a":"1.5"' in canonical
        # Decimal uses scientific notation when the exponent is large.
        assert '"b":"' in canonical and '"c":"999999999999.999999999999"' in canonical
        # The value must round-trip deterministically.

        reloaded = json.loads(canonical)
        assert Decimal(reloaded["a"]) == Decimal("1.5")
        assert Decimal(reloaded["b"]) == Decimal("0.000000001")

    def test_canonicalize_uuid(self):
        from app.modules.logistics.inventory.ledger.domain.services.hash_service import (
            canonicalize,
        )

        uid = UUID("12345678-1234-5678-1234-567812345678")
        canonical = canonicalize({"id": uid})
        assert '"12345678-1234-5678-1234-567812345678"' in canonical

    def test_canonicalize_datetime_normalizes_to_utc(self):
        from app.modules.logistics.inventory.ledger.domain.services.hash_service import (
            canonicalize,
        )

        naive = datetime(2026, 1, 1, 12, 0, 0)  # noqa: DTZ001
        aware_utc = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        canonical_a = canonicalize({"t": naive})
        canonical_b = canonicalize({"t": aware_utc})
        assert canonical_a == canonical_b

    def test_hash_is_deterministic(self):
        from app.modules.logistics.inventory.ledger.domain.services.hash_service import (
            hash_payload,
        )

        payload = {"a": 1, "b": [1, 2, 3], "c": {"x": "y"}}
        h1 = hash_payload(payload)
        h2 = hash_payload(payload)
        assert h1 == h2
        # Different payloads should produce different hashes.
        assert h1 != hash_payload({"a": 1, "b": [1, 2, 3], "c": {"x": "z"}})

    def test_compute_movement_hash_changes_with_payload(self):
        from app.modules.logistics.inventory.ledger.domain.services.hash_service import (
            compute_movement_hash,
        )

        base = dict(  # noqa: C408
            ledger_partition_key="org:wh:2026",
            ledger_sequence=1,
            movement_code="MOV-1",
            movement_type="PUTAWAY_COMPLETED",
            movement_family="INBOUND",
            organization_id=uuid4(),
            branch_id=uuid4(),
            source_event_id="evt-1",
            source_event_version=1,
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
            posted_at=datetime(2026, 1, 1, tzinfo=UTC),
            reason_code="PUTAWAY_COMPLETED",
            compensation_for_movement_id=None,
            previous_movement_hash=None,
            lines=[{"line_number": 1, "quantity": "5"}],
            sources=[{"source_event_id": "evt-1"}],
        )
        h1 = compute_movement_hash(**base)
        tampered = {**base, "ledger_sequence": 2}
        h2 = compute_movement_hash(**tampered)
        assert h1 != h2

    def test_compute_line_content_hash(self):
        from app.modules.logistics.inventory.ledger.domain.services.hash_service import (
            compute_line_content_hash,
        )

        base = dict(  # noqa: C408
            line_number=1,
            product_id=uuid4(),
            product_version_id=None,
            quantity=Decimal(5),
            unit_id=uuid4(),
            base_quantity=Decimal(5),
            base_unit_id=uuid4(),
            source_position_id=None,
            destination_position_id=None,
            source_external_boundary_kind="SUPPLIER",
            destination_external_boundary_kind=None,
            quantity_direction="ENTRY",
        )
        h1 = compute_line_content_hash(**base)
        h2 = compute_line_content_hash(**base)
        assert h1 == h2
        tampered = {**base, "quantity": Decimal(6)}
        h3 = compute_line_content_hash(**tampered)
        assert h1 != h3


class TestSequenceService:
    def test_build_partition_key(self):
        from app.modules.logistics.inventory.ledger.domain.services.sequence_service import (
            InventoryLedgerSequenceService,
        )

        svc = InventoryLedgerSequenceService(db=None)  # type: ignore[arg-type]
        key = svc.build_partition_key(
            organization_id=UUID("12345678-1234-5678-1234-567812345678"),
            warehouse_id=UUID("12345678-1234-5678-1234-567812345679"),
            fiscal_year=2026,
        )
        assert "2026" in key
        assert "12345678-1234-5678-1234-567812345678" in key

    def test_build_movement_code_format(self):
        from app.modules.logistics.inventory.ledger.domain.services.sequence_service import (
            InventoryMovementCodeService,
        )

        svc = InventoryMovementCodeService(db=None)  # type: ignore[arg-type]
        code, normalized = svc.build_movement_code(
            organization_id=uuid4(),
            site_code="LIM",
            fiscal_year=2026,
            correlative=1,
        )
        assert code == "MOV-LIM-2026-000001"
        assert normalized == "MOV-LIM-2026-000001"

    def test_build_movement_code_no_site(self):
        from app.modules.logistics.inventory.ledger.domain.services.sequence_service import (
            InventoryMovementCodeService,
        )

        svc = InventoryMovementCodeService(db=None)  # type: ignore[arg-type]
        code, normalized = svc.build_movement_code(
            organization_id=uuid4(),
            site_code="",
            fiscal_year=2026,
            correlative=42,
            site_code_used=False,
        )
        assert code == "MOV-GLOBAL-2026-000042"
        assert normalized == "MOV-GLOBAL-2026-000042"


class TestStateTransitionPolicy:
    def test_legal_transitions_present(self):
        from app.modules.logistics.inventory.ledger.domain.policies.state_transition_policy import (
            LEGAL_STATE_TRANSITIONS,
            is_legal_transition,
        )

        assert len(LEGAL_STATE_TRANSITIONS) > 0
        assert is_legal_transition(
            availability_from="PENDING_PUTAWAY",
            availability_to="AVAILABLE",
            quality_from="QUARANTINE",
            quality_to="APPROVED",
            transit_from="INBOUND_STAGING",
            transit_to="NOT_IN_TRANSIT",
            damage_from="NORMAL",
            damage_to="NORMAL",
            expiration_from="NOT_APPLICABLE",
            expiration_to="VALID",
        )
        assert not is_legal_transition(
            availability_from="UNKNOWN",
            availability_to="AVAILABLE",
            quality_from="UNKNOWN",
            quality_to="APPROVED",
            transit_from="NOT_IN_TRANSIT",
            transit_to="NOT_IN_TRANSIT",
            damage_from="NORMAL",
            damage_to="NORMAL",
            expiration_from="NOT_APPLICABLE",
            expiration_to="VALID",
        )


class TestValidationService:
    def _payload(self, **overrides):
        base = {
            "movement_type": "PUTAWAY_COMPLETED",
            "source_adapter_name": "PUTAWAY_COMPLETED",
            "source_event_id": "evt-1",
            "source_hash": "a" * 64,
            "payload_hash": "b" * 64,
            "lines": [
                {
                    "product_id": str(uuid4()),
                    "unit_id": str(uuid4()),
                    "base_unit_id": str(uuid4()),
                    "quantity": "10",
                    "base_quantity": "10",
                    "destination_position_id": str(uuid4()),
                    "quantity_direction": "TRANSFER",
                }
            ],
        }
        base.update(overrides)
        return base

    def test_accepts_valid_payload(self):
        from app.modules.logistics.inventory.ledger.application.services.validation_service import (
            InventoryMovementValidationService,
        )
        from app.modules.logistics.inventory.ledger.domain.services.availability_provider import (
            SourceBackedAvailabilityProvider,
        )

        svc = InventoryMovementValidationService(
            availability_provider=SourceBackedAvailabilityProvider(None)  # type: ignore[arg-type]
        )
        product_id = uuid4()
        payload = self._payload()
        payload["lines"][0]["product_id"] = str(product_id)
        payload["lines"][0]["source_position_id"] = str(uuid4())
        payload["source_references"] = [
            {
                "source_entity_type": "OPERATIONAL_PLACEMENT",
                "source_entity_id": str(uuid4()),
                "source_hash": "a" * 64,
                "product_id": str(product_id),
                "requested_base_quantity": "10",
            }
        ]
        result = svc.validate(
            organization_id=uuid4(),
            source_adapter_name="PUTAWAY_COMPLETED",
            movement_type="PUTAWAY_COMPLETED",
            payload=payload,
        )
        assert result.validation_status in {"VALID", "VALID_WITH_WARNINGS"}

    def test_rejects_unknown_movement_type(self):
        from app.modules.logistics.inventory.ledger.application.services.validation_service import (
            InventoryMovementValidationService,
        )
        from app.modules.logistics.inventory.ledger.domain.services.availability_provider import (
            SourceBackedAvailabilityProvider,
        )

        svc = InventoryMovementValidationService(
            availability_provider=SourceBackedAvailabilityProvider(None)  # type: ignore[arg-type]
        )
        result = svc.validate(
            organization_id=uuid4(),
            source_adapter_name="PUTAWAY_COMPLETED",
            movement_type="UNKNOWN_FUTURE",
            payload=self._payload(),
        )
        codes = [e.code for e in result.blocking_errors]
        assert "INVENTORY_MOVEMENT_TYPE_INVALID" in codes

    def test_rejects_disabled_movement_type(self):
        from app.modules.logistics.inventory.ledger.application.services.validation_service import (
            InventoryMovementValidationService,
        )
        from app.modules.logistics.inventory.ledger.domain.services.availability_provider import (
            SourceBackedAvailabilityProvider,
        )

        svc = InventoryMovementValidationService(
            availability_provider=SourceBackedAvailabilityProvider(None)  # type: ignore[arg-type]
        )
        result = svc.validate(
            organization_id=uuid4(),
            source_adapter_name="ADJUSTMENT_APPROVED",
            movement_type="ADJUSTMENT_INCREASE_FUTURE",
            payload=self._payload(),
        )
        codes = [e.code for e in result.blocking_errors]
        assert "INVENTORY_MOVEMENT_TYPE_INVALID" in codes

    def test_rejects_non_positive_quantity(self):
        from app.modules.logistics.inventory.ledger.application.services.validation_service import (
            InventoryMovementValidationService,
        )
        from app.modules.logistics.inventory.ledger.domain.services.availability_provider import (
            SourceBackedAvailabilityProvider,
        )

        svc = InventoryMovementValidationService(
            availability_provider=SourceBackedAvailabilityProvider(None)  # type: ignore[arg-type]
        )
        payload = self._payload(
            lines=[
                {
                    "product_id": str(uuid4()),
                    "unit_id": str(uuid4()),
                    "base_unit_id": str(uuid4()),
                    "quantity": "0",
                    "base_quantity": "0",
                    "destination_position_id": str(uuid4()),
                    "quantity_direction": "TRANSFER",
                }
            ]
        )
        result = svc.validate(
            organization_id=uuid4(),
            source_adapter_name="PUTAWAY_COMPLETED",
            movement_type="PUTAWAY_COMPLETED",
            payload=payload,
        )
        codes = [e.code for e in result.blocking_errors]
        assert "INVENTORY_MOVEMENT_QUANTITY_INVALID" in codes

    def test_rejects_float_quantity(self):
        from app.modules.logistics.inventory.ledger.application.services.validation_service import (
            InventoryMovementValidationService,
        )
        from app.modules.logistics.inventory.ledger.domain.services.availability_provider import (
            SourceBackedAvailabilityProvider,
        )

        svc = InventoryMovementValidationService(
            availability_provider=SourceBackedAvailabilityProvider(None)  # type: ignore[arg-type]
        )
        payload = self._payload(
            lines=[
                {
                    "product_id": str(uuid4()),
                    "unit_id": str(uuid4()),
                    "base_unit_id": str(uuid4()),
                    "quantity": 1.5,  # not a string
                    "base_quantity": "1.5",
                    "destination_position_id": str(uuid4()),
                    "quantity_direction": "TRANSFER",
                }
            ]
        )
        result = svc.validate(
            organization_id=uuid4(),
            source_adapter_name="PUTAWAY_COMPLETED",
            movement_type="PUTAWAY_COMPLETED",
            payload=payload,
        )
        codes = [e.code for e in result.blocking_errors]
        assert "INVENTORY_MOVEMENT_QUANTITY_INVALID" in codes

    def test_rejects_disabled_adapter(self):
        from app.modules.logistics.inventory.ledger.application.services.validation_service import (
            InventoryMovementValidationService,
        )
        from app.modules.logistics.inventory.ledger.domain.services.availability_provider import (
            SourceBackedAvailabilityProvider,
        )

        svc = InventoryMovementValidationService(
            availability_provider=SourceBackedAvailabilityProvider(None)  # type: ignore[arg-type]
        )
        result = svc.validate(
            organization_id=uuid4(),
            source_adapter_name="ADJUSTMENT_APPROVED",
            movement_type="PUTAWAY_COMPLETED",
            payload=self._payload(),
        )
        codes = [e.code for e in result.blocking_errors]
        assert "INVENTORY_MOVEMENT_SOURCE_NOT_AUTHORIZED" in codes

    def test_rejects_same_source_and_destination(self):
        from app.modules.logistics.inventory.ledger.application.services.validation_service import (
            InventoryMovementValidationService,
        )
        from app.modules.logistics.inventory.ledger.domain.services.availability_provider import (
            SourceBackedAvailabilityProvider,
        )

        svc = InventoryMovementValidationService(
            availability_provider=SourceBackedAvailabilityProvider(None)  # type: ignore[arg-type]
        )
        pos = str(uuid4())
        payload = self._payload(
            lines=[
                {
                    "product_id": str(uuid4()),
                    "unit_id": str(uuid4()),
                    "base_unit_id": str(uuid4()),
                    "quantity": "10",
                    "base_quantity": "10",
                    "source_position_id": pos,
                    "destination_position_id": pos,
                    "quantity_direction": "TRANSFER",
                }
            ]
        )
        result = svc.validate(
            organization_id=uuid4(),
            source_adapter_name="PUTAWAY_COMPLETED",
            movement_type="PUTAWAY_COMPLETED",
            payload=payload,
        )
        codes = [e.code for e in result.blocking_errors]
        assert "INVENTORY_MOVEMENT_POSITION_INVALID" in codes


class TestPhase044SecurityAndDerivedFields:
    def test_public_payload_rejects_nested_base_quantity(self):
        from app.modules.logistics.inventory.ledger.application.services.posting_service import (
            assert_no_server_derived_fields,
        )
        from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
            InventoryMovementLineInvalid,
        )

        with pytest.raises(InventoryMovementLineInvalid):
            assert_no_server_derived_fields({"lines": [{"quantity": "1", "base_quantity": "999"}]})

    def test_line_service_derives_same_unit_with_decimal(self):
        from app.modules.logistics.inventory.ledger.domain.services.line_service import (
            InventoryMovementLineService,
        )

        unit_id = uuid4()
        result = InventoryMovementLineService(None).derive_base_quantity(  # type: ignore[arg-type]
            organization_id=uuid4(),
            product_id=uuid4(),
            quantity=Decimal("12.345678901234567890"),
            unit_id=unit_id,
            base_unit_id=unit_id,
            conversion_rule_id=None,
        )
        assert result.base_quantity == Decimal("12.345678901234567890")
        assert result.conversion_snapshot is None

    def test_registry_rejects_future_adapter(self):
        from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
            InventoryMovementSourceNotAuthorized,
        )
        from app.modules.logistics.inventory.ledger.domain.services.source_registry import (
            InventoryMovementSourceRegistry,
        )
        from app.modules.logistics.inventory.ledger.infrastructure.source_adapters.adapters import (
            FutureAdjustmentMovementAdapter,
        )

        registry = InventoryMovementSourceRegistry([FutureAdjustmentMovementAdapter()])
        with pytest.raises(InventoryMovementSourceNotAuthorized):
            registry.get("FUTURE_ADJUSTMENT")

    def test_permission_marker_is_actually_enforced(self):
        from types import SimpleNamespace

        from starlette.requests import Request

        from app.core.exceptions import ApplicationError
        from app.modules.logistics.inventory.ledger.presentation.dependencies import (
            enforce_inventory_route_security,
            require_capability,
        )

        @require_capability("logistics.inventory_ledger.read")
        def endpoint():
            return None

        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/inventory/movements",
                "headers": [],
                "query_string": b"",
                "path_params": {},
                "endpoint": endpoint,
            }
        )
        principal = SimpleNamespace(
            is_platform_admin=False,
            has_permission=lambda _permission: False,
        )
        with pytest.raises(ApplicationError):
            enforce_inventory_route_security(
                request=request,
                principal=principal,  # type: ignore[arg-type]
                db=None,  # type: ignore[arg-type]
                x_step_up_proof_id=None,
                x_csrf_token=None,
            )


class TestSourceRegistry:
    def test_enabled_adapters(self):
        from app.modules.logistics.inventory.ledger.domain.services.source_registry import (
            ENABLED_ADAPTERS,
            is_adapter_enabled,
        )
        from app.modules.logistics.inventory.ledger.infrastructure.source_adapters.adapters import (
            build_default_registry,
        )

        registry = build_default_registry()
        for name in ENABLED_ADAPTERS:
            assert name.value in registry
            assert is_adapter_enabled(name.value)

    def test_disabled_movement_types(self):
        from app.modules.logistics.inventory.ledger.domain.services.source_registry import (
            is_movement_type_disabled,
        )
        from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
            DISABLED_MOVEMENT_TYPES,
            MovementType,
        )

        assert is_movement_type_disabled(MovementType.ADJUSTMENT_INCREASE_FUTURE)
        assert is_movement_type_disabled(MovementType.TRANSFER_RECEIPT_FUTURE)
        assert not is_movement_type_disabled(MovementType.PUTAWAY_COMPLETED)
        assert MovementType.QUARANTINE_APPLIED not in DISABLED_MOVEMENT_TYPES


class TestPositionService:
    def test_dimension_key_is_deterministic(self):
        from app.modules.logistics.inventory.ledger.domain.services.position_service import (
            PositionDimension,
            compute_dimension_key,
        )
        from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
            AvailabilityState,
            BoundaryType,
            DamageState,
            ExpirationState,
            QualityState,
            TransitState,
        )

        dim = PositionDimension(
            organization_id=uuid4(),
            branch_id=uuid4(),
            warehouse_id=uuid4(),
            warehouse_location_id=uuid4(),
            boundary_type=BoundaryType.INTERNAL_LOCATION,
            product_id=uuid4(),
            product_version_id=None,
            ownership_type="OWNED",
            owner_business_partner_id=None,
            availability_state=AvailabilityState.AVAILABLE,
            quality_state=QualityState.APPROVED,
            transit_state=TransitState.NOT_IN_TRANSIT,
            damage_state=DamageState.NORMAL,
            expiration_state=ExpirationState.VALID,
        )
        key1 = compute_dimension_key(dim)
        key2 = compute_dimension_key(dim)
        assert key1 == key2
        assert len(key1) == 64  # SHA-256 hex

    def test_different_states_yield_different_keys(self):
        from app.modules.logistics.inventory.ledger.domain.services.position_service import (
            PositionDimension,
            compute_dimension_key,
        )
        from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
            AvailabilityState,
            BoundaryType,
            DamageState,
            ExpirationState,
            QualityState,
            TransitState,
        )

        dim_a = PositionDimension(
            organization_id=uuid4(),
            branch_id=uuid4(),
            warehouse_id=uuid4(),
            warehouse_location_id=uuid4(),
            boundary_type=BoundaryType.INTERNAL_LOCATION,
            product_id=uuid4(),
            product_version_id=None,
            ownership_type="OWNED",
            owner_business_partner_id=None,
            availability_state=AvailabilityState.AVAILABLE,
            quality_state=QualityState.APPROVED,
            transit_state=TransitState.NOT_IN_TRANSIT,
            damage_state=DamageState.NORMAL,
            expiration_state=ExpirationState.VALID,
        )
        dim_b = PositionDimension(
            organization_id=dim_a.organization_id,
            branch_id=dim_a.branch_id,
            warehouse_id=dim_a.warehouse_id,
            warehouse_location_id=dim_a.warehouse_location_id,
            boundary_type=BoundaryType.INTERNAL_LOCATION,
            product_id=dim_a.product_id,
            product_version_id=dim_a.product_version_id,
            ownership_type=dim_a.ownership_type,
            owner_business_partner_id=dim_a.owner_business_partner_id,
            availability_state=AvailabilityState.RESERVED,
            quality_state=QualityState.APPROVED,
            transit_state=TransitState.NOT_IN_TRANSIT,
            damage_state=DamageState.NORMAL,
            expiration_state=ExpirationState.VALID,
        )
        assert compute_dimension_key(dim_a) != compute_dimension_key(dim_b)


class TestAvailabilityProvider:
    def test_invalid_source_type_rejected(self):
        from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
            InventoryAvailabilityProviderUnavailable,
        )
        from app.modules.logistics.inventory.ledger.domain.services.availability_provider import (
            SourceBackedAvailabilityProvider,
        )

        provider = SourceBackedAvailabilityProvider(db=None)  # type: ignore[arg-type]
        with pytest.raises(InventoryAvailabilityProviderUnavailable):
            provider.get_available_quantity(
                organization_id=uuid4(),
                source_entity_type="UNKNOWN",
                source_entity_id=uuid4(),
                product_id=uuid4(),
            )


class TestIdempotencyService:
    def test_hash_payload_is_deterministic(self):
        from app.modules.logistics.inventory.ledger.domain.services.idempotency_service import (
            hash_payload,
        )

        p = {"a": 1, "b": "x"}
        assert hash_payload(p) == hash_payload(p)
        assert hash_payload(p) != hash_payload({"a": 1, "b": "y"})


class TestSourceAdapters:
    def test_quality_adapters_produce_valid_prepared_movements(self):
        from app.modules.logistics.inventory.ledger.infrastructure.source_adapters.adapters import (
            PutawayCompletedAdapter,
            QualityApprovedAdapter,
            QualityQuarantineAppliedAdapter,
            QualityRejectedAdapter,
            QuarantineReleasedAdapter,
        )

        org_id = uuid4()
        base = {
            "product_id": str(uuid4()),
            "unit_id": str(uuid4()),
            "base_unit_id": str(uuid4()),
            "quantity": "5",
            "base_quantity": "5",
            "source_event_id": "evt-1",
            "source_hash": "a" * 64,
            "occurred_at": datetime(2026, 1, 1, tzinfo=UTC),
        }

        adapter = QualityQuarantineAppliedAdapter()
        prepared = adapter.build(organization_id=org_id, payload=base)
        assert prepared.movement_type == "QUARANTINE_APPLIED"
        assert prepared.lines[0]["quantity_direction"] == "STATE_CHANGE"

        adapter = QualityApprovedAdapter()
        prepared = adapter.build(organization_id=org_id, payload=base)
        assert prepared.movement_type == "QUALITY_RELEASE_TO_STAGING"

        adapter = QuarantineReleasedAdapter()
        prepared = adapter.build(organization_id=org_id, payload=base)
        assert prepared.movement_type == "QUARANTINE_RELEASED"

        adapter = QualityRejectedAdapter()
        prepared = adapter.build(organization_id=org_id, payload=base)
        assert prepared.movement_type == "QUALITY_BLOCKED"

        base_putaway = {
            "source_event_id": "evt-2",
            "source_hash": "b" * 64,
            "destinations": [
                {
                    "product_id": str(uuid4()),
                    "unit_id": str(uuid4()),
                    "quantity": "1",
                    "base_quantity": "1",
                    "destination_position_id": str(uuid4()),
                }
            ],
        }
        adapter = PutawayCompletedAdapter()
        prepared = adapter.build(organization_id=org_id, payload=base_putaway)
        assert prepared.movement_type == "PUTAWAY_COMPLETED"
        assert prepared.lines[0]["quantity_direction"] == "TRANSFER"
