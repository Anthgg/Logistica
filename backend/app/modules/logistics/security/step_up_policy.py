"""Step-up policy catalog — versioned, centralized policy for sensitive permissions."""

from enum import StrEnum
from dataclasses import dataclass

POLICY_VERSION = "1.1.0"
CHALLENGE_TTL_SECONDS = 120
PROOF_TTL_SECONDS = 60
MAX_ATTEMPTS = 3


class StepUpFactor(StrEnum):
    FACE = "face"
    PAD = "pad"
    BEHAVIOR = "behavior"
    SESSION_REAUTH = "session_reauth"
    COMBINED_FACE_PAD = "combined_face_pad"
    COMBINED_MULTIMODAL = "combined_multimodal"


class ChallengeStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PASSED = "passed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    LOCKED = "locked"
    CONSUMED = "consumed"


class ProofStatus(StrEnum):
    ACTIVE = "active"
    CONSUMED = "consumed"
    EXPIRED = "expired"
    REVOKED = "revoked"


class RiskDecision(StrEnum):
    ALLOW = "allow"
    STEP_UP_REQUIRED = "step_up_required"
    DENY = "deny"
    REVIEW = "review"
    SESSION_TERMINATION_REQUIRED = "session_termination_required"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class StepUpPolicyEntry:
    """Policy entry mapping a permission to its step-up requirements."""
    permission_code: str
    base_risk_level: RiskLevel
    required_factors: list[StepUpFactor]
    one_time_proof: bool = True
    requires_reason: bool = True
    fail_closed: bool = True


# ---------------------------------------------------------------------------
# Policy catalog — maps sensitive permissions to step-up requirements
# ---------------------------------------------------------------------------

