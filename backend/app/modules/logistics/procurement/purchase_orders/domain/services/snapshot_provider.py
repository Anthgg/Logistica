"""PurchaseOrderSnapshotProvider — immutable point-in-time snapshots.

Captures the state of all external entities (supplier, buyer, product, etc.)
at the time the PO is created or approved. Snapshots prevent retroactive
mutation of purchase order data when the source records change later.

Design decisions:
- All snapshots are plain dicts — JSON-serializable.
- Snapshots include only what is needed for the document. Not the full model.
- The `captured_at` timestamp is always UTC.
- Snapshots are immutable once frozen (revision FROZEN/APPROVED status).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PurchaseOrderSnapshotProvider:
    """Generates immutable snapshots for PO-related entities."""

    # ------------------------------------------------------------------
    # Supplier snapshot
    # ------------------------------------------------------------------
    @staticmethod
    def build_supplier_snapshot(
        partner_data: dict[str, Any],
        role_data: dict[str, Any] | None = None,
        address_data: dict[str, Any] | None = None,
        contact_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build a supplier snapshot from business partner data."""
        snapshot: dict[str, Any] = {
            "business_partner_id": str(partner_data.get("id", "")),
            "partner_code": partner_data.get("partner_code") or partner_data.get("code"),
            "legal_name": partner_data.get("legal_name") or partner_data.get("name"),
            "trade_name": partner_data.get("trade_name"),
            "tax_id": partner_data.get("tax_id") or partner_data.get("ruc"),
            "country_code": partner_data.get("country_code", "PE"),
            "status": partner_data.get("status", "ACTIVE"),
            "captured_at": _utc_now_iso(),
        }
        if role_data:
            snapshot["role"] = {
                "role_id": str(role_data.get("id", "")),
                "role_type": role_data.get("role_type", "SUPPLIER"),
                "status": role_data.get("status", "ACTIVE"),
            }
        if address_data:
            snapshot["primary_address"] = {
                "address_id": str(address_data.get("id", "")),
                "address_line_1": address_data.get("address_line_1") or address_data.get("street"),
                "address_line_2": address_data.get("address_line_2"),
                "city": address_data.get("city"),
                "state": address_data.get("state") or address_data.get("department"),
                "postal_code": address_data.get("postal_code") or address_data.get("zip_code"),
                "country_code": address_data.get("country_code", "PE"),
            }
        if contact_data:
            snapshot["primary_contact"] = {
                "contact_id": str(contact_data.get("id", "")),
                "contact_name": contact_data.get("contact_name") or contact_data.get("name"),
                "email": contact_data.get("email"),
                "phone": contact_data.get("phone"),
            }
        return snapshot

    # ------------------------------------------------------------------
    # Buyer snapshot
    # ------------------------------------------------------------------
    @staticmethod
    def build_buyer_snapshot(
        user_data: dict[str, Any],
        branch_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build a buyer (internal user) snapshot."""
        return {
            "user_id": str(user_data.get("id", "")),
            "full_name": user_data.get("full_name") or user_data.get("name"),
            "email": user_data.get("email"),
            "branch_id": str((branch_data or {}).get("id", "")),
            "branch_name": (branch_data or {}).get("name"),
            "captured_at": _utc_now_iso(),
        }

    # ------------------------------------------------------------------
    # Cost center snapshot
    # ------------------------------------------------------------------
    @staticmethod
    def build_cost_center_snapshot(cost_center_data: dict[str, Any] | None) -> dict[str, Any] | None:
        if not cost_center_data:
            return None
        return {
            "cost_center_id": str(cost_center_data.get("id", "")),
            "cost_center_code": cost_center_data.get("code"),
            "cost_center_name": cost_center_data.get("name"),
            "captured_at": _utc_now_iso(),
        }

    # ------------------------------------------------------------------
    # Product snapshot (per line)
    # ------------------------------------------------------------------
    @staticmethod
    def build_product_snapshot(
        product_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Build an immutable product snapshot for a PO line."""
        return {
            "product_id": str(product_data.get("id", "")),
            "sku": product_data.get("sku"),
            "name": product_data.get("name"),
            "description": product_data.get("description"),
            "base_unit_code": product_data.get("base_unit_code"),
            "specifications": product_data.get("specifications"),
            "category_name": product_data.get("category_name"),
            "brand_name": product_data.get("brand_name"),
            "captured_at": _utc_now_iso(),
        }

    # ------------------------------------------------------------------
    # Destination snapshot
    # ------------------------------------------------------------------
    @staticmethod
    def build_destination_snapshot(
        warehouse_data: dict[str, Any] | None = None,
        address_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if not warehouse_data and not address_data:
            return None
        result: dict[str, Any] = {"captured_at": _utc_now_iso()}
        if warehouse_data:
            result["warehouse"] = {
                "warehouse_id": str(warehouse_data.get("id", "")),
                "warehouse_code": warehouse_data.get("code"),
                "warehouse_name": warehouse_data.get("name"),
            }
        if address_data:
            result["address"] = {
                "address_line_1": address_data.get("address_line_1") or address_data.get("street"),
                "address_line_2": address_data.get("address_line_2"),
                "city": address_data.get("city"),
                "country_code": address_data.get("country_code", "PE"),
            }
        return result

    # ------------------------------------------------------------------
    # Source snapshot (from evaluation decision)
    # ------------------------------------------------------------------
    @staticmethod
    def build_source_snapshot(
        decision_data: dict[str, Any],
        evaluation_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build an immutable snapshot of the source evaluation decision."""
        return {
            "decision_id": str(decision_data.get("id", "")),
            "decision_status": decision_data.get("status"),
            "decision_number": decision_data.get("decision_number"),
            "recorded_by": str(decision_data.get("recorded_by", "")),
            "recorded_at": str(decision_data.get("recorded_at", "")),
            "rationale": decision_data.get("rationale"),
            "decision_snapshot_hash": decision_data.get("decision_snapshot_hash"),
            "evaluation_id": str((evaluation_data or {}).get("id", "")),
            "evaluation_status": (evaluation_data or {}).get("status"),
            "captured_at": _utc_now_iso(),
        }

    # ------------------------------------------------------------------
    # Monetary summary snapshot
    # ------------------------------------------------------------------
    @staticmethod
    def build_monetary_snapshot(monetary_summary_dict: dict[str, Any]) -> dict[str, Any]:
        """Wrap a MonetarySummary dict as an immutable snapshot."""
        return {
            **monetary_summary_dict,
            "captured_at": _utc_now_iso(),
        }

    # ------------------------------------------------------------------
    # Content hash (for revision immutability verification)
    # ------------------------------------------------------------------
    @staticmethod
    def compute_revision_hash(
        supplier_snapshot: dict[str, Any],
        lines_data: list[dict[str, Any]],
        monetary_snapshot: dict[str, Any],
        currency_code: str,
    ) -> str:
        """Compute a deterministic SHA-256 hash of the revision content.

        The hash is used to detect tampering or unintended modification.
        `captured_at` timestamps are excluded from the hash computation
        because they are non-deterministic.
        """
        def _strip_timestamps(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: _strip_timestamps(v) for k, v in obj.items() if k != "captured_at"}
            if isinstance(obj, list):
                return [_strip_timestamps(i) for i in obj]
            return obj

        canonical = {
            "currency_code": currency_code,
            "supplier": _strip_timestamps(supplier_snapshot),
            "lines": [_strip_timestamps(ln) for ln in sorted(
                lines_data, key=lambda x: x.get("line_number", 0)
            )],
            "monetary": _strip_timestamps(monetary_snapshot),
        }
        payload = json.dumps(canonical, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
