"""Phase 042 — Inspection result calculation service."""

from __future__ import annotations

from typing import Any

from app.modules.logistics.inbound.quality_quarantine.domain.enums import (
    ControlResultStatus,
    InspectionOverallResult,
)


def calculate_overall_result(
    controls: list[dict[str, Any]],
    evidence_links: list[dict[str, Any]],
    sample_sets: list[dict[str, Any]],
    certificate_reviews: list[dict[str, Any]],
) -> str:
    """Calculate inspection overall result from controls, evidence, samples, certificates.

    Rules:
    - A FAIL on a blocking control produces FAIL.
    - A mandatory control pending produces INCONCLUSIVE.
    - Required evidence missing produces INCONCLUSIVE or FAIL.
    - All mandatory controls PASS produces PASS.
    - PASS with warnings produces PASS_WITH_OBSERVATIONS.
    """
    has_blocking_fail = False
    has_warning = False
    mandatory_pending = 0
    required_evidence_missing = False

    for ctrl in controls:
        if ctrl.get("required") and ctrl.get("status") == "NOT_STARTED":
            mandatory_pending += 1
            continue
        if ctrl.get("status") != "COMPLETED":
            if ctrl.get("required"):
                mandatory_pending += 1
            continue

        result_status = ctrl.get("result_status")
        if result_status == ControlResultStatus.FAIL:
            if ctrl.get("blocking_on_fail"):
                has_blocking_fail = True
            else:
                has_warning = True
        elif result_status == ControlResultStatus.PASS_WITH_OBSERVATION:
            has_warning = True
        elif result_status == ControlResultStatus.CONDITIONAL:
            has_warning = True

    for ev in evidence_links:
        if ev.get("required") and not ev.get("evidence_complete"):
            required_evidence_missing = True

    if has_blocking_fail:
        return InspectionOverallResult.FAIL

    if mandatory_pending > 0:
        return InspectionOverallResult.INCONCLUSIVE

    if required_evidence_missing:
        return InspectionOverallResult.INCONCLUSIVE

    if has_warning:
        return InspectionOverallResult.PASS_WITH_OBSERVATIONS

    return InspectionOverallResult.PASS
