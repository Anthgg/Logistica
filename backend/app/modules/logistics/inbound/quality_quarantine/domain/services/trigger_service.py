"""Phase 042 — Quarantine trigger service (domain policy engine)."""

from __future__ import annotations

from typing import Any

from app.modules.logistics.inbound.quality_quarantine.domain.enums import (
    TriggerEvaluationResult,
)


class QuarantineTriggerService:
    """Evaluates whether a received line requires quarantine based on configurable rules."""

    @staticmethod
    def evaluate_triggers(
        *,
        product_requires_inspection: bool = False,
        quality_plan_applicable: bool = False,
        difference_severity: str | None = None,
        has_damage: bool = False,
        wrong_product: bool = False,
        product_expired: bool = False,
        insufficient_shelf_life: bool = False,
        temperature_observed: bool = False,
        certificate_missing: bool = False,
        document_mismatch: bool = False,
        seal_broken: bool = False,
        serial_duplicate: bool = False,
        lot_missing: bool = False,
        serial_missing: bool = False,
        manual_sensitive_entry: bool = False,
        supervisor_order: bool = False,
        mandatory_sampling: bool = False,
    ) -> dict[str, Any]:
        """Evaluate all quarantine triggers and return evaluation result."""
        reasons: list[str] = []
        result = TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE

        # Always quarantine if damage, wrong product, expired
        if has_damage:
            reasons.append("DAMAGE_DETECTED")
            result = TriggerEvaluationResult.QUARANTINE_REQUIRED
        if wrong_product:
            reasons.append("WRONG_PRODUCT")
            result = TriggerEvaluationResult.QUARANTINE_REQUIRED
        if product_expired:
            reasons.append("PRODUCT_EXPIRED")
            result = TriggerEvaluationResult.QUARANTINE_REQUIRED
        if insufficient_shelf_life:
            reasons.append("INSUFFICIENT_SHELF_LIFE")
            result = TriggerEvaluationResult.QUARANTINE_REQUIRED
        if seal_broken:
            reasons.append("SEAL_BROKEN")
            result = TriggerEvaluationResult.QUARANTINE_REQUIRED

        # Inspection required triggers
        if product_requires_inspection:
            reasons.append("PRODUCT_REQUIRES_INSPECTION")
            if result == TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE:
                result = TriggerEvaluationResult.INSPECTION_REQUIRED
        if quality_plan_applicable:
            reasons.append("QUALITY_PLAN_APPLICABLE")
            if result == TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE:
                result = TriggerEvaluationResult.INSPECTION_REQUIRED
        if mandatory_sampling:
            reasons.append("MANDATORY_SAMPLING")
            if result == TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE:
                result = TriggerEvaluationResult.INSPECTION_REQUIRED

        # High/Critical differences require quarantine
        if difference_severity in ("HIGH", "CRITICAL"):
            reasons.append(f"DIFFERENCE_SEVERITY_{difference_severity}")
            result = TriggerEvaluationResult.QUARANTINE_REQUIRED

        # Manual review triggers
        if temperature_observed:
            reasons.append("TEMPERATURE_CONCERN")
            if result == TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE:
                result = TriggerEvaluationResult.MANUAL_REVIEW_REQUIRED
        if certificate_missing:
            reasons.append("CERTIFICATE_MISSING")
            if result == TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE:
                result = TriggerEvaluationResult.MANUAL_REVIEW_REQUIRED
        if document_mismatch:
            reasons.append("DOCUMENT_MISMATCH")
            if result == TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE:
                result = TriggerEvaluationResult.MANUAL_REVIEW_REQUIRED
        if serial_duplicate:
            reasons.append("SERIAL_DUPLICATE")
            if result == TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE:
                result = TriggerEvaluationResult.MANUAL_REVIEW_REQUIRED
        if lot_missing:
            reasons.append("LOT_MISSING")
            if result == TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE:
                result = TriggerEvaluationResult.MANUAL_REVIEW_REQUIRED
        if serial_missing:
            reasons.append("SERIAL_MISSING")
            if result == TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE:
                result = TriggerEvaluationResult.MANUAL_REVIEW_REQUIRED
        if manual_sensitive_entry:
            reasons.append("MANUAL_SENSITIVE_ENTRY")
            if result == TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE:
                result = TriggerEvaluationResult.MANUAL_REVIEW_REQUIRED
        if supervisor_order:
            reasons.append("SUPERVISOR_ORDER")
            if result == TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE:
                result = TriggerEvaluationResult.MANUAL_REVIEW_REQUIRED

        if not reasons:
            result = TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE

        return {
            "result": result,
            "reasons": reasons,
            "triggers_applied": len(reasons),
        }
