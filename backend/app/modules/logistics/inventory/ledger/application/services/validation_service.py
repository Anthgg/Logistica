"""Inventory movement validation service.

The validation service is the single point through which all posting
requests must pass. It performs:

* organization / branch / warehouse scope validation
* idempotency check
* adapter authorization
* source allocation freshness
* product, unit, conversion, position, transition and payload checks

It never persists anything; it produces a
``PreparedInventoryEventValidationResponse`` that the posting service
consumes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Mapping
from uuid import UUID

from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
    InventoryMovementConversionMissing,
    InventoryMovementExternalBoundaryInvalid,
    InventoryMovementLineInvalid,
    InventoryMovementPositionInvalid,
    InventoryMovementQuantityInvalid,
    InventoryMovementSourceConflict,
    InventoryMovementSourceNotAuthorized,
    InventoryMovementSourceNotFound,
    InventoryMovementTypeInvalid,
    InventoryMovementUnitInvalid,
)
from app.modules.logistics.inventory.ledger.domain.policies.state_transition_policy import (
    is_legal_transition,
)
from app.modules.logistics.inventory.ledger.domain.services.availability_provider import (
    InventoryAvailabilityProvider,
)
from app.modules.logistics.inventory.ledger.domain.services.line_service import (
    InventoryMovementLineService,
)
from app.modules.logistics.inventory.ledger.domain.services.source_registry import (
    is_adapter_enabled,
)
from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
    DISABLED_MOVEMENT_TYPES,
    MOVEMENT_TYPE_FAMILY,
    MovementFamily,
    MovementType,
)


@dataclass
class ValidationFinding:
    code: str
    message: str
    severity: str  # "ERROR" | "WARNING"
    path: str | None = None


@dataclass
class ResolvedLine:
    product_id: UUID
    product_version_id: UUID | None
    product_snapshot: Mapping[str, Any]
    quantity: Decimal
    unit_id: UUID
    base_quantity: Decimal
    base_unit_id: UUID
    conversion_rule_id: UUID | None
    conversion_snapshot: Mapping[str, Any] | None
    source_position_id: UUID | None
    destination_position_id: UUID | None
    source_external_boundary_kind: str | None
    destination_external_boundary_kind: str | None
    quantity_direction: str
    line_number: int
    reason_code: str | None
    metadata: Mapping[str, Any] | None = None


@dataclass
class PreparedInventoryEventValidation:
    validation_status: str
    blocking_errors: list[ValidationFinding] = field(default_factory=list)
    warnings: list[ValidationFinding] = field(default_factory=list)
    movement_type: str | None = None
    movement_family: str | None = None
    resolved_lines: list[ResolvedLine] = field(default_factory=list)
    source_hash: str | None = None
    payload_hash: str | None = None
    server_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    validation_hash: str | None = None
    posting_options: Mapping[str, Any] = field(default_factory=dict)


class InventoryMovementValidationService:
    def __init__(
        self,
        *,
        availability_provider: InventoryAvailabilityProvider,
        line_service: InventoryMovementLineService | None = None,
    ) -> None:
        self._availability = availability_provider
        self._line_service = line_service

    # ------------------------------------------------------------------ public
    def validate(
        self,
        *,
        organization_id: UUID,
        source_adapter_name: str,
        movement_type: str,
        payload: Mapping[str, Any],
    ) -> PreparedInventoryEventValidation:
        result = PreparedInventoryEventValidation(
            validation_status="VALID",
            posting_options={"organization_id": str(organization_id)},
        )

        if not is_adapter_enabled(source_adapter_name):
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementSourceNotAuthorized.code,
                    message=(f"Source adapter {source_adapter_name!r} is not enabled."),
                    severity="ERROR",
                )
            )

        if movement_type in DISABLED_MOVEMENT_TYPES:
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementTypeInvalid.code,
                    message=(f"Movement type {movement_type!r} is not enabled in this phase."),
                    severity="ERROR",
                )
            )

        family = MOVEMENT_TYPE_FAMILY.get(movement_type)
        if family is None:
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementTypeInvalid.code,
                    message=f"Movement type {movement_type!r} is unknown.",
                    severity="ERROR",
                )
            )
        else:
            result.movement_type = movement_type
            result.movement_family = family

        try:
            MovementType(movement_type)
        except ValueError:
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementTypeInvalid.code,
                    message=f"Movement type {movement_type!r} is not in the catalog.",
                    severity="ERROR",
                )
            )

        payload_hash = payload.get("payload_hash") if isinstance(payload, Mapping) else None
        if not isinstance(payload_hash, str) or len(payload_hash) != 64:
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementLineInvalid.code,
                    message="payload_hash is required and must be a 64-character SHA-256 string.",
                    severity="ERROR",
                    path="payload.payload_hash",
                )
            )
        result.payload_hash = payload_hash if isinstance(payload_hash, str) else None

        source_hash = payload.get("source_hash") if isinstance(payload, Mapping) else None
        if not isinstance(source_hash, str) or len(source_hash) != 64:
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementSourceConflict.code,
                    message="source_hash is required and must be a 64-character SHA-256 string.",
                    severity="ERROR",
                    path="payload.source_hash",
                )
            )
        result.source_hash = source_hash if isinstance(source_hash, str) else None

        raw_lines = payload.get("lines") if isinstance(payload, Mapping) else None
        if not isinstance(raw_lines, list) or not raw_lines:
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementLineInvalid.code,
                    message="payload.lines must be a non-empty list.",
                    severity="ERROR",
                    path="payload.lines",
                )
            )
            raw_lines = []

        for idx, line in enumerate(raw_lines):
            self._validate_line(idx, line, result)

        result.resolved_lines = self._coerce_resolved_lines(raw_lines, result)

        if self._requires_availability(family):
            self._validate_availability(
                organization_id=organization_id,
                payload=payload if isinstance(payload, Mapping) else {},
                result=result,
            )

        if family in {MovementFamily.QUALITY_TRANSITION, MovementFamily.AVAILABILITY_TRANSITION}:
            self._validate_state_transition(raw_lines, result)

        if result.blocking_errors:
            result.validation_status = "INVALID"
        elif result.warnings:
            result.validation_status = "VALID_WITH_WARNINGS"
        else:
            result.validation_status = "VALID"

        result.server_time = datetime.now(timezone.utc)
        result.validation_hash = self._compute_validation_hash(result)
        return result

    # ------------------------------------------------------------------ helpers
    def _requires_availability(self, family: str | None) -> bool:
        return family in {
            MovementFamily.OUTBOUND,
            MovementFamily.INTERNAL_TRANSFER,
            MovementFamily.RESERVATION,
            MovementFamily.WAREHOUSE_TRANSFER,
            MovementFamily.ADJUSTMENT,
            MovementFamily.COUNT_VARIANCE,
        }

    def _validate_line(
        self,
        idx: int,
        line: Any,
        result: PreparedInventoryEventValidation,
    ) -> None:
        prefix = f"payload.lines[{idx}]"
        if not isinstance(line, Mapping):
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementLineInvalid.code,
                    message="Line must be a mapping.",
                    severity="ERROR",
                    path=prefix,
                )
            )
            return

        quantity = line.get("quantity")
        base_quantity = line.get("base_quantity")
        unit_id = line.get("unit_id")
        base_unit_id = line.get("base_unit_id")
        product_id = line.get("product_id")

        if not isinstance(quantity, str) or not self._is_decimal(quantity):
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementQuantityInvalid.code,
                    message="quantity must be a decimal string > 0.",
                    severity="ERROR",
                    path=f"{prefix}.quantity",
                )
            )
        elif Decimal(quantity) <= 0:
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementQuantityInvalid.code,
                    message="quantity must be > 0.",
                    severity="ERROR",
                    path=f"{prefix}.quantity",
                )
            )

        if base_quantity is not None and (
            not isinstance(base_quantity, str) or not self._is_decimal(base_quantity)
        ):
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementQuantityInvalid.code,
                    message="base_quantity must be a decimal string > 0.",
                    severity="ERROR",
                    path=f"{prefix}.base_quantity",
                )
            )
        elif base_quantity is not None and Decimal(base_quantity) <= 0:
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementQuantityInvalid.code,
                    message="base_quantity must be > 0.",
                    severity="ERROR",
                    path=f"{prefix}.base_quantity",
                )
            )

        if not isinstance(unit_id, str):
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementUnitInvalid.code,
                    message="unit_id is required.",
                    severity="ERROR",
                    path=f"{prefix}.unit_id",
                )
            )
        if not isinstance(base_unit_id, str):
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementUnitInvalid.code,
                    message="base_unit_id is required.",
                    severity="ERROR",
                    path=f"{prefix}.base_unit_id",
                )
            )
        if not isinstance(product_id, str):
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementLineInvalid.code,
                    message="product_id is required.",
                    severity="ERROR",
                    path=f"{prefix}.product_id",
                )
            )

        source_position_id = line.get("source_position_id")
        destination_position_id = line.get("destination_position_id")
        source_external_boundary_kind = line.get("source_external_boundary_kind")
        destination_external_boundary_kind = line.get("destination_external_boundary_kind")

        if source_position_id is None and not source_external_boundary_kind:
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementPositionInvalid.code,
                    message="source_position_id or source_external_boundary_kind is required.",
                    severity="ERROR",
                    path=prefix,
                )
            )
        if destination_position_id is None and not destination_external_boundary_kind:
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementPositionInvalid.code,
                    message="destination_position_id or destination_external_boundary_kind is required.",
                    severity="ERROR",
                    path=prefix,
                )
            )

        if (
            source_position_id is not None
            and destination_position_id is not None
            and str(source_position_id) == str(destination_position_id)
        ):
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementPositionInvalid.code,
                    message="source and destination positions must differ.",
                    severity="ERROR",
                    path=prefix,
                )
            )

        if source_position_id and source_external_boundary_kind:
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementExternalBoundaryInvalid.code,
                    message="line cannot define both source_position_id and source_external_boundary_kind.",
                    severity="ERROR",
                    path=prefix,
                )
            )
        if destination_position_id and destination_external_boundary_kind:
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementExternalBoundaryInvalid.code,
                    message="line cannot define both destination_position_id and destination_external_boundary_kind.",
                    severity="ERROR",
                    path=prefix,
                )
            )

        quantity_direction = line.get("quantity_direction")
        if quantity_direction not in {
            "ENTRY",
            "EXIT",
            "TRANSFER",
            "STATE_CHANGE",
            "RESERVATION_CHANGE",
            "COMPENSATION",
        }:
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementLineInvalid.code,
                    message="quantity_direction is required and must be a canonical value.",
                    severity="ERROR",
                    path=f"{prefix}.quantity_direction",
                )
            )

        if (
            self._line_service is not None
            and unit_id
            and base_unit_id
            and str(unit_id) != str(base_unit_id)
            and not line.get("conversion_rule_id")
        ):
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementConversionMissing.code,
                    message="conversion_rule_id is required when the units differ.",
                    severity="ERROR",
                    path=f"{prefix}.conversion_rule_id",
                )
            )

    def _coerce_resolved_lines(
        self,
        raw_lines: list[Any],
        result: PreparedInventoryEventValidation,
    ) -> list[ResolvedLine]:
        resolved: list[ResolvedLine] = []
        for idx, line in enumerate(raw_lines):
            if not isinstance(line, Mapping):
                continue
            try:
                quantity = Decimal(str(line.get("quantity", "0")))
                unit_id = UUID(str(line["unit_id"])) if line.get("unit_id") else UUID(int=0)
                base_unit_id = (
                    UUID(str(line["base_unit_id"])) if line.get("base_unit_id") else UUID(int=0)
                )
                product_id = (
                    UUID(str(line["product_id"])) if line.get("product_id") else UUID(int=0)
                )
                conversion_rule_id = (
                    UUID(str(line["conversion_rule_id"]))
                    if line.get("conversion_rule_id")
                    else None
                )
                if self._line_service is not None:
                    derived = self._line_service.derive_base_quantity(
                        organization_id=UUID(str(result.posting_options["organization_id"])),
                        product_id=product_id,
                        quantity=quantity,
                        unit_id=unit_id,
                        base_unit_id=base_unit_id,
                        conversion_rule_id=conversion_rule_id,
                    )
                    base_quantity = derived.base_quantity
                    conversion_snapshot = derived.conversion_snapshot
                else:
                    base_quantity = Decimal(str(line.get("base_quantity", quantity)))
                    conversion_snapshot = line.get("conversion_snapshot")
            except Exception as exc:  # validation output must stay structured
                result.blocking_errors.append(
                    ValidationFinding(
                        code=getattr(exc, "code", InventoryMovementConversionMissing.code),
                        message=str(exc),
                        severity="ERROR",
                        path=f"payload.lines[{idx}].conversion_rule_id",
                    )
                )
                continue
            resolved.append(
                ResolvedLine(
                    product_id=product_id,
                    product_version_id=(
                        UUID(str(line["product_version_id"]))
                        if line.get("product_version_id")
                        else None
                    ),
                    product_snapshot=dict(line.get("product_snapshot") or {}),
                    quantity=quantity,
                    unit_id=unit_id,
                    base_quantity=base_quantity,
                    base_unit_id=base_unit_id,
                    conversion_rule_id=conversion_rule_id,
                    conversion_snapshot=conversion_snapshot,
                    source_position_id=(
                        UUID(str(line["source_position_id"]))
                        if line.get("source_position_id")
                        else None
                    ),
                    destination_position_id=(
                        UUID(str(line["destination_position_id"]))
                        if line.get("destination_position_id")
                        else None
                    ),
                    source_external_boundary_kind=line.get("source_external_boundary_kind"),
                    destination_external_boundary_kind=line.get(
                        "destination_external_boundary_kind"
                    ),
                    quantity_direction=str(line.get("quantity_direction", "TRANSFER")),
                    line_number=idx + 1,
                    reason_code=line.get("reason_code"),
                    metadata=line.get("metadata"),
                )
            )
        return resolved

    def _validate_availability(
        self,
        *,
        organization_id: UUID,
        payload: Mapping[str, Any],
        result: PreparedInventoryEventValidation,
    ) -> None:
        sources = payload.get("source_references") if isinstance(payload, Mapping) else None
        if not isinstance(sources, list) or not sources:
            result.blocking_errors.append(
                ValidationFinding(
                    code=InventoryMovementSourceNotFound.code,
                    message="At least one source reference is required for availability-consuming movements.",
                    severity="ERROR",
                    path="payload.source_references",
                )
            )
            return
        for idx, source in enumerate(sources):
            if not isinstance(source, Mapping):
                result.blocking_errors.append(
                    ValidationFinding(
                        code=InventoryMovementSourceNotFound.code,
                        message="source_references entries must be mappings.",
                        severity="ERROR",
                        path=f"payload.source_references[{idx}]",
                    )
                )
                continue
            try:
                self._availability.validate_source_quantity(
                    organization_id=organization_id,
                    source_entity_type=str(source.get("source_entity_type", "")),
                    source_entity_id=UUID(str(source["source_entity_id"])),
                    product_id=UUID(str(source["product_id"])),
                    requested_base_quantity=Decimal(
                        str(source.get("requested_base_quantity", "0"))
                    ),
                )
            except Exception as exc:  # noqa: BLE001 - adapter errors are mapped here
                result.blocking_errors.append(
                    ValidationFinding(
                        code=getattr(exc, "code", "INVENTORY_AVAILABILITY_PROVIDER_UNAVAILABLE"),
                        message=str(exc),
                        severity="ERROR",
                        path=f"payload.source_references[{idx}]",
                    )
                )

    def _validate_state_transition(
        self,
        raw_lines: list[Any],
        result: PreparedInventoryEventValidation,
    ) -> None:
        for idx, line in enumerate(raw_lines):
            if not isinstance(line, Mapping):
                continue
            transition = line.get("state_transition")
            if not isinstance(transition, Mapping):
                result.blocking_errors.append(
                    ValidationFinding(
                        code=InventoryMovementLineInvalid.code,
                        message="state_transition mapping is required for transitions.",
                        severity="ERROR",
                        path=f"payload.lines[{idx}].state_transition",
                    )
                )
                continue
            ok = is_legal_transition(
                availability_from=str(transition.get("availability_state_from", "")),
                availability_to=str(transition.get("availability_state_to", "")),
                quality_from=str(transition.get("quality_state_from", "")),
                quality_to=str(transition.get("quality_state_to", "")),
                transit_from=str(transition.get("transit_state_from", "")),
                transit_to=str(transition.get("transit_state_to", "")),
                damage_from=str(transition.get("damage_state_from", "")),
                damage_to=str(transition.get("damage_state_to", "")),
                expiration_from=str(transition.get("expiration_state_from", "")),
                expiration_to=str(transition.get("expiration_state_to", "")),
            )
            if not ok:
                result.blocking_errors.append(
                    ValidationFinding(
                        code="INVENTORY_MOVEMENT_STATE_TRANSITION_INVALID",
                        message="The state transition is not allowed by the policy.",
                        severity="ERROR",
                        path=f"payload.lines[{idx}].state_transition",
                    )
                )

    @staticmethod
    def _is_decimal(value: str) -> bool:
        try:
            Decimal(value)
        except Exception:  # noqa: BLE001
            return False
        return True

    @staticmethod
    def _compute_validation_hash(result: PreparedInventoryEventValidation) -> str:
        import hashlib
        import json

        raw = json.dumps(
            {
                "movement_type": result.movement_type,
                "lines": [vars(line) for line in result.resolved_lines],
                "errors": [vars(e) for e in result.blocking_errors],
                "warnings": [vars(w) for w in result.warnings],
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
