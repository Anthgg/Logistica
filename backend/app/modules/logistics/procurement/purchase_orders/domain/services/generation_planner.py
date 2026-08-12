"""PurchaseOrderGenerationPlanner — generates OC creation plans from evaluation decisions.

Takes a QuotationEvaluationDecisionModel (status=RECORDED) and produces
a PurchaseOrderGenerationPlan with one entry per (supplier, currency) group.

Rules:
- Only RECORDED decisions are processed.
- The plan does NOT create OCs — it describes what will be created.
- The caller (PurchaseOrderGenerationService) executes the plan.
- All monetary values in the plan are Decimal, never float.
- If the decision has split lines (different suppliers per line),
  multiple plan entries are produced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from uuid import UUID


_ZERO = Decimal("0")

DECISION_STATUS_RECORDED = "RECORDED"


@dataclass(frozen=True)
class GenerationPlanLineEntry:
    """A single line to be created in a purchase order."""
    evaluation_decision_line_id: UUID
    quotation_response_line_id: UUID | None
    requisition_line_id: UUID | None
    product_id: UUID | None
    product_name_snapshot: str
    product_description_snapshot: str | None
    specifications_snapshot: dict | None
    supplier_product_reference: str | None
    ordered_quantity: Decimal
    ordered_unit_id: UUID | None
    ordered_unit_code: str
    unit_price: Decimal
    currency_code: str
    source_line_total: Decimal


@dataclass
class GenerationPlanEntry:
    """Plan for creating ONE purchase order (one supplier, one currency)."""
    entry_index: int
    supplier_business_partner_id: UUID
    supplier_name_snapshot: str
    currency_code: str
    lines: list[GenerationPlanLineEntry] = field(default_factory=list)
    source_evaluation_id: UUID | None = None
    source_evaluation_run_id: UUID | None = None
    source_quotation_round_id: UUID | None = None
    source_purchase_requisition_id: UUID | None = None
    # Computed totals from the decision (informational only — service recalculates)
    estimated_subtotal: Decimal = _ZERO
    estimated_grand_total: Decimal = _ZERO
    warnings: list[str] = field(default_factory=list)


@dataclass
class PurchaseOrderGenerationPlan:
    """Complete plan for generating one or more purchase orders from a decision."""
    evaluation_decision_id: UUID
    evaluation_decision_status: str
    entries: list[GenerationPlanEntry] = field(default_factory=list)
    blocking_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_executable(self) -> bool:
        """True if the plan has no blocking issues and at least one entry."""
        return len(self.blocking_issues) == 0 and len(self.entries) > 0

    @property
    def total_orders_to_create(self) -> int:
        return len(self.entries)


class PurchaseOrderGenerationPlanner:
    """Generates a PurchaseOrderGenerationPlan from an evaluation decision dict.

    The planner is a pure domain service — it does NOT access the database.
    Data is provided as pre-loaded dicts (snapshots) from the application layer.
    """

    def build_plan(
        self,
        decision_data: dict[str, Any],
        decision_lines_data: list[dict[str, Any]],
        candidates_by_id: dict[UUID, dict[str, Any]],
        evaluation_data: dict[str, Any] | None = None,
    ) -> PurchaseOrderGenerationPlan:
        """Build a generation plan from raw decision and line data.

        Args:
            decision_data: Dict representation of QuotationEvaluationDecisionModel.
            decision_lines_data: List of QuotationEvaluationDecisionLineModel dicts.
            candidates_by_id: Map from candidate_id → candidate dict (includes supplier info).
            evaluation_data: Optional parent QuotationEvaluationModel dict.

        Returns:
            PurchaseOrderGenerationPlan (may have blocking_issues).
        """
        plan = PurchaseOrderGenerationPlan(
            evaluation_decision_id=UUID(str(decision_data["id"])),
            evaluation_decision_status=decision_data.get("status", ""),
        )

        # --- Pre-checks ---
        if plan.evaluation_decision_status != DECISION_STATUS_RECORDED:
            plan.blocking_issues.append(
                f"Decision status is {plan.evaluation_decision_status!r}. "
                "Only RECORDED decisions can generate purchase orders."
            )
            return plan

        if not decision_lines_data:
            plan.blocking_issues.append("Decision has no lines. Cannot generate a purchase order.")
            return plan

        if decision_data.get("procurement_approval_status", "") != "PENDING_PHASE_035":
            # This is a warning, not a blocker — we still generate the plan
            plan.warnings.append(
                "procurement_approval_status is not PENDING_PHASE_035. "
                "The decision may have already been processed."
            )

        # --- Group lines by (supplier_id, currency_code) ---
        groups: dict[tuple[UUID, str], GenerationPlanEntry] = {}

        for i, line_data in enumerate(decision_lines_data):
            try:
                entry, line_entry, issue = self._process_line(
                    line_data, candidates_by_id, evaluation_data
                )
            except Exception as exc:
                plan.blocking_issues.append(
                    f"Line {i + 1}: Failed to process decision line — {exc}"
                )
                continue

            if issue:
                plan.blocking_issues.append(f"Line {i + 1}: {issue}")
                continue

            key = (entry.supplier_business_partner_id, entry.currency_code)
            if key not in groups:
                groups[key] = entry
            else:
                # Merge line into existing entry for same supplier+currency
                groups[key].lines.append(line_entry)
                groups[key].estimated_subtotal += line_entry.source_line_total

        # --- Finalize entries ---
        for idx, po_entry in enumerate(groups.values()):
            po_entry.entry_index = idx
            po_entry.estimated_grand_total = po_entry.estimated_subtotal
            plan.entries.append(po_entry)

        if not plan.entries and not plan.blocking_issues:
            plan.blocking_issues.append("No purchase order entries could be derived from the decision lines.")

        return plan

    def _process_line(
        self,
        line_data: dict[str, Any],
        candidates_by_id: dict[UUID, dict[str, Any]],
        evaluation_data: dict[str, Any] | None,
    ) -> tuple[GenerationPlanEntry, GenerationPlanLineEntry, str | None]:
        """Process a single decision line. Returns (entry, line_entry, issue_or_None)."""
        candidate_id = UUID(str(line_data.get("selected_candidate_id", "") or ""))
        candidate = candidates_by_id.get(candidate_id)
        if not candidate:
            return GenerationPlanEntry(0, candidate_id, "", ""), GenerationPlanLineEntry(  # type: ignore[call-arg]
                evaluation_decision_line_id=UUID(str(line_data.get("id", ""))),
                quotation_response_line_id=None,
                requisition_line_id=None,
                product_id=None,
                product_name_snapshot="UNKNOWN",
                product_description_snapshot=None,
                specifications_snapshot=None,
                supplier_product_reference=None,
                ordered_quantity=Decimal("0"),
                ordered_unit_id=None,
                ordered_unit_code="UND",
                unit_price=Decimal("0"),
                currency_code="PEN",
                source_line_total=Decimal("0"),
            ), f"Candidate {candidate_id} not found in candidates map."

        # Extract supplier info from candidate snapshot
        supplier_id = UUID(str(candidate.get("supplier_business_partner_id", "")))
        supplier_snapshot = candidate.get("supplier_snapshot") or {}
        supplier_name = supplier_snapshot.get("legal_name") or supplier_snapshot.get("name") or f"Supplier {supplier_id}"

        currency_code = str(line_data.get("selected_currency_code") or "PEN").strip().upper()

        # Quantities and pricing — always Decimal
        qty_raw = line_data.get("selected_quantity") or Decimal("0")
        price_raw = line_data.get("selected_unit_price") or Decimal("0")
        total_raw = line_data.get("selected_line_total") or Decimal("0")

        ordered_quantity = Decimal(str(qty_raw))
        unit_price = Decimal(str(price_raw))
        source_line_total = Decimal(str(total_raw))

        if ordered_quantity <= Decimal("0"):
            return GenerationPlanEntry(0, supplier_id, supplier_name, currency_code), GenerationPlanLineEntry(  # type: ignore[call-arg]
                evaluation_decision_line_id=UUID(str(line_data.get("id", ""))),
                quotation_response_line_id=None,
                requisition_line_id=None,
                product_id=None,
                product_name_snapshot="",
                product_description_snapshot=None,
                specifications_snapshot=None,
                supplier_product_reference=None,
                ordered_quantity=ordered_quantity,
                ordered_unit_id=None,
                ordered_unit_code="UND",
                unit_price=unit_price,
                currency_code=currency_code,
                source_line_total=source_line_total,
            ), "selected_quantity must be positive."

        product_snapshot = line_data.get("product_snapshot") or {}
        unit_id_raw = line_data.get("selected_unit_id")

        line_entry = GenerationPlanLineEntry(
            evaluation_decision_line_id=UUID(str(line_data.get("id", ""))),
            quotation_response_line_id=_safe_uuid(line_data.get("selected_response_line_id")),
            requisition_line_id=_safe_uuid(line_data.get("requisition_line_id")),
            product_id=_safe_uuid(product_snapshot.get("id")),
            product_name_snapshot=product_snapshot.get("name") or "PRODUCT",
            product_description_snapshot=product_snapshot.get("description"),
            specifications_snapshot=product_snapshot.get("specifications"),
            supplier_product_reference=line_data.get("supplier_product_reference"),
            ordered_quantity=ordered_quantity,
            ordered_unit_id=_safe_uuid(unit_id_raw),
            ordered_unit_code=str(line_data.get("selected_unit_code") or "UND").strip().upper(),
            unit_price=unit_price,
            currency_code=currency_code,
            source_line_total=source_line_total,
        )

        eval_id = _safe_uuid((evaluation_data or {}).get("id"))
        run_id = _safe_uuid(line_data.get("evaluation_run_id"))
        req_id = _safe_uuid(candidate.get("source_requisition_id"))

        entry = GenerationPlanEntry(
            entry_index=0,  # Set later when merging
            supplier_business_partner_id=supplier_id,
            supplier_name_snapshot=supplier_name,
            currency_code=currency_code,
            lines=[line_entry],
            source_evaluation_id=eval_id,
            source_evaluation_run_id=run_id,
            source_purchase_requisition_id=req_id,
            estimated_subtotal=source_line_total,
            estimated_grand_total=source_line_total,
        )
        return entry, line_entry, None


def _safe_uuid(value: Any) -> UUID | None:
    """Convert a value to UUID or return None if not convertible."""
    if value is None or str(value).strip() in ("", "None"):
        return None
    try:
        return UUID(str(value))
    except (ValueError, AttributeError):
        return None
