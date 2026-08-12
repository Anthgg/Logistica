"""Phase 042 — Preparation services for future phases (read-only contracts)."""

from __future__ import annotations

from typing import Any


class PutawayPreparationService:
    """Prepares data for Phase 043 putaway. Read-only, no mutations."""

    @staticmethod
    def prepare_putaway_data(allocations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return allocations eligible for putaway (RELEASED_FOR_PUTAWAY only)."""
        result = []
        for a in allocations:
            if a.get("allocation_status") != "RELEASED_FOR_PUTAWAY":
                continue
            result.append({
                "allocation_id": a["id"],
                "quarantine_case_id": a.get("quarantine_case_id"),
                "release_authorization_id": a.get("release_authorization_id"),
                "receipt_id": a.get("inbound_receipt_id"),
                "warehouse_id": a.get("warehouse_id"),
                "product_id": a.get("product_id"),
                "product_version_id": a.get("product_version_id"),
                "quantity": a.get("quantity"),
                "unit_id": a.get("unit_id"),
                "base_quantity": a.get("base_quantity"),
                "observed_lots": a.get("lot_observation_ids", []),
                "observed_serials": a.get("serial_observation_ids", []),
                "expiration_observations": a.get("expiration_observation_ids", []),
                "eligible_for_putaway": True,
                "blocking_reasons": [],
            })
        return result


class FutureInventoryMovementPreparationService:
    """Prepares data for Phase 044 inventory movement book. Read-only."""

    @staticmethod
    def prepare_movement_events(allocations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return future movement events for Phase 044 consumption."""
        events = []
        for a in allocations:
            status = a.get("allocation_status")
            if status == "RELEASED_FOR_PUTAWAY":
                event_type = "QUARANTINE_RELEASED"
            elif status == "REJECTED_PENDING_DISPOSITION":
                event_type = "QUALITY_REJECTED"
            elif status in ("QUALITY_APPROVED",):
                event_type = "QUALITY_APPROVED"
            else:
                continue

            events.append({
                "source_allocation_id": a["id"],
                "product_id": a.get("product_id"),
                "quantity": a.get("quantity"),
                "unit_id": a.get("unit_id"),
                "base_quantity": a.get("base_quantity"),
                "warehouse_id": a.get("warehouse_id"),
                "event_type": event_type,
                "quality_hash": a.get("content_hash"),
            })
        return events


class FutureInventoryBalancePreparationService:
    """Prepares data for Phase 045 balance reconciliation. Read-only."""

    @staticmethod
    def prepare_balance_projections(allocations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return balance projections grouped by product, warehouse, status."""
        projections = []
        for a in allocations:
            projections.append({
                "product_id": a.get("product_id"),
                "warehouse_id": a.get("warehouse_id"),
                "availability_class": a.get("availability_class"),
                "quality_status": a.get("quality_status"),
                "quantity": a.get("quantity"),
                "unit_id": a.get("unit_id"),
                "base_quantity": a.get("base_quantity"),
                "source_allocation_id": a["id"],
            })
        return projections


class FutureTraceabilityPreparationService:
    """Prepares data for Phase 046 lot/serial traceability. Read-only."""

    @staticmethod
    def prepare_traceability_data(allocations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return traceability data for lots, serials, expiration."""
        result = []
        for a in allocations:
            result.append({
                "allocation_id": a["id"],
                "product_id": a.get("product_id"),
                "observed_lot_references": a.get("lot_observation_ids", []),
                "observed_serial_references": a.get("serial_observation_ids", []),
                "expiration_observations": a.get("expiration_observation_ids", []),
                "quantity": a.get("quantity"),
                "unit_id": a.get("unit_id"),
                "quality_status": a.get("quality_status"),
                "release_status": a.get("allocation_status"),
                "source_hash": a.get("content_hash"),
            })
        return result