POLICY_CATALOG: dict[str, StepUpPolicyEntry] = {
    # Organization and purchasing
    "logistics.organizations.change_status": StepUpPolicyEntry(
        permission_code="logistics.organizations.change_status",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    "logistics.purchase_orders.approve": StepUpPolicyEntry(
        permission_code="logistics.purchase_orders.approve",
        base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=False, fail_closed=True,
    ),
    # RBAC — critical
    "logistics.role_assignments.create": StepUpPolicyEntry(
        permission_code="logistics.role_assignments.create",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD, StepUpFactor.BEHAVIOR],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    "logistics.role_assignments.revoke": StepUpPolicyEntry(
        permission_code="logistics.role_assignments.revoke",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD, StepUpFactor.BEHAVIOR],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    "logistics.role_permissions.update": StepUpPolicyEntry(
        permission_code="logistics.role_permissions.update",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD, StepUpFactor.BEHAVIOR],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    # Inventory — critical
    "logistics.inventory.adjustments.create": StepUpPolicyEntry(
        permission_code="logistics.inventory.adjustments.create",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    "logistics.inventory.adjustments.approve": StepUpPolicyEntry(
        permission_code="logistics.inventory.adjustments.approve",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD, StepUpFactor.BEHAVIOR],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    "logistics.quarantine.release": StepUpPolicyEntry(
        permission_code="logistics.quarantine.release",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    # Dispatch — high
    "logistics.dispatches.release": StepUpPolicyEntry(
        permission_code="logistics.dispatches.release",
        base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=False, fail_closed=True,
    ),
    # Documents — critical/high
    "logistics.documents.reprint": StepUpPolicyEntry(
        permission_code="logistics.documents.reprint",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    "logistics.documents.cancel": StepUpPolicyEntry(
        permission_code="logistics.documents.cancel",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD, StepUpFactor.BEHAVIOR],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    "logistics.documents.download_bulk": StepUpPolicyEntry(
        permission_code="logistics.documents.download_bulk",
        base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=False, fail_closed=True,
    ),
    "logistics.documents.export": StepUpPolicyEntry(
        permission_code="logistics.documents.export",
        base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=False, fail_closed=True,
    ),
    "logistics.documents.issue": StepUpPolicyEntry(
        permission_code="logistics.documents.issue",
        base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=False, fail_closed=True,
    ),
    # Transport — critical

    "logistics.routes.override": StepUpPolicyEntry(
        permission_code="logistics.routes.override",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    "logistics.trips.close": StepUpPolicyEntry(
        permission_code="logistics.trips.close",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    # Delivery — critical
    "logistics.deliveries.manual_close": StepUpPolicyEntry(
        permission_code="logistics.deliveries.manual_close",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    "logistics.proof_of_delivery.invalidate": StepUpPolicyEntry(
        permission_code="logistics.proof_of_delivery.invalidate",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD, StepUpFactor.BEHAVIOR],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    # Audit — high
    "logistics.audit.read_sensitive": StepUpPolicyEntry(
        permission_code="logistics.audit.read_sensitive",
        base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=False, requires_reason=False, fail_closed=True,
    ),
    "logistics.audit.export": StepUpPolicyEntry(
        permission_code="logistics.audit.export",
        base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=False, fail_closed=True,
    ),
    "logistics.reports.export_sensitive": StepUpPolicyEntry(
        permission_code="logistics.reports.export_sensitive",
        base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=False, fail_closed=True,
    ),
    # Integration config
    "logistics.integrations.configure": StepUpPolicyEntry(
        permission_code="logistics.integrations.configure",
        base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=False, fail_closed=True,
    ),
    # Master-data phases 021–027
    "logistics.company_profile.activate": StepUpPolicyEntry(
        permission_code="logistics.company_profile.activate",
        base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=False, fail_closed=True,
    ),
    "logistics.authorized_signers.activate": StepUpPolicyEntry(
        permission_code="logistics.authorized_signers.activate",
        base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=False, fail_closed=True,
    ),
    "logistics.authorized_signers.revoke": StepUpPolicyEntry(
        permission_code="logistics.authorized_signers.revoke",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    "logistics.business_partners.ruc_apply": StepUpPolicyEntry(
        permission_code="logistics.business_partners.ruc_apply",
        base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=False, fail_closed=True,
    ),
    "logistics.ruc_datasets.activate": StepUpPolicyEntry(
        permission_code="logistics.ruc_datasets.activate",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=False, fail_closed=True,
    ),
    "logistics.ruc_datasets.rollback": StepUpPolicyEntry(
        permission_code="logistics.ruc_datasets.rollback",
        base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=True, fail_closed=True,
    ),
    "logistics.ruc_verifications.approve": StepUpPolicyEntry(
        permission_code="logistics.ruc_verifications.approve",
        base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD],
        one_time_proof=True, requires_reason=False, fail_closed=True,
    ),
    # Phase 038 — sensitive dock/unloading commands.
    "logistics.warehouse_docks.activate": StepUpPolicyEntry(
        permission_code="logistics.warehouse_docks.activate", base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=True,
        requires_reason=False, fail_closed=True,
    ),
    "logistics.warehouse_docks.block": StepUpPolicyEntry(
        permission_code="logistics.warehouse_docks.block", base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=True,
        requires_reason=True, fail_closed=True,
    ),
    "logistics.warehouse_docks.manage_blackouts": StepUpPolicyEntry(
        permission_code="logistics.warehouse_docks.manage_blackouts", base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=True,
        requires_reason=True, fail_closed=True,
    ),
    "logistics.inbound_dock_queue.override_priority": StepUpPolicyEntry(
        permission_code="logistics.inbound_dock_queue.override_priority", base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=True,
        requires_reason=True, fail_closed=True,
    ),
    "logistics.inbound_dock_assignments.assign": StepUpPolicyEntry(
        permission_code="logistics.inbound_dock_assignments.assign", base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=True,
        requires_reason=False, fail_closed=True,
    ),
    "logistics.inbound_dock_assignments.reassign": StepUpPolicyEntry(
        permission_code="logistics.inbound_dock_assignments.reassign", base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=True,
        requires_reason=True, fail_closed=True,
    ),
    "logistics.inbound_dock_assignments.cancel": StepUpPolicyEntry(
        permission_code="logistics.inbound_dock_assignments.cancel", base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=True,
        requires_reason=True, fail_closed=True,
    ),
    "logistics.unloading_operations.start": StepUpPolicyEntry(
        permission_code="logistics.unloading_operations.start", base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=True,
        requires_reason=False, fail_closed=True,
    ),
    "logistics.unloading_operations.cancel": StepUpPolicyEntry(
        permission_code="logistics.unloading_operations.cancel", base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=True,
        requires_reason=True, fail_closed=True,
    ),
    "logistics.unloading_operations.abort": StepUpPolicyEntry(
        permission_code="logistics.unloading_operations.abort", base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=True,
        requires_reason=True, fail_closed=True,
    ),
    "logistics.unloading_operations.complete": StepUpPolicyEntry(
        permission_code="logistics.unloading_operations.complete", base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=True,
        requires_reason=False, fail_closed=True,
    ),
    "logistics.unloading_operations.record_seal_opening": StepUpPolicyEntry(
        permission_code="logistics.unloading_operations.record_seal_opening", base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=True,
        requires_reason=False, fail_closed=True,
    ),
    "logistics.unloading_operations.request_override": StepUpPolicyEntry(
        permission_code="logistics.unloading_operations.request_override", base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=True,
        requires_reason=True, fail_closed=True,
    ),
    "logistics.unloading_operations.approve_override": StepUpPolicyEntry(
        permission_code="logistics.unloading_operations.approve_override", base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD, StepUpFactor.BEHAVIOR], one_time_proof=True,
        requires_reason=True, fail_closed=True,
    ),
    "logistics.unloading_operations.correct_times": StepUpPolicyEntry(
        permission_code="logistics.unloading_operations.correct_times", base_risk_level=RiskLevel.CRITICAL,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD, StepUpFactor.BEHAVIOR], one_time_proof=True,
        requires_reason=True, fail_closed=True,
    ),
    "logistics.dock_operational_metrics.export": StepUpPolicyEntry(
        permission_code="logistics.dock_operational_metrics.export", base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=True,
        requires_reason=False, fail_closed=True,
    ),
    "logistics.dock_operational_integrity.read": StepUpPolicyEntry(
        permission_code="logistics.dock_operational_integrity.read", base_risk_level=RiskLevel.HIGH,
        required_factors=[StepUpFactor.COMBINED_FACE_PAD], one_time_proof=False,
        requires_reason=False, fail_closed=True,
    ),
    # Phase 039 — the backend selects these risk levels; clients cannot downgrade them.
    **{
        code: StepUpPolicyEntry(
            permission_code=code,
            base_risk_level=RiskLevel.CRITICAL if code in {"logistics.inbound_receipt_scans.compensate", "logistics.reception_difference_candidates.dismiss"} else RiskLevel.HIGH,
            required_factors=[StepUpFactor.COMBINED_FACE_PAD],
            one_time_proof=code not in {"logistics.inbound_receipts.read_integrity", "logistics.inbound_receipt_identifiers.read_sensitive"},
            requires_reason=code in {"logistics.inbound_receipts.cancel", "logistics.inbound_receipt_scans.compensate", "logistics.inbound_receipt_scans.resolve_unknown", "logistics.reception_difference_candidates.dismiss"},
            fail_closed=True,
        )
        for code in {
            "logistics.inbound_receipts.start", "logistics.inbound_receipts.complete", "logistics.inbound_receipts.cancel",
            "logistics.inbound_receipts.read_integrity", "logistics.inbound_receipt_scans.compensate",
            "logistics.inbound_receipt_scans.resolve_unknown", "logistics.inbound_receipt_scans.manual_entry",
            "logistics.inbound_receipt_identifiers.read_sensitive", "logistics.reception_difference_candidates.dismiss",
            "logistics.reception_difference_candidates.prepare", "logistics.inbound_receipts.export",
        }
    },
    # Phase 042 — Quality Quarantine
    **{
        permission_code: StepUpPolicyEntry(
            permission_code=permission_code,
            base_risk_level=RiskLevel.MEDIUM,
            required_factors=[StepUpFactor.COMBINED_FACE_PAD],
            one_time_proof=True,
            requires_reason=False,
            fail_closed=True,
        )
        for permission_code in {
            "logistics.quality_quarantine.create",
            "logistics.quality_quarantine.activate",
            "logistics.quality_quarantine.confirm_placement",
            "logistics.quality_inspections.create",
            "logistics.quality_inspections.start",
            "logistics.quality_inspections.validate",
            "logistics.quality_disposition.propose",
            "logistics.quality_disposition.review",
        }
    },
    **{
        permission_code: StepUpPolicyEntry(
            permission_code=permission_code,
            base_risk_level=RiskLevel.HIGH,
            required_factors=[StepUpFactor.COMBINED_FACE_PAD],
            one_time_proof=True,
            requires_reason=False,
            fail_closed=True,
        )
        for permission_code in {
            "logistics.inbound_inventory_disposition.materialize",
            "logistics.quality_inspections.complete",
            "logistics.quality_inspections.request_reinspection",
            "logistics.quality_disposition.approve",
            "logistics.quality_disposition.reject_proposal",
            "logistics.quality_quarantine.request_release",
            "logistics.quality_quarantine.approve_release",
            "logistics.quality_quarantine.execute_release",
            "logistics.quality_quarantine.request_rejection",
            "logistics.quality_quarantine.execute_rejection",
            "logistics.quality_nonconformities.issue",
            "logistics.quality_nonconformities.reprint",
            "logistics.quality_quarantine.cancel",
            "logistics.quality_quarantine.close",
            "logistics.quality_quarantine.read_integrity",
        }
    },
    **{
        permission_code: StepUpPolicyEntry(
            permission_code=permission_code,
            base_risk_level=RiskLevel.CRITICAL,
            required_factors=[StepUpFactor.COMBINED_FACE_PAD],
            one_time_proof=True,
            requires_reason=False,
            fail_closed=True,
        )
        for permission_code in {
            "logistics.quality_quarantine.direct_release",
            "logistics.quality_quarantine.approve_rejection",
            "logistics.quality_nonconformities.cancel",
        }
    },
    **{
        permission_code: StepUpPolicyEntry(
            permission_code=permission_code,
            base_risk_level=RiskLevel.HIGH,
            required_factors=[StepUpFactor.COMBINED_FACE_PAD],
            one_time_proof=True,
            requires_reason=True,
            fail_closed=True,
        )
        for permission_code in {
            "logistics.inbound_inventory_disposition.split",
            "logistics.inbound_inventory_disposition.cancel",
            "logistics.quality_nonconformities.cancel",
        }
    },
    # Phase 043: Putaway
    **{
        permission_code: StepUpPolicyEntry(
            permission_code=permission_code,
            base_risk_level=RiskLevel.CRITICAL,
            required_factors=[StepUpFactor.COMBINED_FACE_PAD],
            one_time_proof=True,
            requires_reason=True,
            fail_closed=True,
        )
        for permission_code in {
            "logistics.putaway.override.approve",
        }
    },
    **{
        permission_code: StepUpPolicyEntry(
            permission_code=permission_code,
            base_risk_level=RiskLevel.HIGH,
            required_factors=[StepUpFactor.COMBINED_FACE_PAD],
            one_time_proof=True,
            requires_reason=True,
            fail_closed=True,
        )
        for permission_code in {
            "logistics.putaway.override",
        }
    },
}


def get_policy(permission_code: str) -> StepUpPolicyEntry | None:
    """Get the step-up policy for a permission, or None if not sensitive."""
    return POLICY_CATALOG.get(permission_code)


def is_sensitive_permission(permission_code: str) -> bool:
    """Check if a permission requires step-up authentication."""
    return permission_code in POLICY_CATALOG


def requires_step_up(permission_code: str) -> bool:
    """Alias for is_sensitive_permission."""
    return permission_code in POLICY_CATALOG
